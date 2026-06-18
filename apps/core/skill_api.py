import logging
from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.core.models import SkillTemplate, SkillVerification
from .schemas_skill import SkillOut, SkillCreate, SkillUpdate, SkillTestOut, SkillTestRequest

logger = logging.getLogger(__name__)
router = Router(tags=["Skills - 技能庫"])


@router.get("/", response=List[SkillOut])
def list_skills(request, q: str = "", language: str = "", deprecated: bool = False):
    """列出所有技能，支援搜尋與篩選"""
    qs = SkillTemplate.objects.all()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(tags__icontains=q)
        )
    if language:
        qs = qs.filter(language=language)
    if not deprecated:
        qs = qs.filter(is_deprecated=False)
    return list(qs.order_by("-is_robust", "-usage_count", "-updated_at"))


@router.get("/{skill_id}", response=SkillOut)
def get_skill(request, skill_id: int):
    """取得單一技能詳情"""
    return get_object_or_404(SkillTemplate, id=skill_id)


@router.post("/", response=SkillOut)
def create_skill(request, payload: SkillCreate):
    """建立新技能"""
    try:
        skill = SkillTemplate(
            name=payload.name,
            description=payload.description,
            instructions=payload.instructions,
            language=payload.language or "python",
            tags=payload.tags or [],
            input_schema=payload.input_schema or {},
            output_schema=payload.output_schema or {},
            script_body=payload.script_body or "",
            script_content=payload.script_content or "",
        )
        skill.save()
        return skill
    except ValidationError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.exception("Failed to create skill")
        raise HttpError(400, f"創建技能失敗: {e}")


@router.patch("/{skill_id}", response=SkillOut)
def update_skill(request, skill_id: int, payload: SkillUpdate):
    """更新技能（PATCH，只傳需要修改的欄位）"""
    skill = get_object_or_404(SkillTemplate, id=skill_id)
    updates = payload.model_dump(exclude_unset=True)
    try:
        for attr, value in updates.items():
            setattr(skill, attr, value)
        skill.save()
        return skill
    except ValidationError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        logger.exception("Failed to update skill")
        raise HttpError(400, f"更新技能失敗: {e}")


@router.delete("/{skill_id}")
def delete_skill(request, skill_id: int):
    """硬刪除技能"""
    skill = get_object_or_404(SkillTemplate, id=skill_id)
    try:
        name = skill.name
        skill.delete()
        logger.info(f"[SkillAPI] Hard-deleted skill '{name}' (ID={skill_id})")
        return {"success": True, "message": f"技能 '{name}' 已刪除"}
    except Exception as e:
        logger.exception("Failed to delete skill")
        raise HttpError(400, f"刪除技能失敗: {e}")


@router.post("/{skill_id}/test", response=SkillTestOut)
def test_skill(request, skill_id: int, payload: SkillTestRequest = SkillTestRequest()):
    """在 Docker Sandbox 中執行技能並驗證結果

    若 payload.test_input 提供，使用該輸入；否則由 LLM 自動產生測試輸入。
    """
    get_object_or_404(SkillTemplate, id=skill_id)
    try:
        from apps.auto.skill_verifier import SkillVerifier
        verifier = SkillVerifier()
        if payload.test_input is not None:
            result = verifier.verify(skill_id, test_input=payload.test_input)
        else:
            result = verifier.verify(skill_id)
        raw = result.get("raw_output")
        if raw and len(raw) > 2000:
            raw = raw[:2000] + "\n... [truncated]"
        return SkillTestOut(
            ok=result.get("ok", False),
            verification_id=result.get("verification_id"),
            verdict=result.get("verdict"),
            confidence=result.get("confidence"),
            error=result.get("error"),
            exit_code=result.get("exit_code"),
            duration_ms=result.get("duration_ms"),
            raw_output=raw,
            agent_notes=result.get("agent_notes"),
        )
    except Exception as e:
        logger.exception(f"Skill test failed for #{skill_id}")
        return SkillTestOut(ok=False, error=str(e)[:500])
