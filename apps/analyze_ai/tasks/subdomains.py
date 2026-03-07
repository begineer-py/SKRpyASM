import json
import random
from typing import List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from c2_core.config.config import Config
from c2_core.config.logging import log_function_call
from apps.core.models import SubdomainAIAnalysis

from .common import (
    _fire_at_target,
    fetch_subdomain_data_for_batch,
    load_subdomain_prompt_template,
    logger,
)


@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_subdomains(self, subdomain_ids: List[int]):
    """【總司令部 - 子域名分部】"""
    logger.info(
        f"Task {self.request.id}: 收到 {len(subdomain_ids)} 個子域名的 AI 分析請求。"
    )

    with transaction.atomic():
        # 改為直接 create，因為允許歷史記錄
        SubdomainAIAnalysis.objects.bulk_create(
            [SubdomainAIAnalysis(subdomain_id=sid, status="PENDING") for sid in subdomain_ids]
        )

    perform_ai_analysis_for_subdomain_batch.delay(subdomain_ids)
    return f"已成功為 {len(subdomain_ids)} 個子域名派發分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_subdomain_batch(self, subdomain_ids: List[int]):
    """
    【作戰單元 - 子域名分析】
    """
    logger.info(
        f"Task {self.request.id}: 開始處理子域名批次，數量: {len(subdomain_ids)}。"
    )

    with transaction.atomic():
        analysis_qs = SubdomainAIAnalysis.objects.filter(
            subdomain_id__in=subdomain_ids, status="PENDING"
        )
        analysis_qs.update(status="RUNNING")
        analysis_records = list(analysis_qs.filter(status="RUNNING"))

    if not analysis_records:
        logger.warning("沒有找到處於 PENDING 狀態的子域名分析記錄，任務結束。")
        return

    try:
        # 1. 獲取數據
        data_payload = fetch_subdomain_data_for_batch(subdomain_ids)
        if not data_payload["list_of_assets"]:
            logger.warning("未能提取到任何子域名數據，任務終止。")
            SubdomainAIAnalysis.objects.filter(id__in=[r.id for r in analysis_records]).update(
                status="FAILED",
                error_message="Failed to fetch asset data via GraphQL.",
            )
            return

        # 2. 準備彈藥
        template = load_subdomain_prompt_template()
        final_prompt = template.replace("{$data}", json.dumps(data_payload, indent=2))

        # 3. 火力覆蓋
        available_targets = list(Config.AI_SERVICE_URLS.items())
        random.shuffle(available_targets)

        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"正在嘗試使用火力點: {api_name} 分析子域名...")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception

        if ai_response is None:
            error_msg = f"所有 AI 節點均失敗。最後錯誤: {last_exception}"
            logger.error(error_msg)
            SubdomainAIAnalysis.objects.filter(id__in=[r.id for r in analysis_records]).update(
                status="FAILED", error_message=str(last_exception)
            )
            self.retry(exc=last_exception)
            return

        # 4. 戰果存檔
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"收到 {len(analysis_results)} 條 AI 分析結果。")

        analysis_map = {record.subdomain_id: record for record in analysis_records}
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)

            if record:
                record.summary = result.get("summary")
                record.inferred_purpose = result.get("inferred_purpose")
                record.business_impact = result.get("business_impact")
                record.tech_stack_summary = result.get("tech_stack_summary")
                record.risk_score = result.get("risk_score")
                record.potential_vulnerabilities = result.get("potential_vulnerabilities")
                record.recommended_actions = result.get("recommended_actions")
                record.command_actions = result.get("command_actions")
                record.raw_response = result
                record.status = "COMPLETED"
                record.completed_at = timezone.now()
                records_to_update.append(record)
            else:
                logger.warning(
                    f"AI 返回了未知的 Subdomain ID: {correlation_id}，忽略。"
                )

        if records_to_update:
            SubdomainAIAnalysis.objects.bulk_update(
                records_to_update,
                [
                    "summary",
                    "inferred_purpose",
                    "business_impact",
                    "tech_stack_summary",
                    "risk_score",
                    "potential_vulnerabilities",
                    "recommended_actions",
                    "command_actions",
                    "raw_response",
                    "status",
                    "completed_at",
                ],
            )
            logger.info(f"成功更新 {len(records_to_update)} 條子域名分析記錄。")

    except Exception as e:
        error_msg = f"子域名批次處理中發生致命錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        self.retry(exc=e)
