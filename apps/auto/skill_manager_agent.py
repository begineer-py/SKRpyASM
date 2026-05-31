"""
Skill Manager Agent
===================

Centralized agent for managing SkillTemplate lifecycle:
- Creation (delegates to SkillCreatorAgent)
- Updates (version control, robustness check)
- Merging (executes SkillMergeEvaluation)
- Deprecation

This agent ensures that AI automation agents do not directly modify the Skill database
without proper validation and record-keeping.
"""

from __future__ import annotations
import logging
import json
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.core.models.analyze.SkillTemplate import SkillTemplate
from apps.core.models.analyze.SkillMergeEvaluation import SkillMergeEvaluation
from apps.auto.tools.skill_creator_agent import generate_script_body, create_skill_from_spec

logger = logging.getLogger(__name__)

def merge_schemas(schema_a: Optional[dict], schema_b: Optional[dict]) -> dict:
    """合併兩個 JSON Schema"""
    if not schema_a:
        return schema_b or {}
    if not schema_b:
        return schema_a or {}
    
    if schema_a.get("type") == "object" and schema_b.get("type") == "object":
        merged = {
            "type": "object",
            "properties": {},
            "required": []
        }
        merged["properties"].update(schema_a.get("properties", {}))
        merged["properties"].update(schema_b.get("properties", {}))
        req_set = set(schema_a.get("required", [])) | set(schema_b.get("required", []))
        merged["required"] = list(req_set)
        return merged
    
    return schema_a or schema_b or {}

def merge_script_bodies(skill_a: SkillTemplate, skill_b: SkillTemplate) -> str:
    """串聯兩個技能的腳本主體 (CONCAT 策略)"""
    body_a = skill_a.script_body or ""
    body_b = skill_b.script_body or ""
    
    if skill_a.language != "python":
        # 非 Python 腳本直接串接
        return f"# === Merged from {skill_a.name} ===\n{body_a}\n\n# === Merged from {skill_b.name} ===\n{body_b}"
        
    import re
    # 重新命名 main 以免衝突
    body_a_renamed = re.sub(r'def\s+main\s*\(\s*inputs\b', 'def main_a(inputs', body_a)
    body_b_renamed = re.sub(r'def\s+main\s*\(\s*inputs\b', 'def main_b(inputs', body_b)
    
    if body_a_renamed == body_a:
        body_a_renamed = f"def main_a(inputs: Any) -> None:\n    # Legacy/fallback body\n" + "\n".join("    " + line for line in body_a.splitlines())
    if body_b_renamed == body_b:
        body_b_renamed = f"def main_b(inputs: Any) -> None:\n    # Legacy/fallback body\n" + "\n".join("    " + line for line in body_b.splitlines())

    merged = (
        f"# === Merged script body ===\n"
        f"{body_a_renamed}\n\n"
        f"{body_b_renamed}\n\n"
        f"def main(inputs: SkillInput) -> None:\n"
        f"    # Sequential execution of merged logic\n"
        f"    main_a(inputs)\n"
        f"    main_b(inputs)\n"
    )
    return merged

class SkillManagerAgent:
    """
    Skill 管理 Agent
    負責 Skill 的 CRUD 與合併 (Merge) 執行。
    """
    
    def __init__(self, llm=None):
        self._llm = llm

    def create_skill(self, **kwargs) -> dict:
        """建立新技能 (封裝 SkillCreatorAgent)"""
        return create_skill_from_spec(llm=self._llm, **kwargs)

    @transaction.atomic
    def deprecate_skill(self, skill_id: int, reason: str = "") -> bool:
        """標記技能為棄用，不直接刪除"""
        try:
            skill = SkillTemplate.objects.get(id=skill_id)
            skill.is_deprecated = True
            if reason:
                skill.last_failure_reason = f"Deprecated: {reason}"
            skill.save()
            logger.info(f"[SkillManager] Deprecated skill: {skill.name} (ID: {skill_id})")
            return True
        except SkillTemplate.DoesNotExist:
            return False

    @transaction.atomic
    def execute_merge(self, evaluation_id: int) -> dict:
        """
        執行合併評估記錄中的建議策略。
        
        策略包括：
        - LATEST_ONLY: 保留較新的，棄用較舊的。
        - CONCAT: 串聯腳本與指令。
        - UNION: 合併 Schema 與內容。
        - A_MERGES_INTO_B: A 併入 B，棄用 A。
        - B_MERGES_INTO_A: B 併入 A，棄用 B。
        """
        try:
            eval_rec = SkillMergeEvaluation.objects.get(id=evaluation_id)
        except SkillMergeEvaluation.DoesNotExist:
            return {"ok": False, "error": f"Evaluation record {evaluation_id} not found."}

        if eval_rec.merged_into:
            return {"ok": False, "error": "This evaluation has already been executed."}

        skill_a = eval_rec.skill_a
        skill_b = eval_rec.skill_b
        strategy = eval_rec.merge_strategy

        logger.info(f"[SkillManager] Executing merge strategy '{strategy}' for {skill_a.name} & {skill_b.name}")

        result = {"ok": True, "strategy": strategy}

        if strategy == "NOT_RECOMMENDED":
            return {"ok": False, "error": "Merge strategy is NOT_RECOMMENDED."}

        elif strategy == "LATEST_ONLY":
            # 保留 updated_at 較晚的
            to_keep, to_deprecate = (skill_a, skill_b) if skill_a.updated_at > skill_b.updated_at else (skill_b, skill_a)
            self.deprecate_skill(to_deprecate.id, reason=f"Merged into {to_keep.name} (LATEST_ONLY strategy)")
            eval_rec.merged_into = to_keep
            result["kept_skill_id"] = to_keep.id

        elif strategy in ["A_MERGES_INTO_B", "B_MERGES_INTO_A"]:
            to_deprecate, to_keep = (skill_a, skill_b) if strategy == "A_MERGES_INTO_B" else (skill_b, skill_a)
            self.deprecate_skill(to_deprecate.id, reason=f"Merged into {to_keep.name} ({strategy} strategy)")
            eval_rec.merged_into = to_keep
            result["kept_skill_id"] = to_keep.id

        elif strategy in ["CONCAT", "UNION", "SMART_MERGE"]:
            # 建立全新的合併技能
            new_skill_data = self._prepare_merged_skill_data(skill_a, skill_b, strategy)
            create_res = self.create_skill(**new_skill_data)
            
            if create_res.get("ok"):
                new_skill_id = create_res["skill_id"]
                new_skill = SkillTemplate.objects.get(id=new_skill_id)
                new_skill.merged_from = [skill_a.id, skill_b.id]
                new_skill.save()
                
                # 棄用舊技能
                self.deprecate_skill(skill_a.id, reason=f"Merged into new skill {new_skill.name}")
                self.deprecate_skill(skill_b.id, reason=f"Merged into new skill {new_skill.name}")
                
                eval_rec.merged_into = new_skill
                result["new_skill_id"] = new_skill_id
            else:
                return create_res

        eval_rec.save()
        return result

    def _prepare_merged_skill_data(self, skill_a: SkillTemplate, skill_b: SkillTemplate, strategy: str) -> dict:
        """準備合併後的技能數據"""
        # 使用本模組內的合併工具
        
        # 決定新名稱
        new_name = f"{skill_a.name}-merged-{skill_b.name}"[:100]
        
        # 合併 tags
        tags = list(set(skill_a.tags or []) | set(skill_b.tags or []))
        
        # 合併 schemas
        input_schema = merge_schemas(skill_a.input_schema, skill_b.input_schema)
        output_schema = merge_schemas(skill_a.output_schema, skill_b.output_schema)
        
        # 組合說明
        instructions = (
            f"# Merged Skill: {new_name}\n\n"
            f"## Description\nMerged from {skill_a.name} and {skill_b.name} using {strategy} strategy.\n\n"
            f"## Original Instructions (A: {skill_a.name})\n{skill_a.instructions}\n\n"
            f"## Original Instructions (B: {skill_b.name})\n{skill_b.instructions}"
        )[:2000]

        # 任務描述 (用於重新生成腳本或組裝)
        task_description = f"Combine functionality of {skill_a.name} and {skill_b.name}. "
        if strategy == "CONCAT":
            task_description += "Concatenate their logic."
        else:
            task_description += "Unify their logic into a single streamlined process."

        return {
            "name": new_name,
            "description": f"Merged from {skill_a.name} & {skill_b.name}",
            "instructions": instructions,
            "task_description": task_description,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "language": skill_a.language,
            "tags": tags,
        }
