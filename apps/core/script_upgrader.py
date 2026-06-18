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
    從 ScriptExecution 升級為 SkillTemplate。
    如果 ScriptExecution 不存在或不可用，嘗試從 ExecutionArtifact 建立。
    """
    from apps.core.models.analyze.SkillTemplate import SkillTemplate
    from apps.core.models.analyze.AttackVector import ScriptExecution

    try:
        script_exec = ScriptExecution.objects.select_related("skill", "attack_vector").get(id=script_execution_id)
    except ScriptExecution.DoesNotExist:
        return False, f"ScriptExecution #{script_execution_id} 不存在"

    if not force:
        if script_exec.status != "SUCCESS":
            return False, f"只有 SUCCESS 狀態的執行才能升級，目前狀態: {script_exec.status}"
        if script_exec.validation_status not in ("VALIDATED", "NOT_VALIDATED"):
            return False, f"輸入/輸出驗證失敗，無法升級: {script_exec.validation_status}"

    if SkillTemplate.objects.filter(name=skill_name).exists():
        return False, f"Skill '{skill_name}' 已存在"

    if description is None:
        if script_exec.attack_vector:
            description = f"Script to handle attack vector: {script_exec.attack_vector.name}"
        else:
            description = "Promoted from successful script execution"

    instructions = _generate_instructions(script_exec)

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
            is_robust=False,
        )
        script_exec.skill = skill
        script_exec.save(update_fields=["skill"])
        logger.info(f"Successfully promoted ScriptExecution #{script_execution_id} to Skill '{skill_name}'")
        return True, f"Script promoted to Skill '{skill_name}' (ID: {skill.id})"
    except Exception as e:
        return False, f"升級失敗: {str(e)}"


def _generate_instructions(script_exec) -> str:
    """
    根據 execution artifact 形狀自動生成 instructions。
    """
    instructions = f"""# Script Instructions

## Overview
This script was automatically promoted from a successful execution.
- Created: {script_exec.started_at.isoformat()}
- Source: ExecutionArtifact
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
    return []
