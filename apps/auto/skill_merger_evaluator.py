"""
Skill Merge Evaluator Agent

定期檢查資料庫中 tag 重疊的技能對，使用 AI Agent 評估是否有合併空間。
參考壓縮系統（apps/auto/compression/）的 LLM 評估設計模式。

流程：
  1. 找出 tags 有交集的技能對 (skill_a, skill_b)
  2. 檢查 SkillMergeEvaluation 是否已評估過 → 跳過
  3. 用 LLM 評估合併價值
  4. 記錄評估結果
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from pydantic import BaseModel, Field

from apps.ai_assistant.prompts import PromptSpec, TaskDefinition

logger = logging.getLogger(__name__)


class MergeEvalOutput(BaseModel):
    """Structured output for merge evaluation LLM call."""
    is_mergeable: bool = Field(description="是否可以合併")
    merge_strategy: str = Field(description="合併策略（如 NOT_RECOMMENDED/CONCAT/UNION 等）")
    reasoning: str = Field(description="詳細推理過程")
    suggested_name: Optional[str] = Field(default=None, description="合併後的建議名稱")
    suggested_tags: Optional[list[str]] = Field(default=None, description="合併後的建議標籤")
    overlap_analysis: Optional[dict] = Field(default=None, description="重疊分析")


# ════════════════════════════════════════════════════════════════════
# PromptSpec 宣告（取代原本的字串常數）
# ════════════════════════════════════════════════════════════════════

MERGE_EVAL_SPEC = PromptSpec(
    name="SkillMergeEvaluator",
    role="Skill Merge Evaluation Agent",
    task=TaskDefinition(
        goal="分析兩個滲透測試技能，判斷是否可合併為單一統一技能。",
        background="資料庫中 tag 重疊的技能對需要被評估是否有合併價值，避免重複技能堆積。",
        materials=(
            "兩個技能的完整資訊（各 8 欄）：name/description/tags/language/input_schema/"
            "output_schema/instructions/script_summary（A 與 B 各一份）。"
        ),
        boundary=(
            "1. merge_strategy 必須是受控詞彙之一（case-sensitive）：\n"
            "   NOT_RECOMMENDED | CONCAT | UNION | LATEST_ONLY | SMART_MERGE | "
            "A_MERGES_INTO_B | B_MERGES_INTO_A\n"
            "2. reasoning 必須為繁體中文。\n"
            "3. 輸出合法 JSON，不要 markdown code block。"
        ),
        dod=(
            "回傳含 is_mergeable、merge_strategy、reasoning、suggested_name、"
            "suggested_tags、overlap_analysis（含 tag_overlap/purpose_similarity/"
            "script_compatibility）的 JSON。"
        ),
    ),
    template_body=(
        "<skill_context>\n<skill_a>\n<name>{name_a}</name>\n<description>{desc_a}</description>\n"
        "<tags>{tags_a}</tags>\n<language>{lang_a}</language>\n<input_schema>{input_a}</input_schema>\n"
        "<output_schema>{output_a}</output_schema>\n<instructions>{instructions_a}</instructions>\n"
        "<script_summary>{script_a}</script_summary>\n</skill_a>\n\n"
        "<skill_b>\n<name>{name_b}</name>\n<description>{desc_b}</description>\n"
        "<tags>{tags_b}</tags>\n<language>{lang_b}</language>\n<input_schema>{input_b}</input_schema>\n"
        "<output_schema>{output_b}</output_schema>\n<instructions>{instructions_b}</instructions>\n"
        "<script_summary>{script_b}</script_summary>\n</skill_b>\n</skill_context>\n\n"
        "<task>\nAnalyze whether these two skills should be merged. Consider:\n"
        "1. Do they solve the same type of problem?\n"
        "2. Do they target the same technology stack?\n"
        "3. Can their scripts be combined into one unified script?\n"
        "4. Would merging improve usability or cause confusion?\n</task>\n\n"
        "<strategy_guide>\n"
        "- NOT_RECOMMENDED: Skills are unrelated or serve different purposes\n"
        "- CONCAT: Merge descriptions, tags, and combine both scripts with clear separation\n"
        "- UNION: Full merge — unified script with combined functionality\n"
        "- LATEST_ONLY: Keep only the newer/richer skill, deprecate the other\n"
        "- SMART_MERGE: Scripts can be intelligently combined into one\n"
        "- A_MERGES_INTO_B: Skill A is a subset of Skill B\n"
        "- B_MERGES_INTO_A: Skill B is a subset of Skill A\n"
        "</strategy_guide>"
    ),
    output_schema=MergeEvalOutput,
    agent_id="skill_merger_evaluator_agent",
    temperature=0.2,
    output_format_hint=(
        "Return ONLY valid JSON. The merge_strategy field MUST be exactly one of these values (case-sensitive):\n"
        '  "NOT_RECOMMENDED" | "CONCAT" | "UNION" | "LATEST_ONLY" | "SMART_MERGE" | "A_MERGES_INTO_B" | "B_MERGES_INTO_A"\n\n'
        "JSON structure:\n"
        '{{\n  "is_mergeable": true | false,\n'
        '  "merge_strategy": "string from list above",\n'
        '  "reasoning": "Detailed analysis in Traditional Chinese",\n'
        '  "suggested_name": "name if mergeable, or null",\n'
        '  "suggested_tags": ["tag1", "tag2"],\n'
        '  "overlap_analysis": {{\n'
        '    "tag_overlap": ["shared_tag"],\n'
        '    "purpose_similarity": "high" | "medium" | "low",\n'
        '    "script_compatibility": "compatible" | "conflicting" | "independent"\n'
        '  }}\n}}'
    ),
)
MERGE_EVAL_PROMPT = MERGE_EVAL_SPEC  # 向後相容別名


def _extract_json(text: str) -> dict:
    """Extract JSON dict from LLM response text (handles markdown code blocks, etc.)."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    import re
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    brace_start = text.find('{')
    if brace_start != -1:
        brace_end = text.rfind('}')
        if brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass
    return {}


_VALID_STRATEGIES = {
    "NOT_RECOMMENDED", "CONCAT", "UNION", "LATEST_ONLY",
    "SMART_MERGE", "A_MERGES_INTO_B", "B_MERGES_INTO_A",
}


def _normalize_strategy(raw: str) -> str:
    """Map free-text LLM strategy to controlled vocabulary."""
    if not raw:
        return "NOT_RECOMMENDED"
    clean = raw.strip().upper()
    if clean in _VALID_STRATEGIES:
        return clean
    # fuzzy match
    low = raw.lower()
    if "not recommend" in low or "separate" in low or "keep" in low or "independent" in low:
        return "NOT_RECOMMENDED"
    if "concat" in low or "combine" in low or "merge" in low:
        return "CONCAT"
    if "union" in low or "unify" in low:
        return "UNION"
    if "latest" in low or "newer" in low or "new" in low:
        return "LATEST_ONLY"
    if "smart" in low or "intelligent" in low:
        return "SMART_MERGE"
    if "a_merge" in low or "a into" in low or "a <-" in low:
        return "A_MERGES_INTO_B"
    if "b_merge" in low or "b into" in low or "b <-" in low:
        return "B_MERGES_INTO_A"
    return "NOT_RECOMMENDED"


class SkillMergeEvaluator:
    """AI agent-based skill merge evaluator.

    Discovers skill pairs with overlapping tags, evaluates merge potential via LLM,
    and stores results to avoid redundant re-evaluation.
    """

    def __init__(self, llm=None):
        from apps.core.llms import get_llm_instance
        self._llm = llm or get_llm_instance(
            agent_id="skill_merger_evaluator_agent",
            temperature=0.2
        )

    def find_overlapping_pairs(self, max_pairs: int = 5) -> list[Tuple]:
        """Find skill pairs that share at least one common tag.

        Excludes:
        - Pairs already evaluated (SkillMergeEvaluation exists)
        - Deprecated skills
        - Skills of different languages (python vs bash)
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from apps.core.models.analyze.SkillMergeEvaluation import SkillMergeEvaluation
        from django.db.models import Q

        active_skills = list(
            SkillTemplate.objects.filter(is_deprecated=False).only("id", "name", "tags", "language")
        )

        if len(active_skills) < 2:
            return []

        # Build a tag → skills index
        tag_to_skills: dict[str, list] = {}
        for skill in active_skills:
            for tag in (skill.tags or []):
                tag_lower = tag.lower().strip()
                if tag_lower:
                    tag_to_skills.setdefault(tag_lower, []).append(skill)

        # Collect all existing evaluations to skip
        evaluated_pairs = set()
        for eval_record in SkillMergeEvaluation.objects.filter(
            Q(skill_a__in=[s.id for s in active_skills]),
            Q(skill_b__in=[s.id for s in active_skills]),
        ).values_list("skill_a_id", "skill_b_id"):
            evaluated_pairs.add((eval_record[0], eval_record[1]))
            evaluated_pairs.add((eval_record[1], eval_record[0]))

        # Find un-evaluated pairs with overlapping tags
        seen_pairs = set()
        pairs = []
        for tag, skills in tag_to_skills.items():
            if len(skills) < 2:
                continue
            for i in range(len(skills)):
                for j in range(i + 1, len(skills)):
                    a, b = skills[i], skills[j]
                    if a.language != b.language:
                        continue
                    pair_key = (a.id, b.id)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    if pair_key in evaluated_pairs:
                        continue
                    pairs.append((a, b))
                    if len(pairs) >= max_pairs:
                        return pairs
        return pairs

    def evaluate_pair(self, skill_a, skill_b) -> dict:
        """Evaluate merge potential for a single skill pair.

        Returns dict with evaluation result. Automatically saves to SkillMergeEvaluation.
        """
        from apps.core.models.analyze.SkillMergeEvaluation import SkillMergeEvaluation

        logger.info(f"[MergeEval] Evaluating: {skill_a.name} ↔ {skill_b.name}")

        prompt = MERGE_EVAL_PROMPT.format(
            name_a=skill_a.name,
            desc_a=skill_a.description or "",
            tags_a=json.dumps(skill_a.tags, ensure_ascii=False),
            lang_a=skill_a.language,
            input_a=json.dumps(skill_a.input_schema or {}, indent=2, ensure_ascii=False),
            output_a=json.dumps(skill_a.output_schema or {}, indent=2, ensure_ascii=False),
            instructions_a=(skill_a.instructions or "")[:300],
            script_a=(skill_a.script_content or "")[:200],
            name_b=skill_b.name,
            desc_b=skill_b.description or "",
            tags_b=json.dumps(skill_b.tags, ensure_ascii=False),
            lang_b=skill_b.language,
            input_b=json.dumps(skill_b.input_schema or {}, indent=2, ensure_ascii=False),
            output_b=json.dumps(skill_b.output_schema or {}, indent=2, ensure_ascii=False),
            instructions_b=(skill_b.instructions or "")[:300],
            script_b=(skill_b.script_content or "")[:200],
        )

        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            data = _extract_json(content)
            result = MergeEvalOutput(**data)
            is_mergeable = result.is_mergeable
            strategy = _normalize_strategy(result.merge_strategy)
            reasoning = result.reasoning
        except Exception as e:
            logger.warning(f"[MergeEval] LLM evaluation failed for {skill_a.name} ↔ {skill_b.name}: {e}")
            is_mergeable = False
            strategy = "NOT_RECOMMENDED"
            reasoning = f"LLM evaluation error: {e}"

        # Save evaluation record
        eval_record, created = SkillMergeEvaluation.objects.update_or_create(
            skill_a=skill_a,
            skill_b=skill_b,
            defaults={
                "is_mergeable": is_mergeable,
                "merge_strategy": strategy,
                "reasoning": reasoning,
                "evaluated_at": datetime.now(timezone.utc),
            },
        )

        logger.info(
            f"[MergeEval] Result for {skill_a.name} ↔ {skill_b.name}: "
            f"{'MERGEABLE' if is_mergeable else 'NOT_MERGEABLE'} "
            f"(strategy={strategy})"
        )

        return {
            "ok": True,
            "evaluation_id": eval_record.id,
            "is_mergeable": is_mergeable,
            "merge_strategy": strategy,
            "reasoning": reasoning,
            "created": created,
        }

    def evaluate_all_pending(self, max_pairs: int = 5) -> list[dict]:
        """Find and evaluate all pending merge candidates.

        Args:
            max_pairs: Maximum number of pairs to evaluate in one run.

        Returns:
            List of evaluation result dicts.
        """
        results = []
        pairs = self.find_overlapping_pairs(max_pairs=max_pairs)

        if not pairs:
            logger.info("[MergeEval] No pending merge candidates found.")
            return [{"ok": True, "message": "No pending candidates"}]

        logger.info(f"[MergeEval] Found {len(pairs)} pending merge candidate(s).")

        for skill_a, skill_b in pairs:
            try:
                result = self.evaluate_pair(skill_a, skill_b)
                results.append(result)
            except Exception as e:
                logger.exception(f"[MergeEval] Error evaluating pair {skill_a.id} ↔ {skill_b.id}: {e}")
                results.append({"ok": False, "error": str(e)})

        return results

    def perform_merge(self, evaluation_id: int) -> dict:
        """Execute an actual merge based on a previous evaluation.
        Delegates to SkillManagerAgent.
        """
        from apps.auto.skill_manager_agent import SkillManagerAgent
        manager = SkillManagerAgent(llm=self._llm)
        return manager.execute_merge(evaluation_id)
