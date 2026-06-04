import logging
import asyncio
from typing import Optional
from celery import shared_task
from django.utils import timezone
from apps.core.models import CVEIntelligence, TechStackCVEMapping
from apps.scanners.cve_intelligence.clients import CISAKEVClient
from apps.scanners.cve_intelligence.services.cve_enrichment import CVEEnrichmentService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def sync_cisa_kev_database(self, callback_step_id: Optional[int] = None):
    """
    每日同步 CISA KEV (Known Exploited Vulnerabilities) 目錄

    工作流程：
    1. 抓取 CISA KEV 目錄
    2. 更新本地 CVEIntelligence 記錄的 KEV 狀態
    3. 對於本地不存在的 KEV CVE，觸發 NVD 查詢補充詳情
    4. 檢查是否有新的 KEV CVE 影響現有的 TechStack

    Args:
        callback_step_id: Step ID for callback
    """
    logger.info("Starting CISA KEV database sync")

    # 抓取 CISA KEV 目錄
    async def fetch_kev():
        async with CISAKEVClient() as kev_client:
            return await kev_client.fetch_kev_catalog()

    kev_catalog = asyncio.run(fetch_kev())

    if not kev_catalog:
        logger.error("Failed to fetch CISA KEV catalog")
        return {"status": "failed", "reason": "Failed to fetch KEV catalog"}

    logger.info(f"Fetched {len(kev_catalog)} CVEs from CISA KEV catalog")

    # 統計
    updated_count = 0
    new_kev_count = 0
    missing_cve_ids = []

    # 更新現有的 CVEIntelligence 記錄
    for cve_id, kev_data in kev_catalog.items():
        try:
            cve_intel = CVEIntelligence.objects.get(cve_id=cve_id)

            # 更新 KEV 狀態
            if not cve_intel.cisa_kev:
                cve_intel.cisa_kev = True
                cve_intel.exploited_in_wild = True

                # 更新 data_sources
                if not cve_intel.data_sources:
                    cve_intel.data_sources = {}
                cve_intel.data_sources["cisa_kev"] = kev_data

                cve_intel.save(update_fields=["cisa_kev", "exploited_in_wild", "data_sources"])
                updated_count += 1
                logger.info(f"Updated KEV status for {cve_id}")

        except CVEIntelligence.DoesNotExist:
            # 本地不存在此 CVE，記錄下來稍後查詢
            missing_cve_ids.append(cve_id)
            new_kev_count += 1

    logger.info(f"Updated {updated_count} existing CVEs with KEV status")

    # 對於缺失的 KEV CVE，從 NVD 查詢並建立記錄
    if missing_cve_ids:
        logger.info(f"Fetching {len(missing_cve_ids)} missing KEV CVEs from NVD")

        service = CVEEnrichmentService()
        # 批次查詢（限制數量避免速率限制）
        batch_size = 50
        for i in range(0, len(missing_cve_ids), batch_size):
            batch = missing_cve_ids[i:i + batch_size]
            cve_intel_map = asyncio.run(service.enrich_cves_batch(batch))

            # 更新 KEV 狀態
            for cve_id in batch:
                cve_intel = cve_intel_map.get(cve_id)
                if cve_intel:
                    cve_intel.cisa_kev = True
                    cve_intel.exploited_in_wild = True

                    if not cve_intel.data_sources:
                        cve_intel.data_sources = {}
                    cve_intel.data_sources["cisa_kev"] = kev_catalog.get(cve_id, {})

                    cve_intel.save(update_fields=["cisa_kev", "exploited_in_wild", "data_sources"])
                    logger.info(f"Created new CVE {cve_id} from KEV catalog")

    # 檢查是否有新的 KEV CVE 影響現有的 TechStack
    new_mappings = _check_kev_impact_on_techstacks(list(kev_catalog.keys()))

    result = {
        "status": "success",
        "total_kev": len(kev_catalog),
        "updated_existing": updated_count,
        "new_kev_cves": new_kev_count,
        "new_techstack_mappings": new_mappings,
        "synced_at": timezone.now().isoformat()
    }

    logger.info(f"CISA KEV sync completed: {result}")
    return result


def _check_kev_impact_on_techstacks(kev_cve_ids: list) -> int:
    """
    檢查 KEV CVE 是否影響現有的 TechStack

    Args:
        kev_cve_ids: KEV CVE ID 清單

    Returns:
        新建立的 TechStackCVEMapping 數量
    """
    new_mappings = 0

    # 查詢這些 KEV CVE 的 CVEIntelligence 記錄
    kev_cves = CVEIntelligence.objects.filter(
        cve_id__in=kev_cve_ids,
        cisa_kev=True
    )

    for cve_intel in kev_cves:
        # 檢查是否有 TechStack 尚未關聯此 CVE
        # 這裡使用簡單的邏輯，實際可以更複雜
        existing_mappings = TechStackCVEMapping.objects.filter(
            cve_intelligence=cve_intel
        ).values_list("techstack_id", flat=True)

        # 查詢可能受影響但尚未關聯的 TechStack
        # （這裡簡化處理，實際應該使用 version_matcher）
        from apps.core.models import TechStack

        for product in cve_intel.affected_products:
            product_name = product.get("product", "")
            if not product_name:
                continue

            # 查詢名稱匹配的 TechStack
            matching_techstacks = TechStack.objects.filter(
                name__icontains=product_name
            ).exclude(id__in=existing_mappings)

            for techstack in matching_techstacks[:10]:  # 限制數量
                # 建立 TechStackCVEMapping
                mapping, created = TechStackCVEMapping.objects.get_or_create(
                    techstack=techstack,
                    cve_intelligence=cve_intel,
                    defaults={
                        "version_match": "unknown",
                        "confidence": 0.7,
                        "notified": False,
                    }
                )

                if created:
                    new_mappings += 1
                    logger.warning(
                        f"🚨 KEV Alert: {techstack.target.name} - {techstack.name} "
                        f"vulnerable to {cve_intel.cve_id} (CISA KEV)"
                    )

    return new_mappings
