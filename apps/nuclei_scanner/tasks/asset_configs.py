"""
apps/nuclei_scanner/tasks/asset_configs.py

NucleiAssetConfig 工廠配置（Factory Registry）

每種資產型別在 Nuclei 掃描中的差異集中於此，包含資料庫讀取方式、目標字串提取、以及特定標籤（Tags）的生成邏輯。
讓 `_execute_nuclei_batch()` 能統一協調掃描工作。
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Dict


@dataclass
class NucleiAssetConfig:
    """
    Nuclei 掃描的資產設定

    Attributes:
        asset_name: 資產名稱 (用於日誌，如 'IP')
        prepare_targets: 將 IDs 與 custom_tags 轉換成 Nuclei 執行所需的 (target_map, scan_record_ids, cli_targets, final_tags_str)
    """
    asset_name: str
    prepare_targets: Callable[[List[int], Optional[List[str]]], Tuple[Dict[str, int], List[int], List[str], str]]


# =============================================================================
# 各資產的目標準備邏輯
# =============================================================================

def _prepare_ip_targets(ip_ids: List[int], custom_tags: Optional[List[str]]) -> Tuple[Dict[str, int], List[int], List[str], str]:
    from apps.core.models import IP, NucleiScan

    ip_records = IP.objects.filter(id__in=ip_ids).values("id", "address", "version")
    ip_map = {}
    scan_record_ids = []

    tags = ",".join(custom_tags) if custom_tags else "network,cves,exposures,panel,misconfig"

    for r in ip_records:
        val = r["address"]
        if val:
            ip_map[val] = r["id"]
            scan = NucleiScan.objects.create(
                ip_asset_id=r["id"],
                severity_filter="info-crit",
                template_ids=[tags],
                status="RUNNING",
            )
            scan_record_ids.append(scan.id)

    targets = []
    for ip in ip_map.keys():
        targets.extend(["-u", ip])

    return ip_map, scan_record_ids, targets, tags


def _prepare_subdomain_targets(sub_ids: List[int], custom_tags: Optional[List[str]]) -> Tuple[Dict[str, int], List[int], List[str], str]:
    from apps.core.models import Subdomain, NucleiScan

    sub_records = Subdomain.objects.filter(id__in=sub_ids).values("id", "name")
    sub_map = {r["name"]: r["id"] for r in sub_records}
    scan_record_ids = []

    tags = ",".join(custom_tags) if custom_tags else "dns,ssl,subtakeover,tech,misconfig"

    for name, sid in sub_map.items():
        scan = NucleiScan.objects.create(
            subdomain_asset_id=sid,
            severity_filter="all",
            template_ids=[tags],
            status="RUNNING",
        )
        scan_record_ids.append(scan.id)

    targets = []
    for name in sub_map.keys():
        targets.extend(["-u", name])

    return sub_map, scan_record_ids, targets, tags


def _prepare_url_targets(url_ids: List[int], custom_tags: Optional[List[str]]) -> Tuple[Dict[str, int], List[int], List[str], str]:
    from apps.core.models import URLResult, NucleiScan
    from apps.nuclei_scanner.utils.utils import map_tech_to_nuclei_tags
    import logging
    logger = logging.getLogger(__name__)

    url_objects = URLResult.objects.filter(id__in=url_ids).prefetch_related("technologies")
    url_map = {obj.url: obj.id for obj in url_objects}
    scan_record_ids = []

    base_tags = [
        "cves", "vulnerabilities", "exposure", "sqli", "xss", 
        "rce", "lfi", "ssrf", "token-spray", "misconfig"
    ]
    if custom_tags:
        base_tags = custom_tags

    tech_tags = set()
    for obj in url_objects:
        for tech in obj.technologies.all():
            if tech.name:
                mapped_tags = map_tech_to_nuclei_tags(tech.name)
                if mapped_tags:
                    tech_tags.update(mapped_tags)

    final_tags_list = list(set(base_tags) | tech_tags)
    final_tags_list = [t for t in final_tags_list if t]
    final_tags_str = ",".join(final_tags_list)

    logger.info(f"Nuclei 智能 URL 掃描 tags 總結: {final_tags_str}")

    for url, uid in url_map.items():
        scan = NucleiScan.objects.create(
            url_asset_id=uid,
            severity_filter="low-crit",
            template_ids=[final_tags_str],
            status="RUNNING",
        )
        scan_record_ids.append(scan.id)

    targets = []
    for url in url_map.keys():
        targets.extend(["-u", url])

    return url_map, scan_record_ids, targets, final_tags_str


# =============================================================================
# 懶加載 Registry
# =============================================================================

_nuclei_registry_cache: dict | None = None

def get_nuclei_asset_registry() -> dict:
    global _nuclei_registry_cache
    if _nuclei_registry_cache is None:
        _nuclei_registry_cache = {
            "ip": NucleiAssetConfig(
                asset_name="IP",
                prepare_targets=_prepare_ip_targets,
            ),
            "subdomain": NucleiAssetConfig(
                asset_name="Subdomain",
                prepare_targets=_prepare_subdomain_targets,
            ),
            "url": NucleiAssetConfig(
                asset_name="URL",
                prepare_targets=_prepare_url_targets,
            ),
        }
    return _nuclei_registry_cache
