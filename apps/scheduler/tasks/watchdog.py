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

@shared_task(name="scheduler.tasks.watchdog_stalled_overviews")
def watchdog_stalled_overviews():
    """
    Watchdog task to identify and recover stalled Overviews.
    1. Overviews in PLANNING for > 15 mins.
    2. Overviews in EXECUTING with no active execution graphs for > 30 mins.
    3. Overviews in EXECUTING with stuck execution nodes for > 30 mins.
    """
    now = timezone.now()
    summary = {"recovered_planning": 0, "recovered_executing": 0}
    now_time = timezone.now()

    # 1. Recover PLANNING overviews — 自動觸發策略規劃，而非僅發送救援訊息
    stalled_planning = list(Overview.objects.filter(
        status="PLANNING",
        updated_at__lt=now - timedelta(minutes=15)
    ))
    for ov in stalled_planning:
        logger.warning(f"[Watchdog] Overview#{ov.id} stalled in PLANNING. Triggering propose_next_steps.")
        # 鏈式修復：自動觸發策略規劃，不再依賴 Agent 回應
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
            ov.save(update_fields=["status", "updated_at"])
            logger.info(f"[Watchdog] Overview#{ov.id} has active execution but stuck in PLANNING, fixed to EXECUTING")
            summary["recovered_planning"] += 1
        send_rescue_message(ov, f"[SYSTEM Watchdog] 概觀 #{ov.id} 在規劃中停滯超過 15 分鐘。系統已自動觸發策略規劃或修正狀態。")
        ov.updated_at = now_time

    if stalled_planning:
        Overview.objects.bulk_update(stalled_planning, ['updated_at'])

    # 2. Recover EXECUTING overviews
    stalled_executing = Overview.objects.filter(
        status="EXECUTING",
        updated_at__lt=now - timedelta(minutes=30)
    )
    executing_to_update = []
    for ov in stalled_executing:
        thread_ids = [value for value in [ov.thread_id, ov.parent_thread_id] if value]
        active_graphs = ExecutionGraph.objects.filter(
            thread_id__in=thread_ids,
            status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
        ) if thread_ids else ExecutionGraph.objects.none()
        if active_graphs.count() == 0:
            logger.warning(f"[Watchdog] Overview#{ov.id} stalled in EXECUTING with no active executions. Sending rescue message.")
            send_rescue_message(ov, f"[SYSTEM Watchdog] 任務中斷: Overview #{ov.id} 正在 EXECUTING 但超過 30 分鐘沒有新的步驟。你是否已經完成滲透？請呼叫 get_target_context 重新檢視狀態，並決定下一步或是呼叫 notify_caller_agent 結束任務。")
            ov.updated_at = now_time
            executing_to_update.append(ov)
            summary["recovered_executing"] += 1
        else:
            # Handle cases where execution nodes are waiting/running for too long
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
        Overview.objects.bulk_update(executing_to_update, ['updated_at'])

    return summary
