"""
臨時腳本升級工具

將成功驗證的 ScriptExecution 自動升級到 SkillTemplate，
實現「低成本臨時 → 持久技能」的自動進階機制。

使用方式：
    from apps.core.script_upgrader import promote_to_skill
    
    promote_to_skill(
        script_execution_id=123,
        skill_name="csrf-bypass-django",
        tags=["django", "csrf", "bypass"]
    )
"""

from django.core.exceptions import ValidationError
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ScriptUpgradeError(Exception):
    """腳本升級失敗"""
    pass


def promote_to_skill(
    script_execution_id: int,
    skill_name: str,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
    force: bool = False
) -> Tuple[bool, str]:
    """
    將成功的 ScriptExecution 升級為 SkillTemplate。
    
    升級規則：
    1. 必須是 SUCCESS 狀態且通過輸出驗證
    2. 必須從 ScriptExecution 中提取 input_schema / output_schema
    3. 自動生成 instructions（如果沒有指定）
    4. 保留完整的執行上下文
    
    Args:
        script_execution_id: ScriptExecution 的 ID
        skill_name: 新技能的名稱（kebab-case）
        tags: 技能標籤列表
        description: 技能描述（如果 None，自動生成）
        force: 強制升級（即使狀態不是 SUCCESS）
    
    Returns:
        (is_success: bool, message: str)
    """
    from apps.core.models.analyze.AttackVector import ScriptExecution
    from apps.core.models.analyze.SkillTemplate import SkillTemplate
    
    # 1. 取得 ScriptExecution
    try:
        script_exec = ScriptExecution.objects.get(id=script_execution_id)
    except ScriptExecution.DoesNotExist:
        return False, f"ScriptExecution #{script_execution_id} 不存在"
    
    # 2. 檢查升級條件
    if not force:
        if script_exec.status != "SUCCESS":
            return False, f"只有 SUCCESS 狀態的執行才能升級，目前狀態: {script_exec.status}"
        
        if script_exec.validation_status not in ("VALIDATED", "NOT_VALIDATED"):
            return False, f"輸入/輸出驗證失敗，無法升級: {script_exec.validation_status}"
    
    # 3. 檢查名稱是否已存在
    try:
        existing = SkillTemplate.objects.get(name=skill_name)
        return False, f"Skill '{skill_name}' 已存在 (ID: {existing.id})"
    except SkillTemplate.DoesNotExist:
        pass
    
    # 4. 生成 description（如果沒有指定）
    if description is None:
        if script_exec.attack_vector:
            description = f"Script to handle attack vector: {script_exec.attack_vector.name}"
        elif script_exec.step:
            description = f"Script from Step #{script_exec.step.id}"
        else:
            description = "Promoted from successful script execution"
    
    # 5. 生成 instructions
    instructions = _generate_instructions(script_exec)
    
    # 6. 創建 SkillTemplate
    try:
        skill = SkillTemplate.objects.create(
            name=skill_name,
            description=description,
            instructions=instructions,
            script_content=script_exec.script_content,
            language=script_exec.script_language,
            tags=tags or [],
            input_schema=script_exec.input_json or {},
            output_schema=script_exec.output_json or {},
            version=1,
            is_robust=False,  # 新升級的技能需要進一步驗證
        )
        
        # 將 ScriptExecution 關聯到新技能
        script_exec.skill = skill
        script_exec.save(update_fields=["skill"])
        
        logger.info(f"Successfully promoted ScriptExecution #{script_execution_id} to Skill '{skill_name}'")
        return True, f"[SUCCESS] Script promoted to Skill '{skill_name}' (ID: {skill.id}). 标记为 v{skill.version}，尚需进一步验证以升级为 ROBUST。"
    
    except ValidationError as e:
        return False, f"Skill 驗證失敗: {str(e)}"
    except Exception as e:
        return False, f"升級失敗: {str(e)}"


def _generate_instructions(script_exec) -> str:
    """
    根據 ScriptExecution 自動生成 instructions
    """
    from apps.core.models.analyze.AttackVector import ScriptExecution
    
    instructions = f"""# Script Instructions

## Overview
This script was automatically promoted from a successful execution.
- Created: {script_exec.started_at.isoformat()}
- Source: Step #{script_exec.step.id if script_exec.step else 'Unknown'}
- Language: {script_exec.script_language}

## Execution Details
- Arguments: {script_exec.args_string or 'None'}
- Exit Code: {script_exec.exit_code}
- Execution Duration: {script_exec.execution_duration_ms}ms

"""
    
    if script_exec.input_json:
        instructions += f"""## Input Parameters
Expected input format:
```json
{json_dumps_pretty(script_exec.input_json)}
```

"""
    
    if script_exec.output_json:
        instructions += f"""## Output Format
Expected output format (JSON):
```json
{json_dumps_pretty(script_exec.output_json)}
```

"""
    
    instructions += f"""## Script Source
```{script_exec.script_language}
{script_exec.script_content}
```

## Notes
- This script was automatically promoted from a successful execution
- It may need further testing before marking as ROBUST
- Consider running it against multiple targets to verify stability
"""
    
    return instructions


def json_dumps_pretty(obj) -> str:
    """Pretty-print JSON"""
    import json
    return json.dumps(obj, indent=2)


def mark_skill_as_robust(skill_id: int, verified: bool = True) -> Tuple[bool, str]:
    """
    將技能標記為 ROBUST（已充分驗證）
    
    Args:
        skill_id: SkillTemplate 的 ID
        verified: 是否已驗證
    
    Returns:
        (is_success, message)
    """
    from apps.core.models.analyze.SkillTemplate import SkillTemplate
    from django.utils import timezone
    
    try:
        skill = SkillTemplate.objects.get(id=skill_id)
        skill.is_robust = verified
        if verified:
            skill.last_verified_at = timezone.now()
        skill.save(update_fields=["is_robust", "last_verified_at"])
        
        status = "ROBUST" if verified else "TESTING"
        return True, f"Skill '{skill.name}' marked as {status}"
    except SkillTemplate.DoesNotExist:
        return False, f"Skill #{skill_id} not found"
    except Exception as e:
        return False, f"Failed to update skill: {str(e)}"


def get_scripts_ready_for_promotion(
    min_success_count: int = 1,
    validation_status: str = "VALIDATED"
) -> list:
    """
    查詢可以升級到 SkillTemplate 的 ScriptExecution
    
    條件：
    1. 必須是 SUCCESS 狀態
    2. 必須通過驗證
    3. 未關聯到任何 SkillTemplate
    
    Args:
        min_success_count: 最少成功執行次數（默認 1）
        validation_status: 驗證狀態（默認 VALIDATED）
    
    Returns:
        ScriptExecution 列表
    """
    from apps.core.models.analyze.AttackVector import ScriptExecution
    from django.db.models import Count
    
    return list(
        ScriptExecution.objects
        .filter(
            status="SUCCESS",
            skill__isnull=True,
            validation_status=validation_status
        )
        .order_by("-started_at")
    )
