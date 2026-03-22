"""
apps/analyze_ai/tasks/subdomains.py

子域名 AI 分析 Celery 任務。

【重構說明】
批次執行邏輯已統一提取至 `common._execute_ai_batch()`，
本檔案只保留 Celery task 的宣告與調度。
"""

from typing import List

from celery import shared_task
from django.db import transaction

from apps.core.models import SubdomainAIAnalysis
from c2_core.config.logging import log_function_call

from .common import _execute_ai_batch, logger

from typing import Optional
@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_subdomains(self, subdomain_ids: List[int], overview_id: Optional[int] = None, step_id: Optional[int] = None):
    """
    【AI 指揮調度 - 子域名分析啟動】
    """
    logger.info(
        f"Task {self.request.id}: 收到 {len(subdomain_ids)} 個子域名的 AI 分析請求。"
    )
    with transaction.atomic():
        SubdomainAIAnalysis.objects.bulk_create(
            [
                SubdomainAIAnalysis(subdomain_id=sid, status="PENDING", overview_id=overview_id, triggered_by_step_id=step_id)
                for sid in subdomain_ids
            ]
        )
    perform_ai_analysis_for_subdomain_batch.delay(subdomain_ids)
    return f"已成功為 {len(subdomain_ids)} 個子域名派發分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_subdomain_batch(self, subdomain_ids: List[int]):
    """
    【AI 作戰單位 - 子域名批次數據分析】

    實際的 AI 分析執行由通用工廠函式 `_execute_ai_batch` 處理。
    本 Task 作為 Celery 入口點，確保 Task 名稱對外公開不變。
    """
    _execute_ai_batch(
        asset_type="subdomain", asset_ids=subdomain_ids, task_self=self
    )
