import hashlib
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from apps.core.models import Vulnerability

logger = logging.getLogger(__name__)


def save_nuclei_result_to_db(
    data: Dict[str, Any], asset_id: int, asset_type: str, scan_record_id: int = None
) -> Vulnerability:
    """
    將單條 Nuclei 結果存入 Vulnerability 表，並精確關聯掃描記錄
    """
    template_id = data.get("template-id")
    matched_at = data.get("matched-at")
    # 增加更多維度生成指紋，防止重複
    finger_str = f"{template_id}{matched_at}{data.get('type','')}"
    fingerprint = hashlib.sha256(finger_str.encode()).hexdigest()

    info = data.get("info", {})
    defaults = {
        "name": info.get("name", "Unknown"),
        "severity": info.get("severity", "info"),
        "extracted_results": data.get("extracted-results", []),
        "request_raw": data.get("request", ""),
        "response_raw": data.get("response", ""),
        "description": info.get("description", ""),
        "status": "unverified",
        "last_seen": timezone.now(),
    }

    if asset_type == "IP":
        defaults["ip_asset_id"] = asset_id
    elif asset_type == "Subdomain":
        defaults["subdomain_asset_id"] = asset_id
    elif asset_type == "URL":
        defaults["url_asset_id"] = asset_id

    vuln_obj, created = Vulnerability.objects.update_or_create(
        fingerprint=fingerprint, defaults=defaults
    )

    # 關聯到具體的掃描記錄 (ManyToMany)
    if scan_record_id:
        vuln_obj.discovery_scans.add(scan_record_id)  # 假設模型中有此 M2M 欄位

    return vuln_obj
