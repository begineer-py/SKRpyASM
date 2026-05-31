"""
Celery Beat 定時任務：技能系統自動化

1. verify_skills_periodic  — 用 SkillVerifier Agent 定期驗證久未測試的技能
2. evaluate_skill_merges   — 用 SkillMergeEvaluator Agent 定期評估 tag 重疊技能
"""
from __future__ import annotations

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.auto.tasks.verify_skills_periodic")
def verify_skills_periodic():
    """定期驗證技能：挑選久未驗證或從未驗證的技能，使用 AI Agent 驗證。

    條件（優先級由高到低）：
    1. last_verified_at IS NULL 且 is_robust=False（從未驗證的非穩健技能）
    2. last_verified_at < 7 天前（超過一週未驗證）
    3. last_failure_reason 不為空（上次失敗的技能需要重新確認）

    每次最多驗證 3 個，避免大量的 LLM token 消耗。
    """
    from apps.core.models.analyze.SkillTemplate import SkillTemplate

    cutoff = timezone.now() - timedelta(days=7)

    stale_skills = SkillTemplate.objects.filter(
        is_deprecated=False,
    ).filter(
        Q(last_verified_at__isnull=True, is_robust=False)
        | Q(last_verified_at__lt=cutoff)
        | (
            Q(last_failure_reason__isnull=False)
            & ~Q(last_failure_reason="")
        )
    ).order_by("last_verified_at", "usage_count")[:3]

    if not stale_skills.exists():
        logger.info("[SkillTasks] No stale skills to verify.")
        return {"ok": True, "verified_count": 0, "message": "No stale skills"}

    logger.info(f"[SkillTasks] Found {stale_skills.count()} stale skill(s) to verify.")

    from apps.auto.skill_verifier import SkillVerifier

    verifier = SkillVerifier()
    results = []

    for skill in stale_skills:
        logger.info(f"[SkillTasks] Verifying skill: {skill.name} v{skill.version}")
        try:
            result = verifier.verify(skill.id)
            results.append(result)
        except Exception as e:
            logger.exception(f"[SkillTasks] Verification failed for {skill.name}: {e}")
            results.append({"ok": False, "error": str(e)})

    success_count = sum(1 for r in results if r.get("ok"))
    logger.info(f"[SkillTasks] Verified {len(results)} skills ({success_count} succeeded).")

    return {
        "ok": True,
        "verified_count": len(results),
        "success_count": success_count,
        "results": results,
    }


@shared_task(name="apps.auto.tasks.evaluate_skill_merges")
def evaluate_skill_merges():
    """定期評估 tag 重疊的技能是否有合併空間。

    流程：
    1. 找出所有 active 技能中 tags 有交集的 pair
    2. 排除已存在 SkillMergeEvaluation 記錄的 pair
    3. 用 LLM 評估合併價值（每次最多 2 對）
    4. 記錄結果到 SkillMergeEvaluation
    5. 若評估為可合併，寫入建議的 merge_strategy

    注意：此任務只做「評估」，不自動執行合併。
    實際合併可由 AI agent 或管理員透過 `perform_merge()` 觸發。
    """
    from apps.auto.skill_merger_evaluator import SkillMergeEvaluator

    evaluator = SkillMergeEvaluator()
    results = evaluator.evaluate_all_pending(max_pairs=2)

    mergeable_count = sum(
        1 for r in results if r.get("is_mergeable")
    )
    total = len([r for r in results if r.get("ok")])

    logger.info(
        f"[SkillTasks] Merge evaluation: {total} pairs evaluated, "
        f"{mergeable_count} mergeable."
    )

    return {
        "ok": True,
        "evaluated_count": total,
        "mergeable_count": mergeable_count,
        "results": results,
    }


@shared_task(name="apps.auto.tasks.execute_pending_merges")
def execute_pending_merges():
    """自動執行已評估為可合併的項目。
    
    條件：
    - is_mergeable = True
    - merged_into IS NULL (尚未執行)
    - merge_strategy 不為空且不是 'NOT_RECOMMENDED'
    """
    from apps.core.models.analyze.SkillMergeEvaluation import SkillMergeEvaluation
    from apps.auto.skill_manager_agent import SkillManagerAgent

    pending_merges = SkillMergeEvaluation.objects.filter(
        is_mergeable=True,
        merged_into__isnull=True
    ).exclude(merge_strategy="NOT_RECOMMENDED").order_by("evaluated_at")[:2]

    if not pending_merges.exists():
        logger.info("[SkillTasks] No pending merges to execute.")
        return {"ok": True, "executed_count": 0}

    manager = SkillManagerAgent()
    results = []
    for pm in pending_merges:
        logger.info(f"[SkillTasks] Executing auto-merge for Eval {pm.id}: {pm.skill_a.name} ↔ {pm.skill_b.name}")
        try:
            res = manager.execute_merge(pm.id)
            results.append(res)
        except Exception as e:
            logger.exception(f"[SkillTasks] Auto-merge failed for Eval {pm.id}: {e}")
            results.append({"ok": False, "error": str(e)})

    return {
        "ok": True,
        "executed_count": len(results),
        "results": results
    }
