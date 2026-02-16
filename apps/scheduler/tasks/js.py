import logging
import requests
from celery import shared_task
from django.conf import settings

from apps.core.models import JavaScriptFile, ExtractedJS

logger = logging.getLogger(__name__)


@shared_task(name="scheduler.tasks.trigger_scan_js")
def trigger_scan_js(batch_size: int = 10):
    """
    定時任務：找出還沒分析過的 JS，透過 API 丟給 AI 掃描
    """
    logger.info("定時任務啟動：自動搜刮未分析 JS")

    # 1. 抓取未分析的外部 JS
    external_targets = JavaScriptFile.objects.filter(is_analyzed=False).values_list(
        "id", flat=True
    )[
        :batch_size
    ]  # 每次限額 100 個，避免 API 瞬間爆炸

    # 2. 抓取未分析的內嵌 JS
    inline_targets = ExtractedJS.objects.filter(is_analyzed=False).values_list(
        "id", flat=True
    )[:batch_size]

    # 建立一個 Session，發送多次請求時效能比較好
    session = requests.Session()

    # 處理外部 JS
    for target_id in external_targets:
        try:
            payload = {"id": target_id, "type": "external"}
            resp = session.post(f"{settings.JS_AI_SCAN_URL}", json=payload, timeout=5)
            if resp.status_code != 200:
                logger.warning(f"API 拒絕外部 JS (ID: {target_id}): {resp.text}")
        except Exception as e:
            logger.error(f"連線 API 失敗 (External ID: {target_id}): {e}")

    # 處理內嵌 JS
    for target_id in inline_targets:
        try:
            payload = {"id": target_id, "type": "inline"}
            resp = session.post(f"{settings.JS_AI_SCAN_URL}", json=payload, timeout=5)
            if resp.status_code != 200:
                logger.warning(f"API 拒絕內嵌 JS (ID: {target_id}): {resp.text}")
        except Exception as e:
            logger.error(f"連線 API 失敗 (Inline ID: {target_id}): {e}")

    logger.info("定時任務完成：所有待掃描任務已提交")
