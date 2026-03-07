import logging
from typing import List, Optional
from celery import shared_task
from apps.core.models import NucleiScan, Subdomain
from c2_core.config.logging import log_function_call
from .executor import execute_nuclei_command

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_subdomain_batch(
    self, subdomain_ids: List[int], custom_tags: Optional[List[str]] = None
):
    """
    Subdomain 掃描：側重接管、配置與 DNS
    """
    sub_records = Subdomain.objects.filter(id__in=subdomain_ids).values("id", "name")
    sub_map = {r["name"]: r["id"] for r in sub_records}
    scan_record_ids = []

    tags = (
        ",".join(custom_tags) if custom_tags else "dns,ssl,subtakeover,tech,misconfig"
    )

    for name, sid in sub_map.items():
        scan = NucleiScan.objects.create(
            subdomain_asset_id=sid,
            severity_filter="all",
            template_ids=[tags],
            status="RUNNING",
        )
        scan_record_ids.append(scan.id)

    if not sub_map:
        return

    targets = []
    for name in sub_map.keys():
        targets.extend(["-u", name])

    command = ["nuclei"] + targets + ["-as", "-tags", tags, "-j", "-nc", "-silent"]
    execute_nuclei_command(command, sub_map, "Subdomain", scan_record_ids)
