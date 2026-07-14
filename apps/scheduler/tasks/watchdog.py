import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from apps.core.models import ExecutionGraph, ExecutionNode, Overview
from apps.core.services import ExecutionService

logger = logging.getLogger(__name__)

from apps.core.models.ai_models import Thread
from apps.ai_assistant.helpers.use_cases import create_message
from django.contrib.auth import get_user_model

# ─── 升級門檻 ────────────────────────────────────────────────────────
RESCUE_THRESHOLD_STALLED = 3        # rescue 3 次後 → STALLED
RESCUE_THRESHOLD_NEEDS_GUIDANCE = 5  # rescue 5 次後 → NEEDS_GUIDANCE

# 殭屍圖判定：graph 停滯時間
ZOMBIE_GRAPH_STALE_MINUTES = 30


def send_rescue_message(ov: Overview, msg: str):
    thread_id = ov.thread_id or ov.parent_thread_id
    if thread_id:
        try:
            thread = Thread.objects.get(id=thread_id)
            User = get_user_model()
            system_user = thread.created_by or User.objects.filter(is_superuser=True).first()
            create_message(
                assistant_id="automation_agent",
                thread=thread,
                user=system_user,
                content=msg
            )
            logger.info(f"發送救援訊息至 Thread {thread_id}")
        except Exception as e:
            logger.error(f"發送救援訊息失敗: {e}")


def _increment_rescue_count(ov: Overview) -> str | None:
    """遞增 rescue_count 並觸發狀態升級。

    Returns:
        new_status (str | None): 若觸發升級則回傳新狀態名稱，否則 None。
    """
    ov.rescue_count = (ov.rescue_count or 0) + 1
    new_status = None
    if ov.rescue_count >= RESCUE_THRESHOLD_NEEDS_GUIDANCE and ov.status != "NEEDS_GUIDANCE":
        ov.status = "NEEDS_GUIDANCE"
        new_status = "NEEDS_GUIDANCE"
    elif ov.rescue_count >= RESCUE_THRESHOLD_STALLED and ov.status == "EXECUTING":
        ov.status = "STALLED"
        new_status = "STALLED"
    return new_status


@shared_task(name="scheduler.tasks.watchdog_stalled_overviews")
def watchdog_stalled_overviews():
    """Watchdog task to identify and recover stalled Overviews.

    Phases:
      1. PLANNING stalled > 15 min → trigger propose_next_steps / fix status
      2. EXECUTING stalled > 30 min → rescue + escalation (3→STALLED, 5→NEEDS_GUIDANCE)
      3. Stuck execution nodes (> 30min WAITING / > 60min RUNNING) → fail_node + rescue
      4. Zombie graphs: graph=RUNNING + all nodes SUCCEEDED + updated_at > 30min
         → wake_agent_on_scan_completion (soft补救，L2 wake 漏網之魚)
    """
    now = timezone.now()
    now_time = timezone.now()
    summary = {
        "recovered_planning": 0,
        "recovered_executing": 0,
        "zombie_graphs_woken": 0,
        "escalated_to_stalled": 0,
        "escalated_to_needs_guidance": 0,
    }

    # ════════════════════════════════════════════════════════════════
    # Phase 1: Recover PLANNING overviews — 自動觸發策略規劃
    # ════════════════════════════════════════════════════════════════
    stalled_planning = list(Overview.objects.filter(
        status="PLANNING",
        updated_at__lt=now - timedelta(minutes=15)
    ))
    for ov in stalled_planning:
        logger.warning(f"[Watchdog] Overview#{ov.id} stalled in PLANNING. Triggering propose_next_steps.")
        thread_ids = [value for value in [ov.thread_id, ov.parent_thread_id] if value]
        has_active_execution = ExecutionGraph.objects.filter(
            thread_id__in=thread_ids,
            status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
        ).exists() if thread_ids else False
        if not has_active_execution:
            from apps.analyze_ai.tasks.planning import propose_next_steps
            propose_next_steps.delay(ov.id)
            summary["recovered_planning"] += 1
        else:
            # 有 active execution 但 PLANNING 狀態異常 → 修正為 EXECUTING
            ov.status = "EXECUTING"
            logger.info(f"[Watchdog] Overview#{ov.id} has active execution but stuck in PLANNING, fixed to EXECUTING")
            summary["recovered_planning"] += 1
        send_rescue_message(ov, f"[SYSTEM Watchdog] 概觀 #{ov.id} 在規劃中停滯超過 15 分鐘。系統已自動觸發策略規劃或修正狀態。")
        ov.updated_at = now_time

    if stalled_planning:
        Overview.objects.bulk_update(stalled_planning, ['status', 'updated_at'])

    # ════════════════════════════════════════════════════════════════
    # Phase 2: Recover EXECUTING overviews — 含 rescue_count 升級
    # ════════════════════════════════════════════════════════════════
    stalled_executing = list(Overview.objects.filter(
        status="EXECUTING",
        updated_at__lt=now - timedelta(minutes=30)
    ))
    executing_to_update = []
    for ov in stalled_executing:
        thread_ids = [value for value in [ov.thread_id, ov.parent_thread_id] if value]
        active_graphs = ExecutionGraph.objects.filter(
            thread_id__in=thread_ids,
            status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
        ) if thread_ids else ExecutionGraph.objects.none()

        if active_graphs.count() == 0:
            logger.warning(f"[Watchdog] Overview#{ov.id} stalled in EXECUTING with no active executions. Rescue + escalate.")
            # 遞增 rescue_count 並觸發升級
            escalated_to = _increment_rescue_count(ov)
            if escalated_to == "STALLED":
                summary["escalated_to_stalled"] += 1
                msg = (
                    f"[SYSTEM Watchdog] ⚠️ 任務 #{ov.id} 已 {ov.rescue_count} 次救援無回應（>30min 每次）。"
                    f"已自動升級為 STALLED。請人工檢視後再決定是否繼續。"
                )
            elif escalated_to == "NEEDS_GUIDANCE":
                summary["escalated_to_needs_guidance"] += 1
                msg = (
                    f"[SYSTEM Watchdog] 🚨 任務 #{ov.id} 已 {ov.rescue_count} 次救援無回應。"
                    f"已自動升級為 NEEDS_GUIDANCE。上層 StrategyAgent 將產生戰略指導。"
                )
            else:
                msg = (
                    f"[SYSTEM Watchdog] 任務中斷: Overview #{ov.id} 正在 EXECUTING 但超過 30 分鐘沒有新的步驟"
                    f"（rescue_count={ov.rescue_count}）。請呼叫 get_target_context 重新檢視狀態。"
                )
            send_rescue_message(ov, msg)
            ov.updated_at = now_time
            executing_to_update.append(ov)
            summary["recovered_executing"] += 1
        else:
            # Phase 3: Handle cases where execution nodes are waiting/running for too long
            stuck_async = list(ExecutionNode.objects.filter(
                graph__in=active_graphs,
                status=ExecutionNode.Status.WAITING,
                updated_at__lt=now - timedelta(minutes=30)
            ))
            stuck_running = list(ExecutionNode.objects.filter(
                graph__in=active_graphs,
                status=ExecutionNode.Status.RUNNING,
                updated_at__lt=now - timedelta(minutes=60)
            ))
            stuck_nodes = stuck_async + stuck_running
            if stuck_nodes:
                logger.warning(f"[Watchdog] Overview#{ov.id} has stuck execution nodes. Marking FAILED and sending rescue message.")
                for node in stuck_nodes:
                    ExecutionService.fail_node(
                        node,
                        error={"reason": "watchdog_timeout"},
                        content="[SYSTEM Watchdog] Execution node timed out. Forced FAILED.",
                        payload={"overview_id": ov.id},
                    )
                send_rescue_message(ov, f"[SYSTEM Watchdog] 任務超時: Overview #{ov.id} 的部分 execution node 執行超過限制無回應，已被強制標記為 FAILED。請呼叫 get_target_context 繼續其他未完成的計畫。")
                ov.updated_at = now_time
                executing_to_update.append(ov)
                summary["recovered_executing"] += 1

    if executing_to_update:
        Overview.objects.bulk_update(
            executing_to_update, ['status', 'rescue_count', 'updated_at']
        )

    # ════════════════════════════════════════════════════════════════
    # Phase 4: Zombie graph detection — L2 wake 漏網之魚補救
    # 偵測 graph=RUNNING 且 graph.updated_at < now-30min 的停滯圖。
    # 軟補救：呼叫 wake_agent_on_scan_completion 讓 agent 重新被喚醒。
    # ════════════════════════════════════════════════════════════════
    try:
        zombie_graphs = list(
            ExecutionGraph.objects.filter(
                status=ExecutionGraph.Status.RUNNING,
                updated_at__lt=now - timedelta(minutes=ZOMBIE_GRAPH_STALE_MINUTES),
            )
            .exclude(nodes__status__in=[
                ExecutionNode.Status.PENDING,
                ExecutionNode.Status.RUNNING,
                ExecutionNode.Status.WAITING,
            ])
            .distinct()
        )
        if zombie_graphs:
            logger.info(
                f"[Watchdog] Phase 4: detected {len(zombie_graphs)} zombie graph(s) "
                f"(RUNNING, no active nodes, stale > {ZOMBIE_GRAPH_STALE_MINUTES}min)"
            )
            try:
                from apps.auto.tasks import wake_agent_on_scan_completion
                for g in zombie_graphs:
                    logger.info(
                        f"[Watchdog] Triggering wake for zombie graph#{g.id} "
                        f"(thread={g.thread_id})"
                    )
                    wake_agent_on_scan_completion.delay(
                        thread_id=g.thread_id
                    )
                    summary["zombie_graphs_woken"] += 1
            except ImportError:
                logger.warning(
                    "[Watchdog] Phase 4: apps.auto.tasks not importable — skipping zombie wake"
                )
    except Exception as e:
        logger.warning(f"[Watchdog] Phase 4 zombie detection failed: {e}")

    return summary
