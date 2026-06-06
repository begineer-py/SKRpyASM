import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from apps.core.models import Overview, Step, IP, Subdomain, URLResult
from apps.analyze_ai.tasks.planning import propose_next_steps

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
    2. Overviews in EXECUTING with no active steps for > 30 mins.
    3. Overviews in EXECUTING with stuck active steps for > 30 mins.
    """
    from apps.core.models.analyze.Step import StepNote

    now = timezone.now()
    summary = {"recovered_planning": 0, "recovered_executing": 0}
    now_time = timezone.now()

    # 1. Recover PLANNING overviews
    stalled_planning = list(Overview.objects.filter(
        status="PLANNING",
        updated_at__lt=now - timedelta(minutes=15)
    ))
    for ov in stalled_planning:
        logger.warning(f"[Watchdog] Overview#{ov.id} stalled in PLANNING. Sending rescue message.")
        send_rescue_message(ov, f"[SYSTEM Watchdog] 任務中斷或等候超時: Overview #{ov.id} 卡在 PLANNING 超過 15 分鐘。請呼叫 get_target_context 重新確認狀態並繼續行動，或是結束任務。")
        ov.updated_at = now_time
        summary["recovered_planning"] += 1

    if stalled_planning:
        Overview.objects.bulk_update(stalled_planning, ['updated_at'])

    # 2. Recover EXECUTING overviews
    stalled_executing = Overview.objects.filter(
        status="EXECUTING",
        updated_at__lt=now - timedelta(minutes=30)
    )
    executing_to_update = []
    for ov in stalled_executing:
        active_steps = ov.steps.filter(status__in=["PENDING", "RUNNING", "WAITING_FOR_ASYNC"])
        if active_steps.count() == 0:
            logger.warning(f"[Watchdog] Overview#{ov.id} stalled in EXECUTING with no active steps. Sending rescue message.")
            send_rescue_message(ov, f"[SYSTEM Watchdog] 任務中斷: Overview #{ov.id} 正在 EXECUTING 但超過 30 分鐘沒有新的步驟。你是否已經完成滲透？請呼叫 get_target_context 重新檢視狀態，並決定下一步或是呼叫 notify_caller_agent 結束任務。")
            ov.updated_at = now_time
            executing_to_update.append(ov)
            summary["recovered_executing"] += 1
        else:
            # Handle cases where steps are waiting for async for too long
            stuck_steps = list(active_steps.filter(updated_at__lt=now - timedelta(minutes=30)))
            if stuck_steps:
                logger.warning(f"[Watchdog] Overview#{ov.id} has stuck steps. Marking FAILED and sending rescue message.")
                for step in stuck_steps:
                    step.status = "FAILED"
                Step.objects.bulk_update(stuck_steps, ['status'])
                StepNote.objects.bulk_create([
                    StepNote(step=step, content="[SYSTEM Watchdog] Step timed out (>30m). Forced FAILED.")
                    for step in stuck_steps
                ])
                send_rescue_message(ov, f"[SYSTEM Watchdog] 任務超時: Overview #{ov.id} 的部分非同步工具執行超過 30 分鐘無回應，已被強制標記為 FAILED。請呼叫 get_target_context 繼續其他未完成的計畫。")
                ov.updated_at = now_time
                executing_to_update.append(ov)
                summary["recovered_executing"] += 1

    if executing_to_update:
        Overview.objects.bulk_update(executing_to_update, ['updated_at'])

    # 3. Sanitation: Delete orphaned assets
    summary["deleted_orphans"] = {
        "ips": IP.objects.filter(target__isnull=True).delete()[0],
        "subdomains": Subdomain.objects.filter(target__isnull=True).delete()[0],
        "url_results": URLResult.objects.filter(target__isnull=True).delete()[0],
        "overviews": Overview.objects.filter(target__isnull=True).delete()[0],
    }
    
    if any(summary["deleted_orphans"].values()):
        logger.info(f"[Watchdog] Cleaned up orphaned assets: {summary['deleted_orphans']}")

    return summary


# =============================================================================
# Thread Compression (對話級記憶壓縮)
# =============================================================================

THREAD_COMPRESSION_THRESHOLD = 40  # Message 條數上限
KEEP_RECENT_RATIO = 0.30           # 保留最近 30% 的 Messages

@shared_task(name="scheduler.tasks.compress_long_threads")
def compress_long_threads():
    """
    定時任務：掃描所有活躍 AI Thread，
    若訊息數量超過閾值則壓縮舊訊息為摘要，防止 Token 視窗爆炸。
    """
    from apps.core.models.ai_models import Thread, Message
    from langchain_core.messages import message_to_dict
    import json

    # 找出活躍 Overview 綁定的 Thread
    active_overviews = Overview.objects.filter(status__in=["PLANNING", "EXECUTING","COMPLETED"])
    active_thread_ids = set()
    for ov in active_overviews:
        if ov.thread_id:
            active_thread_ids.add(ov.thread_id)

    compressed_count = 0

    for thread_id in active_thread_ids:
        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            continue

        messages = list(Message.objects.filter(thread=thread).order_by("created_at"))
        total = len(messages)

        if total <= THREAD_COMPRESSION_THRESHOLD:
            continue

        # 計算要壓縮的範圍
        keep_count = max(int(total * KEEP_RECENT_RATIO), 5)
        messages_to_compress = messages[:total - keep_count]

        if len(messages_to_compress) < 5:
            continue

        # 將舊訊息內容拼接為純文字
        text_parts = []
        for msg in messages_to_compress:
            data = msg.message
            role = data.get("type", "unknown")
            content = data.get("data", {}).get("content", "")
            if content:
                text_parts.append(f"[{role}] {content[:500]}")

        conversation_text = "\n".join(text_parts)[:30000]

        # 呼叫 LLM 壓縮
        try:
            from langchain_mistralai import ChatMistralAI
            from langchain_core.messages import HumanMessage as LCHumanMessage

            llm = ChatMistralAI(model="mistral-small-2503", temperature=0, max_tokens=25000)
            prompt = (
                "你是一個安全分析師的記憶管理助手。以下是一段 AI 滲透測試對話的舊訊息。"
                "請產生一份精確的對話摘要（最多 20000 字），保留所有重要的：\n"
                "1. 已知目標資訊（IP、域名、技術棧）\n"
                "2. 已完成的掃描步驟與結果\n"
                "3. 已發現的漏洞或攻擊向量\n"
                "4. 當前進度與下一步計畫\n"
                "5. 所有關鍵 ID（overview_id, step_id, blob_id 等）\n\n"
                f"=== 對話歷史 ===\n{conversation_text}"
            )
            resp = llm.invoke([LCHumanMessage(content=prompt)])
            summary = resp.content[:2000]
        except Exception as e:
            logger.error(f"Thread compression LLM failed for thread {thread_id}: {e}")
            continue

        # 刪除舊 Messages
        old_ids = [m.id for m in messages_to_compress]
        Message.objects.filter(id__in=old_ids).delete()

        # 清理殘留的孤兒 tool messages（防止 tool-after-system/human 的無效順序）
        remaining = list(Message.objects.filter(thread=thread).order_by("created_at"))
        orphan_ids = []
        for rm in remaining:
            msg_type = rm.message.get("type", "")
            # tool messages 不能出現在 human/ai 前面
            if msg_type == "tool":
                orphan_ids.append(rm.id)
            else:
                break  # 碰到第一個非-tool 訊息就停
        if orphan_ids:
            Message.objects.filter(id__in=orphan_ids).delete()
            logger.info(f"[ThreadCompression] Cleaned {len(orphan_ids)} orphan tool messages from Thread#{thread_id}")

        # 在開頭插入壓縮摘要 (使用 HumanMessage，確保 role 順序合法)
        compressed_msg_data = message_to_dict(
            LCHumanMessage(content=f"[COMPRESSED HISTORY] 以下是你先前 {len(messages_to_compress)} 條對話的濃縮摘要：\n\n{summary}")
        )
        Message.objects.create(
            thread=thread,
            message=compressed_msg_data,
        )

        compressed_count += 1
        logger.info(
            f"[ThreadCompression] Thread#{thread_id}: 壓縮了 {len(messages_to_compress)}/{total} 條訊息 → 摘要 + {keep_count} 條最新訊息"
        )

    return f"Compressed {compressed_count} threads."
