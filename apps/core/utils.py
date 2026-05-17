import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def with_auto_callback(func: Callable) -> Callable:
    """
    通用回調裝飾器：只要任務參數中有 callback_step_id，結束後自動喚醒
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        import inspect
        
        # 解析傳入的參數，尋找 callback_step_id
        callback_step_id = None
        
        # 1. 嘗試直接從 kwargs 拿
        if 'callback_step_id' in kwargs:
            callback_step_id = kwargs['callback_step_id']
        else:
            # 2. 如果沒有，嘗試比對 signature 的位置參數
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                callback_step_id = bound_args.arguments.get('callback_step_id')
            except Exception:
                pass
        
        # 掃描開始前，將 Step 標為 RUNNING
        if callback_step_id:
            try:
                from .models import Step
                Step.objects.filter(id=callback_step_id).update(status="RUNNING")
                logger.info(f"Step#{callback_step_id} 狀態已更新為 RUNNING。")
            except Exception as e:
                logger.warning(f"無法更新 Step#{callback_step_id} 狀態為 RUNNING: {e}")
        
        # 執行原本的掃描任務
        result = func(*args, **kwargs)
        
        # 掃描完成後，將 Step 標為 COMPLETED 並設置 completed_at
        if callback_step_id:
            try:
                from .models import Step
                from django.utils import timezone
                Step.objects.filter(id=callback_step_id).update(
                    status="COMPLETED",
                    # 📍 P0 FIX: 設置 completed_at 時間戳
                    completed_at=timezone.now()
                )
                logger.info(f"Step#{callback_step_id} 狀態已更新為 COMPLETED。")
            except Exception as e:
                logger.warning(f"無法更新 Step#{callback_step_id} 狀態為 COMPLETED: {e}")
        
        # 統一處理喚醒邏輯
        if callback_step_id:
            try:
                logger.info(f"偵測到 callback_step_id={callback_step_id}，掃描完成。準備發送 Callback...")
                
                # 簡單取字串表示結果或摘要（截斷避免超過 AI context window 上限）
                raw_summary = str(result) if result is not None else f"✅ 掃描任務 {func.__name__} 完成 (回報 ID: {callback_step_id})"
                max_len = 5000
                summary = raw_summary[:max_len]
                if len(raw_summary) > max_len:
                    summary += f"\n... [輸出過長，已截斷至 {max_len} 字元，原始長度 {len(raw_summary)} 字元]"
                
                # 透過 Django AI Assistant create_message 喚醒 AI (Django ORM, 不需要 HTTP)
                try:
                    from .models import Step
                    from django_ai_assistant.models import Thread
                    from django_ai_assistant.helpers.use_cases import create_message
                    from django.contrib.auth import get_user_model

                    step_obj = Step.objects.select_related('overview').filter(id=callback_step_id).first()
                    thread_id = None
                    
                    if step_obj and step_obj.overview:
                        # 優先用 overview.thread_id（AI 自己的 Thread）
                        thread_id = step_obj.overview.thread_id
                        
                        # Fallback 1：用 parent_thread_id（呼叫此子 Agent 的上層）
                        if not thread_id:
                            thread_id = step_obj.overview.parent_thread_id
                            if thread_id:
                                logger.info(f"overview.thread_id 為 None，改用 parent_thread_id={thread_id} 作回調目標。")
                        
                        # Fallback 2：找最近一個 automation_agent 的 Thread
                        if not thread_id:
                            from django_ai_assistant.models import Thread
                            latest = Thread.objects.filter(assistant_id="automation_agent").order_by('-updated_at').first()
                            if latest:
                                thread_id = latest.id
                                logger.warning(f"overview.thread_id 與 parent_thread_id 皆為空，使用最近的 automation_agent Thread ID={thread_id} 作應急回調。")
                    
                    if thread_id:
                        thread_obj = Thread.objects.get(id=thread_id)
                        User = get_user_model()
                        system_user = thread_obj.created_by or User.objects.filter(is_superuser=True).first()

                        # Step 221 → we need to know which URLs are newly available
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
                        callback_msg = (
                            f"[系統回調] 任務已非同步完成：\n{summary}"
                            f"{url_hint}"
                        )
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
                
        return result
    return wrapper
