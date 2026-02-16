import json
import random
from typing import List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from c2_core.config.config import Config
from c2_core.config.logging import log_function_call
from apps.core.models import IPAIAnalysis

from .common import (
    _fire_at_target,
    fetch_ip_data_for_batch,
    load_prompt_template,
    logger,
)


@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_ips(self, ip_ids: List[int]):
    """【總司令部】"""
    logger.info(f"Task {self.request.id}: 收到 {len(ip_ids)} 個 IP 的 AI 分析請求。")
    with transaction.atomic():
        IPAIAnalysis.objects.bulk_create(
            [IPAIAnalysis(ip_id=ip_id) for ip_id in ip_ids], ignore_conflicts=True
        )
    perform_ai_analysis_for_ip_batch.delay(ip_ids)
    return f"已成功為 {len(ip_ids)} 個 IP 派發單個分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_ip_batch(self, ip_ids: List[int]):
    """
    【作戰單元】使用重構後的火力系統處理批次。
    """
    logger.info(f"Task {self.request.id}: 開始處理批次，包含 {len(ip_ids)} 個 IP。")
    analysis_qs = IPAIAnalysis.objects.filter(ip_id__in=ip_ids)
    analysis_qs.update(status="RUNNING")

    try:
        # 1. 動態火力選擇
        available_targets = list(Config.AI_SERVICE_URLS.items())
        if not available_targets:
            logger.error("沒有配置任何動態 AI 服務 URL，任務無法執行。")
            analysis_qs.update(status="FAILED", error_message="No AI services configured.")
            return

        random.shuffle(available_targets)
        logger.info(
            f"火力陣地已準備就緒，可用目標: {[name for name, url in available_targets]}"
        )

        # 2. 提取情報 & 準備作戰指令
        data_payload = fetch_ip_data_for_batch(ip_ids)
        if not data_payload["list_of_assets"]:
            logger.warning("未能為此批次提取到任何情報，任務終止。")
            analysis_qs.update(status="FAILED", error_message="Failed to fetch asset data.")
            return

        template = load_prompt_template()
        final_prompt = template.replace("{$data}", json.dumps(data_payload, indent=2))

        # 3. 輪番開火
        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"正在嘗試使用火力點: {api_name} ({api_url})")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception
                logger.warning(f"火力點 {api_name} 未命中，正在切換到下一個...")

        if ai_response is None:
            error_msg = f"所有 AI 服務節點均無響應。最後錯誤: {last_exception}"
            logger.error(error_msg)
            analysis_qs.update(status="FAILED", error_message=str(last_exception))
            self.retry(exc=last_exception)
            return

        # 4. 戰果驗收與存檔
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"收到 {len(analysis_results)} 條 AI 分析結果。")

        if len(analysis_results) == 0:
            logger.warning("未能收到任何 AI 分析結果，任務終止。")
            analysis_qs.update(status="FAILED", error_message="No AI analysis results received.")
            logger.warning(f"{ai_response}")

        analysis_map = {record.ip_id: record for record in analysis_qs}
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)
            if record:
                record.summary = result.get("summary")
                record.inferred_purpose = result.get("inferred_purpose")
                record.risk_score = result.get("risk_score")
                record.port_analysis_summary = result.get("port_analysis_summary")
                record.potential_vulnerabilities = result.get("potential_vulnerabilities")
                record.recommended_actions = result.get("recommended_actions")
                record.command_actions = result.get("command_actions")
                record.raw_response = result
                record.status = "COMPLETED"
                record.completed_at = timezone.now()
                records_to_update.append(record)
            else:
                logger.warning(f"AI 返回了未知的 correlation_id: {correlation_id}，已忽略。")

        if records_to_update:
            IPAIAnalysis.objects.bulk_update(
                records_to_update,
                [
                    "summary",
                    "inferred_purpose",
                    "risk_score",
                    "port_analysis_summary",
                    "potential_vulnerabilities",
                    "recommended_actions",
                    "command_actions",
                    "raw_response",
                    "status",
                    "completed_at",
                ],
            )
            logger.info(f"成功更新 {len(records_to_update)} 條分析記錄。")

    except Exception as e:
        error_msg = f"批次處理中發生未知錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        self.retry(exc=e)
