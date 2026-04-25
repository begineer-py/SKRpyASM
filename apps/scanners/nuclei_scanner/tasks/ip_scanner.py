"""
apps/nuclei_scanner/tasks/ip_scanner.py

IP 的 Nuclei 掃描任務。

【重構說明】
所有命令準備與執行邏輯已統一提取至 `asset_configs.py` 與 `executor._execute_nuclei_batch()`。
本檔案只保留 Celery task 宣告。
"""

import logging
from typing import List, Optional
from celery import shared_task
from c2_core.config.logging import log_function_call

from .executor import _execute_nuclei_batch
from apps.core.utils import with_auto_callback

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
@with_auto_callback
def perform_nuclei_scans_for_ip_batch(
    self, ip_ids: List[int], custom_tags: Optional[List[str]] = None, callback_step_id: Optional[int] = None
):
    """IP 掃描：側重基礎設施與開放服務"""
    return _execute_nuclei_batch("ip", ip_ids, custom_tags, task_self=self, callback_step_id=callback_step_id)
