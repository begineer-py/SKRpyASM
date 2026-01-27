# --- 操，用回你原本的輔助函數模式，清晰明瞭 ---
from typing import Union
from apps.core.models import Target
from ninja.errors import HttpError


async def get_target_object(target_identifier: Union[int, str]) -> Target:
    """
    一個獨立的、可 await 的輔助函數，根據 ID 或 domain 查找 Target。
    找不到就拋 HttpError。
    """
    try:
        if isinstance(target_identifier, int) or str(target_identifier).isdigit():
            target = await Target.objects.aget(id=int(target_identifier))
        else:
            target = await Target.objects.aget(domain=target_identifier)
        return target
    except Target.DoesNotExist:
        raise HttpError(404, f"Target '{target_identifier}' not found.")
