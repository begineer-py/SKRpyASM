"""
apps/subfinder/tasks/amass_brute.py

Amass 掃描任務。

【重構說明】
所有命令準備與執行邏輯已統一提取至 `enum_configs.py` 與 `common._run_subdomain_enum()`。
本檔案只保留 Celery task 宣告。
"""

import logging
from celery import shared_task
from c2_core.config.logging import log_function_call
from .common import _run_subdomain_enum

logger = logging.getLogger(__name__)


from typing import Optional

@shared_task(bind=True, ignore_result=True)
@log_function_call()
def start_amass_scan(self, scan_id: int = None, seed_id: int = None, callback_step_id: Optional[int] = None):
    """啟動 Amass 掃描任務 (重裝坦克)。"""
    _run_subdomain_enum("amass", scan_id, callback_step_id=callback_step_id)
