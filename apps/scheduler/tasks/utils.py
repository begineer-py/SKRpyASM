import asyncio
import logging
from django.db.models import Q
from apps.core.models import URLResult
import httpx

logger = logging.getLogger(__name__)


async def async_post_batch(url: str, payloads: list, timeout: int = 5) -> int:
    """
    並發 POST 到 url，每個 payload 為獨立請求。
    回傳 2xx 成功數量。每個請求獨立記錄錯誤，不拋出例外。
    """
    if not payloads:
        return 0
    async with httpx.AsyncClient(timeout=timeout) as client:
        results = await asyncio.gather(
            *[client.post(url, json=p) for p in payloads],
            return_exceptions=True,
        )
    success = 0
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"async_post_batch: 連線失敗 (index {i}, url={url}): {r}")
        elif isinstance(r, httpx.Response) and 200 <= r.status_code < 300:
            success += 1
        else:
            status = getattr(r, "status_code", "?")
            logger.warning(f"async_post_batch: 非 2xx (index {i}, status={status}, url={url})")
    return success



def is_content_already_analyzed(url_obj, analysis_type="AI"):
    """
    檢查該 URL 的【內容】或【最終跳轉】在【全局歷史】中是否已經被分析過。
    analysis_type: "AI" 或 "NUCLEI"
    """
    # 1. 檢查 Hash (內容指紋)
    if url_obj.raw_response_hash:
        query = Q(raw_response_hash=url_obj.raw_response_hash)

        # 根據類型構造查詢：查找【是否有任何】具有相同 Hash 的 URL 已經完成了分析
        if analysis_type == "AI":
            # 查找是否存在 ai_analyses__status='COMPLETED' 的記錄
            if (
                URLResult.objects.filter(query, ai_analyses__status="COMPLETED")
                .exclude(id=url_obj.id)
                .exists()
            ):
                return True
        elif analysis_type == "NUCLEI":
            # 查找是否存在 nuclei_scans__status='COMPLETED' 的記錄
            if (
                URLResult.objects.filter(query, nuclei_scans__status="COMPLETED")
                .exclude(id=url_obj.id)
                .exists()
            ):
                return True

    # 2. 檢查 Final URL (跳轉終點)
    if url_obj.final_url:
        # 如果 Final URL 和當前 URL 不同，才需要去查
        if url_obj.final_url != url_obj.url:
            query = Q(final_url=url_obj.final_url) | Q(url=url_obj.final_url)

            if analysis_type == "AI":
                if (
                    URLResult.objects.filter(query, ai_analyses__status="COMPLETED")
                    .exclude(id=url_obj.id)
                    .exists()
                ):
                    return True
            elif analysis_type == "NUCLEI":
                if (
                    URLResult.objects.filter(query, nuclei_scans__status="COMPLETED")
                    .exclude(id=url_obj.id)
                    .exists()
                ):
                    return True

    return False
