"""
apps/analyze_ai/tasks/ip.py

IP AI 分析 Celery 任務。

【重構說明】
批次執行邏輯（狀態標記 → GraphQL 取資料 → Prompt 注入 → AI 開火 → 存檔）已
統一提取至 `common._execute_ai_batch()`，本檔案只保留 Celery task 的宣告與調度。
"""

from typing import List

from celery import shared_task
from django.db import transaction

from apps.core.models import IPAIAnalysis
from c2_core.config.logging import log_function_call

from .common import _execute_ai_batch, logger

from typing import Optional
@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_ips(self, ip_ids: List[int], overview_id: Optional[int] = None, step_id: Optional[int] = None):
    """【總司令部 - IP 分析啟動】為指定 IP 批量初始化分析記錄並派發批次任務。"""
    logger.info(f"Task {self.request.id}: 收到 {len(ip_ids)} 個 IP 的 AI 分析請求。")
    with transaction.atomic():
        IPAIAnalysis.objects.bulk_create(
            [IPAIAnalysis(ip_id=ip_id, status="PENDING", overview_id=overview_id, triggered_by_step_id=step_id) for ip_id in ip_ids]
        )
    perform_ai_analysis_for_ip_batch.delay(ip_ids)
    return f"已成功為 {len(ip_ids)} 個 IP 派發單個分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_ip_batch(self, ip_ids: List[int]):
    """
    【作戰單元 - IP 批次分析】

    實際的 AI 分析執行由通用工廠函式 `_execute_ai_batch` 處理。
    本 Task 作為 Celery 入口點，確保 Task 名稱對外公開不變。
    """
    _execute_ai_batch(asset_type="ip", asset_ids=ip_ids, task_self=self)
