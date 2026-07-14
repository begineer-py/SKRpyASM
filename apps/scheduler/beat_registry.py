"""
集中式 Celery Beat 排程註冊表（Single Source of Truth）。

為避免散落多處的 PeriodicTask 建立邏輯，本模組統一定義所有核心排程任務：
  - 看門狗 (watchdog)
  - 清理孤立資產 (cleanup_orphaned_assets)
  - AI 資產初步分析 (periodic_initial_analysis_bootstrapper)
  - 自動執行計畫 (auto_execute_plan)
  - 技能驗證/合併評估

呼叫 ensure_core_schedules() 即可在 DB 中 idempotent 地建立所有任務。
使用時機：
  1. apps/scheduler/apps.py 的 post_migrate signal（自動）
  2. management command `setup_beat_schedules`（手動/部署腳本）
  3. docker compose init phase
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CoreSchedule:
    """一個核心排程任務的宣告。"""

    name: str
    task: str
    every: int
    period: str  # IntervalSchedule.PERIODICITY 的 choices
    enabled: bool = True
    description: str = ""


# ─── 所有核心排程任務（單一事實來源） ─────────────────────────────────
# 順序：最關鍵的監控任務在前
CORE_SCHEDULES: List[CoreSchedule] = [
    CoreSchedule(
        name="[Auto] Watchdog (Stalled Overviews Recovery)",
        task="scheduler.tasks.watchdog_stalled_overviews",
        every=5,
        period="minutes",
        description="監控 PLANNING 15min / EXECUTING 30min / 殭屍圖 → rescue + wake",
    ),
    CoreSchedule(
        name="[Auto] Cleanup Orphaned Assets",
        task="scheduler.tasks.cleanup_orphaned_assets",
        every=60,
        period="minutes",
        description="清除沒有關聯 Target 的孤立資產",
    ),
    CoreSchedule(
        name="[Auto] Periodic AI Asset Analysis",
        task="analyze_ai.tasks.periodic_initial_analysis_bootstrapper",
        every=30,
        period="minutes",
        description="初步資產 AI 分析",
    ),
    CoreSchedule(
        name="[Auto] Autonomous Plan Execution (Layer 3 AutomationAgent)",
        task="apps.auto.tasks.auto_execute_plan",
        every=15,
        period="minutes",
        description="自動化滲透執行",
    ),
    CoreSchedule(
        name="[Auto] Skill Verification (Periodic Testing)",
        task="apps.auto.tasks.verify_skills_periodic",
        every=30,
        period="minutes",
        description="定期技能驗證",
    ),
    CoreSchedule(
        name="[Auto] Skill Merge Evaluation",
        task="apps.auto.tasks.evaluate_skill_merges",
        every=30,
        period="minutes",
        description="技能合併評估",
    ),
]


def ensure_core_schedules() -> dict:
    """Idempotent 地建立所有核心排程任務到資料庫。

    Returns:
        dict: {"created": int, "updated": int, "skipped": int, "details": [...]}
    """
    from django_celery_beat.models import IntervalSchedule, PeriodicTask

    valid_periods = {"days", "hours", "minutes", "seconds", "microseconds"}
    # 快取 IntervalSchedule — same (every, period) 共用一個
    interval_cache: dict[tuple[int, str], IntervalSchedule] = {}

    created_count = 0
    updated_count = 0
    skipped_count = 0
    details = []

    for sched in CORE_SCHEDULES:
        if sched.period not in valid_periods:
            logger.warning(f"[beat_registry] Unknown period: {sched.period} (task={sched.task})")
            skipped_count += 1
            continue

        cache_key = (sched.every, sched.period)
        if cache_key not in interval_cache:
            interval_cache[cache_key], _ = IntervalSchedule.objects.get_or_create(
                every=sched.every,
                period=sched.period,
            )
        interval = interval_cache[cache_key]

        obj, was_created = PeriodicTask.objects.update_or_create(
            name=sched.name,
            defaults={
                "task": sched.task,
                "interval": interval,
                "enabled": sched.enabled,
            },
        )
        if was_created:
            created_count += 1
            action = "created"
        else:
            updated_count += 1
            action = "updated"
        details.append(f"{action}: {sched.name} → every {sched.every} {sched.period}")
        logger.info(f"[beat_registry] {action}: {sched.name}")

    logger.info(
        f"[beat_registry] Done: {created_count} created, {updated_count} updated, {skipped_count} skipped"
    )
    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "details": details,
    }
