import logging
from typing import List, Optional
from celery import shared_task
from apps.core.models import NucleiScan, IP
from c2_core.config.logging import log_function_call
from .executor import execute_nuclei_command

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_ip_batch(
    self, ip_ids: List[int], custom_tags: Optional[List[str]] = None
):
    """
    IP 掃描：側重基礎設施與開放服務
    """
    ip_records = IP.objects.filter(id__in=ip_ids).values("id", "ipv4", "ipv6")
    ip_map = {}
    scan_record_ids = []

    # 預設更強力的 Tags
    tags = (
        ",".join(custom_tags)
        if custom_tags
        else "network,cves,exposures,panel,misconfig"
    )

    for r in ip_records:
        val = r["ipv4"] or r["ipv6"]
        if val:
            ip_map[val] = r["id"]
            scan = NucleiScan.objects.create(
                ip_asset_id=r["id"],
                severity_filter="info-crit",
                template_ids=[tags],  # 記錄本次使用的 tags
                status="RUNNING",
            )
            scan_record_ids.append(scan.id)

    if not ip_map:
        return

    # 命令優化：加入 -tags 並保持 -as 以增強識別
    targets = []
    for ip in ip_map.keys():
        targets.extend(["-u", ip])

    command = (
        ["nice"]
        + ["nuclei"]
        + targets
        + ["-tags", tags, "-as", "-j", "-ni", "-nc", "-silent"]
    )

    execute_nuclei_command(command, ip_map, "IP", scan_record_ids)
