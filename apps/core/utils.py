import asyncio
import functools
import inspect
import logging
from typing import Callable, Any

from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


def _resolve_callback_step_id(func, args, kwargs):
    if 'callback_step_id' in kwargs:
        return kwargs['callback_step_id']
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        return bound_args.arguments.get('callback_step_id')
    except Exception:
        return None


def _set_step_running(callback_step_id):
    try:
        from .models import Step
        Step.objects.filter(id=callback_step_id).update(status="RUNNING")
        logger.info(f"Step#{callback_step_id} 狀態已更新為 RUNNING。")
    except Exception as e:
        logger.warning(f"無法更新 Step#{callback_step_id} 狀態為 RUNNING: {e}")


def _set_step_completed(callback_step_id):
    try:
        from .models import Step
        from django.utils import timezone
        Step.objects.filter(id=callback_step_id).update(
            status="COMPLETED",
            completed_at=timezone.now()
        )
        logger.info(f"Step#{callback_step_id} 狀態已更新為 COMPLETED。")
    except Exception as e:
        logger.warning(f"無法更新 Step#{callback_step_id} 狀態為 COMPLETED: {e}")


def _fire_callback(func, callback_step_id, result):
    """Fire the AI thread callback after task completion (sync)."""
    try:
        logger.info(f"偵測到 callback_step_id={callback_step_id}，掃描完成。準備發送 Callback...")

        raw_summary = str(result) if result is not None else f"✅ 掃描任務 {func.__name__} 完成 (回報 ID: {callback_step_id})"
        max_len = 5000
        summary = raw_summary[:max_len]
        if len(raw_summary) > max_len:
            summary += f"\n... [輸出過長，已截斷至 {max_len} 字元，原始長度 {len(raw_summary)} 字元]"

        try:
            from .models import Step
            from apps.core.models.ai_models import Thread
            from apps.ai_assistant.helpers.use_cases import create_message
            from django.contrib.auth import get_user_model

            step_obj = Step.objects.select_related('overview').filter(id=callback_step_id).first()
            thread_id = None

            if step_obj and step_obj.overview:
                thread_id = step_obj.overview.thread_id
                if not thread_id:
                    thread_id = step_obj.overview.parent_thread_id
                    if thread_id:
                        logger.info(f"overview.thread_id 為 None，改用 parent_thread_id={thread_id} 作回調目標。")
            if not thread_id:
                from apps.core.models.ai_models import Thread
                latest = Thread.objects.filter(assistant_id="automation_agent").order_by('-updated_at').first()
                if latest:
                    thread_id = latest.id
                    logger.warning(f"overview.thread_id 與 parent_thread_id 皆為空，使用最近的 automation_agent Thread ID={thread_id} 作應急回調。")

            if thread_id:
                thread_obj = Thread.objects.get(id=thread_id)
                User = get_user_model()
                system_user = thread_obj.created_by or User.objects.filter(is_superuser=True).first()

                new_url_ids = []
                try:
                    from apps.core.models.url_assets import URLResult
                    if step_obj and step_obj.overview and step_obj.overview.target_id:
                        new_url_ids = list(
                            URLResult.objects.filter(target_id=step_obj.overview.target_id)
                            .values_list('id', flat=True)[:20]
                        )
                except Exception:
                    pass

                url_hint = (
                    f"\n\n[ACTION REQUIRED] Call `get_url_intelligence(url_id=<id>)` for each of these URL IDs to read the newly fetched content: {new_url_ids}. "
                    f"Then proceed with form submission and injection testing using `run_command`."
                    if new_url_ids else ""
                )
                callback_msg = f"[系統回調] 任務已非同步完成：\n{summary}{url_hint}"
                create_message(
                    assistant_id="automation_agent",
                    thread=thread_obj,
                    user=system_user,
                    content=callback_msg,
                )
                logger.info(f"成功向 Thread {thread_id} 發送完成回調。")
            else:
                logger.error(f"Step {callback_step_id} 無任何可用的 thread_id（包含 fallback），無法發送回調。")
        except Exception as inner_e:
            logger.error(f"Callback 通知 AI 失敗: {inner_e}")
    except Exception as e:
        logger.error(f"觸發 callback_step_id={callback_step_id} 失敗: {e}")


def with_auto_callback(func: Callable) -> Callable:
    """
    通用回調裝飾器：只要任務參數中有 callback_step_id，結束後自動喚醒
    支援同步與非同步任務。
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            callback_step_id = _resolve_callback_step_id(func, args, kwargs)

            if callback_step_id:
                await sync_to_async(_set_step_running)(callback_step_id)

            result = await func(*args, **kwargs)

            if callback_step_id:
                await sync_to_async(_set_step_completed)(callback_step_id)
                await sync_to_async(_fire_callback)(func, callback_step_id, result)

            return result
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        callback_step_id = _resolve_callback_step_id(func, args, kwargs)

        # 掃描開始前，將 Step 標為 RUNNING
        if callback_step_id:
            _set_step_running(callback_step_id)

        # 執行原本的掃描任務
        result = func(*args, **kwargs)

        # 掃描完成後，將 Step 標為 COMPLETED 並設置 completed_at
        if callback_step_id:
            _set_step_completed(callback_step_id)
        
        if callback_step_id:
            _fire_callback(func, callback_step_id, result)

        return result
    return wrapper
