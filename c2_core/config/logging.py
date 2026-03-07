import logging
import time
import functools
import asyncio
from typing import Callable, Optional, TypeVar, ParamSpec, Any
from asgiref.sync import sync_to_async

P = ParamSpec("P")
R = TypeVar("R")


def _smart_truncate(obj: Any, max_len: int = 200) -> Any:
    """
    智慧截斷：
    1. 如果是 Dict/List，遞迴進去剁掉太長的 Value。
    2. 如果是原生字串，直接剁了。
    3. 保留所有 Key，不刪除結構。
    """
    if isinstance(obj, dict):
        return {k: _smart_truncate(v, max_len) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_smart_truncate(i, max_len) for i in obj]
    elif isinstance(obj, str):
        if len(obj) > max_len:
            return obj[:max_len] + "... [TRUNCATED]"
        return obj
    return obj


def log_function_call(
    logger: Optional[logging.Logger] = None,
    max_val_len: int = 200,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    裝飾器：無縫支援同步/非同步。
    回傳值截斷邏輯：字串直接剁，JSON 剁 Value 留 Key。
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        _logger = logger or logging.getLogger(func.__module__)

        async def async_log_info(msg):
            await sync_to_async(lambda: _logger.info(msg), thread_sensitive=True)()

        async def async_log_exception(msg):
            await sync_to_async(lambda: _logger.exception(msg), thread_sensitive=True)()

        def format_output(result: Any) -> str:
            # 這是你要的精髓：
            # 如果是字串，_smart_truncate 會直接剁了它
            # 如果是 Dict/List，它會鑽進去剁裡面的內容
            processed = _smart_truncate(result, max_val_len)

            res_repr = repr(processed)
            # 最後防線：如果整串 Repr 還是長到靠北（例如 List 裡有一萬個元素）
            if len(res_repr) > 1500:
                return res_repr[:1500] + "... [OVERALL TOO LONG]"
            return res_repr

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            func_name = func.__qualname__
            # 參數也做一樣的處理，免得傳入大字串撐爆 Log
            clean_args = [_smart_truncate(arg, 100) for arg in args]
            clean_kwargs = {k: _smart_truncate(v, 100) for k, v in kwargs.items()}

            arg_str = ", ".join(
                [repr(a) for a in clean_args]
                + [f"{k}={repr(v)}" for k, v in clean_kwargs.items()]
            )
            await async_log_info(f"📞 [ASYNC CALL] {func_name}({arg_str})")

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                exec_time = time.perf_counter() - start_time
                await async_log_info(
                    f"✅ [SUCCESS] {func_name} ({exec_time:.4f}s) -> {format_output(result)}"
                )
                return result
            except Exception as e:
                exec_time = time.perf_counter() - start_time
                await async_log_exception(
                    f"❌ [FAILED] {func_name} ({exec_time:.4f}s) -> Error: {e}"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            func_name = func.__qualname__
            clean_args = [_smart_truncate(arg, 100) for arg in args]
            clean_kwargs = {k: _smart_truncate(v, 100) for k, v in kwargs.items()}

            arg_str = ", ".join(
                [repr(a) for a in clean_args]
                + [f"{k}={repr(v)}" for k, v in clean_kwargs.items()]
            )
            _logger.info(f"📞 [CALL] {func_name}({arg_str})")

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                exec_time = time.perf_counter() - start_time
                _logger.info(
                    f"✅ [SUCCESS] {func_name} ({exec_time:.4f}s) -> {format_output(result)}"
                )
                return result
            except Exception as e:
                exec_time = time.perf_counter() - start_time
                _logger.exception(
                    f"❌ [FAILED] {func_name} ({exec_time:.4f}s) -> Error: {e}"
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class LogConfig:
    @classmethod
    def setup_enhanced_logging(cls):
        # 這裡什麼都不做，因為 settings.py 已經做完了
        pass
