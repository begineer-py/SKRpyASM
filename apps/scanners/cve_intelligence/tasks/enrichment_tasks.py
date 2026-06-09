import logging
from typing import List, Optional
from celery import shared_task
from django.utils import timezone
from apps.core.models import Vulnerability, CVEIntelligence, TechStack, TechStackCVEMapping
from apps.scanners.cve_intelligence.services.cve_enrichment import CVEEnrichmentService
from apps.scanners.cve_intelligence.services.version_matcher import VersionMatcher
import asyncio
import re

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enrich_vulnerabilities_batch(self, vulnerability_ids: List[int]):
    """
    批次豐富化 Vulnerability 記錄

    Args:
        vulnerability_ids: Vulnerability ID 清單
    """
    logger.info(f"Starting CVE enrichment for {len(vulnerability_ids)} vulnerabilities")

    # 查詢所有待豐富化的 Vulnerability
    vulnerabilities = Vulnerability.objects.filter(
        id__in=vulnerability_ids,
        enrichment_status="pending"
    )

    if not vulnerabilities.exists():
        logger.warning("No pending vulnerabilities found for enrichment")
        return {"enriched": 0, "failed": 0, "skipped": len(vulnerability_ids)}

    # 提取 CVE ID
    cve_ids = []
    vuln_cve_map = {}  # vulnerability_id -> cve_id

    for vuln in vulnerabilities:
        cve_id = _extract_cve_id_from_vulnerability(vuln)
        if cve_id:
            cve_ids.append(cve_id)
            vuln_cve_map[vuln.id] = cve_id

    if not cve_ids:
        logger.warning("No CVE IDs found in vulnerabilities")
        Vulnerability.objects.filter(id__in=vulnerability_ids).update(
            enrichment_status="no_cve",
            enrichment_attempted_at=timezone.now()
        )
        return {"enriched": 0, "failed": 0, "skipped": len(vulnerability_ids)}

    logger.info(f"Extracted {len(cve_ids)} unique CVE IDs: {cve_ids[:5]}...")

    # 批次豐富化 CVE（使用三層快取策略）
    service = CVEEnrichmentService()
    cve_intel_map = asyncio.run(service.enrich_cves_batch(cve_ids))

    # 更新 Vulnerability 記錄
    enriched_count = 0
    failed_count = 0

    for vuln in vulnerabilities:
        cve_id = vuln_cve_map.get(vuln.id)
        if not cve_id:
            vuln.enrichment_status = "no_cve"
            vuln.enrichment_attempted_at = timezone.now()
            vuln.save(update_fields=["enrichment_status", "enrichment_attempted_at"])
            continue

        cve_intel = cve_intel_map.get(cve_id)
        if cve_intel:
            vuln.cve_intelligence = cve_intel
            vuln.enrichment_status = "enriched"
            vuln.enrichment_attempted_at = timezone.now()
            vuln.save(update_fields=["cve_intelligence", "enrichment_status", "enrichment_attempted_at"])
            enriched_count += 1
            logger.debug(f"Enriched vulnerability {vuln.id} with CVE {cve_id}")
        else:
            vuln.enrichment_status = "failed"
            vuln.enrichment_attempted_at = timezone.now()
            vuln.save(update_fields=["enrichment_status", "enrichment_attempted_at"])
            failed_count += 1
            logger.warning(f"Failed to enrich vulnerability {vuln.id} with CVE {cve_id}")

    result = {
        "enriched": enriched_count,
        "failed": failed_count,
        "total": len(vulnerability_ids)
    }

    logger.info(f"CVE enrichment completed: {result}")
    return result


@shared_task(bind=True, max_retries=3)
def sync_techstack_cves(self, target_id: int):
    """
    同步目標的所有 TechStack 與最新 CVE 情報

    Args:
        target_id: Target ID
    """
    logger.info(f"Starting TechStack CVE sync for target {target_id}")

    # 查詢目標的所有 TechStack
    techstacks = TechStack.objects.filter(target_id=target_id)

    if not techstacks.exists():
        logger.warning(f"No TechStack found for target {target_id}")
        return {"mapped": 0, "total": 0}

    logger.info(f"Found {techstacks.count()} TechStack records for target {target_id}")

    mapped_count = 0
    matcher = VersionMatcher()

    for techstack in techstacks:
        tech_name = techstack.name
        tech_version = techstack.version or ""

        # 搜尋相關 CVE（優先使用本地資料庫）
        # 簡單的關鍵字匹配（可以改進為更智慧的匹配）
        keywords = _extract_keywords_from_tech_name(tech_name)

        for keyword in keywords:
            # 查詢本地 CVEIntelligence 記錄
            cve_candidates = CVEIntelligence.objects.filter(
                description__icontains=keyword
            )[:50]  # 限制數量避免過多

            for cve_intel in cve_candidates:
                # 使用 version_matcher 判斷是否匹配
                is_match, match_type, confidence = matcher.match_cpe_to_techstack(
                    tech_name,
                    tech_version,
                    cve_intel.affected_products
                )

                if is_match and confidence >= 0.5:
                    # 建立或更新 TechStackCVEMapping
                    mapping, created = TechStackCVEMapping.objects.get_or_create(
                        techstack=techstack,
                        cve_intelligence=cve_intel,
                        defaults={
                            "version_match": match_type,
                            "confidence": confidence,
                        }
                    )

                    if created:
                        mapped_count += 1
                        logger.info(
                            f"Mapped {tech_name} {tech_version} to {cve_intel.cve_id} "
                            f"(confidence: {confidence:.2f})"
                        )

    result = {
        "mapped": mapped_count,
        "total": techstacks.count()
    }

    logger.info(f"TechStack CVE sync completed: {result}")
    return result


def _extract_cve_id_from_vulnerability(vuln: Vulnerability) -> Optional[str]:
    """
    從 Vulnerability 記錄中提取 CVE ID

    優先順序：
    1. template_id (例如 "CVE-2024-12345")
    2. name (例如 "Apache Struts RCE (CVE-2024-12345)")
    3. extracted_results
    """
    # 從 template_id 提取
    if vuln.template_id:
        match = re.search(r'CVE-\d{4}-\d{4,}', vuln.template_id, re.IGNORECASE)
        if match:
            return match.group(0).upper()

    # 從 name 提取
    if vuln.name:
        match = re.search(r'CVE-\d{4}-\d{4,}', vuln.name, re.IGNORECASE)
        if match:
            return match.group(0).upper()

    # 從 extracted_results 提取
    if vuln.extracted_results:
        extracted_str = str(vuln.extracted_results)
        match = re.search(r'CVE-\d{4}-\d{4,}', extracted_str, re.IGNORECASE)
        if match:
            return match.group(0).upper()

    return None


def _extract_keywords_from_tech_name(tech_name: str) -> List[str]:
    """
    從技術名稱中提取關鍵字

    例如：
    "Apache Struts 2" -> ["apache", "struts"]
    "Django Framework" -> ["django"]
    """
    # 移除常見的無意義詞
    stop_words = {"framework", "library", "server", "web", "application", "app"}

    # 分割並清理
    words = re.findall(r'\w+', tech_name.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords[:3]  # 最多返回 3 個關鍵字
