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
        
        # 執行原本的掃描任務
        result = func(*args, **kwargs)
        
        # 統一處理喚醒邏輯
        if callback_step_id:
            try:
                # 延遲導入避免循環依賴
                from apps.auto.tasks.execution.runner import resume_step_execution
                logger.info(f"偵測到 callback_step_id={callback_step_id}，觸發 Step 喚醒。")
                
                # 簡單取字串表示結果或摘要
                summary = str(result) if result is not None else f"{func.__name__} 完成"
                resume_step_execution.delay(callback_step_id, summary)
            except Exception as e:
                logger.error(f"觸發 callback_step_id={callback_step_id} 失敗: {e}")
                
        return result
    return wrapper
