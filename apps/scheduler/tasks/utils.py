import logging
from django.db.models import Q
from apps.core.models import URLResult

logger = logging.getLogger(__name__)


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
            # 查找是否存在 ai_analysis__status='COMPLETED' 的記錄
            if (
                URLResult.objects.filter(query, ai_analysis__status="COMPLETED")
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
                    URLResult.objects.filter(query, ai_analysis__status="COMPLETED")
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
