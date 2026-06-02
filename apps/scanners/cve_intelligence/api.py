import logging
import asyncio
from ninja import Router
from ninja.errors import HttpError
from typing import List
from concurrent.futures import ThreadPoolExecutor
import threading
from django.db.models import Q

from apps.core.models import CVEIntelligence, Vulnerability, Target, TechStackCVEMapping
from apps.core.schemas import SuccessSendToAISchema, ErrorSchema
from .schemas import (
    CVEQuerySchema,
    CVESearchSchema,
    CVESearchByTagsSchema,
    EnrichVulnerabilitiesSchema,
    SyncTechStackSchema,
    SyncKEVSchema,
    CVEIntelligenceOut,
    CVESearchResultOut,
    TechStackCVEReportOut,
    TechStackCVEMappingOut,
)
from .services.cve_enrichment import CVEEnrichmentService
from .services.version_matcher import VersionMatcher
from .tasks.enrichment_tasks import enrich_vulnerabilities_batch, sync_techstack_cves
from .tasks.scheduled_sync import sync_cisa_kev_database

router = Router()
logger = logging.getLogger(__name__)


def run_async_in_thread(coro):
    """在新線程中運行異步代碼"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result()


# =============================================================================
# 同步端點（直接返回結果）
# =============================================================================

@router.post("/query", response={200: CVEIntelligenceOut, 404: ErrorSchema})
def query_cve(request, payload: CVEQuerySchema):
    """
    查詢特定 CVE 的詳細情報

    使用三層快取策略：PostgreSQL → Redis → External API
    """
    cve_id = payload.cve_id.upper()
    logger.info(f"API: 查詢 CVE {cve_id}")

    try:
        # 使用豐富化服務（三層快取策略）
        service = CVEEnrichmentService()
        cve_intel = run_async_in_thread(
            service.enrich_cve(cve_id, use_external=payload.use_nvd)
        )

        if not cve_intel:
            not_found_msg = (
                f"CVE {cve_id} 不在本地資料庫中" if not payload.use_nvd
                else f"CVE {cve_id} 未找到"
            )
            raise HttpError(404, not_found_msg)

        return 200, cve_intel

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"查詢 CVE {cve_id} 時發生錯誤: {e}", exc_info=True)
        raise HttpError(500, f"查詢 CVE 時發生錯誤: {str(e)}")


@router.post("/search", response={200: CVESearchResultOut, 400: ErrorSchema})
def search_cves(request, payload: CVESearchSchema):
    """
    根據技術名稱和版本搜尋相關 CVE

    支援嚴重性過濾和「僅已利用」模式
    """
    logger.info(f"API: 搜尋 CVE - {payload.tech_name} {payload.version or 'all versions'}")

    try:
        # 查詢本地資料庫
        query = CVEIntelligence.objects.all()

        # 關鍵字過濾：CPE 結構化資料優先（GIN index），fallback 到描述文字搜索
        if payload.tech_name:
            tech_lower = payload.tech_name.lower()
            cve_filter = (
                Q(affected_products__contains=[{"product": tech_lower}]) |
                Q(affected_products__contains=[{"vendor": tech_lower}]) |
                Q(description__icontains=payload.tech_name)
            )
            query = query.filter(cve_filter)

        # 嚴重性過濾：使用 JSONB 路徑查詢 data_sources.nvd.severity（GIN index 可命中 @> 操作）
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        min_level = severity_order.get(payload.severity_min.upper(), 2)
        severity_filter = [k for k, v in severity_order.items() if v >= min_level]
        query = query.filter(data_sources__nvd__severity__in=severity_filter)

        # CVSS 最低分數過濾（JSONB 路徑：data_sources.nvd.cvss_score）
        if payload.min_cvss is not None:
            query = query.filter(data_sources__nvd__cvss_score__gte=payload.min_cvss)

        # EPSS 最低分數過濾（JSONB 路徑：data_sources.epss.epss_score）
        if payload.min_epss is not None:
            query = query.filter(data_sources__epss__epss_score__gte=payload.min_epss)

        # 已利用過濾
        if payload.exploited_only:
            query = query.filter(Q(cisa_kev=True) | Q(exploit_available=True))

        # 發布日期過濾
        if payload.pub_start_date:
            query = query.filter(published_date__gte=payload.pub_start_date)
        if payload.pub_end_date:
            query = query.filter(published_date__lte=payload.pub_end_date)

        # 排序
        query = query.order_by("-cvss_score", "-epss_score")

        limit = min(payload.limit, 100)

        # 版本匹配：先用 JSONB 篩出所有 vendor/product 相關 CVE，再記憶體比對，最後截斷
        if payload.version:
            matcher = VersionMatcher()
            all_cves = list(query)  # 不限筆數，由前置 JSONB 過濾控制規模
            matched_cves = []

            for cve in all_cves:
                is_match, match_type, confidence = matcher.match_cpe_to_techstack(
                    payload.tech_name, payload.version, cve.affected_products
                )
                if is_match and confidence >= 0.5:
                    matched_cves.append(cve)

            cves = matched_cves[:limit]
            total = len(matched_cves)
        else:
            cves = list(query[:limit])
            total = query.count()

        return 200, CVESearchResultOut(total=total, cves=cves)

    except Exception as e:
        logger.error(f"搜尋 CVE 時發生錯誤: {e}")
        raise HttpError(500, f"搜尋 CVE 時發生錯誤: {str(e)}")


@router.post("/search_by_tags", response={200: CVESearchResultOut, 400: ErrorSchema})
def search_cves_by_tags(request, payload: CVESearchByTagsSchema):
    """
    根據 tags 搜尋相關技術的 CVE

    支援多個 tags 的 OR 查詢，例如：["apache", "rce", "authentication"]
    會搜尋描述中包含任一 tag 的 CVE
    """
    logger.info(f"API: 根據 tags 搜尋 CVE - {payload.tags}")

    try:
        from django.db.models import Q

        if not payload.tags:
            raise HttpError(400, "至少需要提供一個 tag")

        # 查詢本地資料庫
        query = CVEIntelligence.objects.all()

        # Tags 過濾（OR 查詢）
        tag_query = Q()
        for tag in payload.tags:
            tag_query |= Q(description__icontains=tag) | Q(cve_id__icontains=tag)
        query = query.filter(tag_query)

        # 嚴重性過濾
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        min_level = severity_order.get(payload.severity_min.upper(), 2)
        severity_filter = [k for k, v in severity_order.items() if v >= min_level]
        query = query.filter(severity__in=severity_filter)

        # 已利用過濾
        if payload.exploited_only:
            query = query.filter(Q(cisa_kev=True) | Q(exploit_available=True))

        # 排序：優先顯示 CISA KEV，然後按 CVSS 分數
        query = query.order_by("-cisa_kev", "-cvss_score", "-epss_score")

        # 限制結果數量
        limit = min(payload.limit, 100)  # 最多 100 個結果
        cves = list(query[:limit])
        total = query.count()

        logger.info(f"找到 {total} 個匹配的 CVE，返回前 {len(cves)} 個")

        return 200, CVESearchResultOut(total=total, cves=cves)

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"根據 tags 搜尋 CVE 時發生錯誤: {e}")
        raise HttpError(500, f"搜尋 CVE 時發生錯誤: {str(e)}")


@router.get("/techstack_report/{target_id}", response={200: TechStackCVEReportOut, 404: ErrorSchema})
def get_techstack_cve_report(request, target_id: int):
    """
    生成目標的技術棧 CVE 風險報告

    分析目標所有已識別的技術棧，並列出相關的高危 CVE
    """
    logger.info(f"API: 生成 Target {target_id} 的技術棧 CVE 報告")

    try:
        # 驗證 Target 存在
        if not Target.objects.filter(id=target_id).exists():
            raise HttpError(404, f"Target {target_id} 不存在")

        # 查詢所有 TechStackCVEMapping
        mappings = TechStackCVEMapping.objects.filter(
            techstack__target_id=target_id
        ).select_related("techstack", "cve_intelligence").order_by(
            "-cve_intelligence__cvss_score"
        )

        mappings_list = list(mappings)

        if not mappings_list:
            return 200, TechStackCVEReportOut(
                target_id=target_id,
                total_cves=0,
                critical_count=0,
                high_count=0,
                kev_count=0,
                top_cves=[]
            )

        # 統計
        total_cves = len(mappings_list)
        critical_count = sum(1 for m in mappings_list if m.cve_intelligence.severity == "CRITICAL")
        high_count = sum(1 for m in mappings_list if m.cve_intelligence.severity == "HIGH")
        kev_count = sum(1 for m in mappings_list if m.cve_intelligence.cisa_kev)

        # 前 10 個高危 CVE
        top_mappings = mappings_list[:10]
        top_cves = [
            TechStackCVEMappingOut(
                cve_id=m.cve_intelligence.cve_id,
                severity=m.cve_intelligence.severity,
                cvss_score=m.cve_intelligence.cvss_score,
                cisa_kev=m.cve_intelligence.cisa_kev,
                exploit_available=m.cve_intelligence.exploit_available,
                techstack_name=m.techstack.name,
                techstack_version=m.techstack.version,
                confidence=m.confidence
            )
            for m in top_mappings
        ]

        return 200, TechStackCVEReportOut(
            target_id=target_id,
            total_cves=total_cves,
            critical_count=critical_count,
            high_count=high_count,
            kev_count=kev_count,
            top_cves=top_cves
        )

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"生成技術棧 CVE 報告時發生錯誤: {e}")
        raise HttpError(500, f"生成報告時發生錯誤: {str(e)}")


# =============================================================================
# 非同步端點（派發 Celery 任務）
# =============================================================================

@router.post("/enrich_vulnerabilities", response={202: SuccessSendToAISchema, 404: ErrorSchema})
def enrich_vulnerabilities(request, payload: EnrichVulnerabilitiesSchema):
    """
    批次豐富化 Vulnerability 記錄

    從 template_id 提取 CVE ID，查詢本地資料庫優先，僅對缺失的 CVE 發起 API 請求
    """
    logger.info(f"API: 批次豐富化 Vulnerability {payload.vulnerability_ids}")

    try:
        # 驗證 Vulnerability IDs 存在
        valid_ids = list(Vulnerability.objects.filter(id__in=payload.vulnerability_ids).values_list('id', flat=True))

        if not valid_ids:
            raise HttpError(404, "未找到有效的 Vulnerability ID")

        # 派發 Celery 任務
        enrich_vulnerabilities_batch.delay(
            valid_ids,
            callback_step_id=payload.callback_step_id
        )

        return 202, SuccessSendToAISchema(
            detail=f"成功派發 {len(valid_ids)} 個 Vulnerability 的豐富化任務"
        )

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"派發豐富化任務時發生錯誤: {e}")
        raise HttpError(500, f"派發任務時發生錯誤: {str(e)}")


@router.post("/sync_techstack", response={202: SuccessSendToAISchema, 404: ErrorSchema})
def sync_techstack(request, payload: SyncTechStackSchema):
    """
    同步目標的 TechStack CVE

    對應 TechStack 到相關 CVE，建立 TechStackCVEMapping 記錄
    """
    logger.info(f"API: 同步 Target {payload.target_id} 的 TechStack CVE")

    try:
        # 驗證 Target 存在
        if not Target.objects.filter(id=payload.target_id).exists():
            raise HttpError(404, f"Target {payload.target_id} 不存在")

        # 派發 Celery 任務
        sync_techstack_cves.delay(
            payload.target_id,
            callback_step_id=payload.callback_step_id
        )

        return 202, SuccessSendToAISchema(
            detail=f"成功派發 Target {payload.target_id} 的 TechStack CVE 同步任務"
        )

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"派發 TechStack 同步任務時發生錯誤: {e}")
        raise HttpError(500, f"派發任務時發生錯誤: {str(e)}")


@router.post("/sync_kev", response={202: SuccessSendToAISchema})
def sync_kev(request, payload: SyncKEVSchema):
    """
    手動觸發 CISA KEV 同步

    抓取最新的 CISA KEV 目錄，更新 CVEIntelligence 記錄
    """
    logger.info("API: 手動觸發 CISA KEV 同步")

    try:
        # 派發 Celery 任務
        sync_cisa_kev_database.delay(callback_step_id=payload.callback_step_id)

        return 202, SuccessSendToAISchema(
            detail="成功派發 CISA KEV 同步任務"
        )

    except Exception as e:
        logger.error(f"派發 KEV 同步任務時發生錯誤: {e}")
        raise HttpError(500, f"派發任務時發生錯誤: {str(e)}")
