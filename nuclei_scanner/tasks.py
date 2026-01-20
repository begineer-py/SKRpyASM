import hashlib
import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.utils import timezone
from core.models import NucleiScan, Vulnerability, IP, URLResult, Subdomain
from c2_core.config.logging import log_function_call
from nuclei_scanner.utils.utils import map_tech_to_nuclei_tags

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
        ["nuclei"] + targets + ["-tags", tags, "-as", "-j", "-ni", "-nc", "-silent"]
    )

    execute_nuclei_command(command, ip_map, "IP", scan_record_ids)


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


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_url_batch(
    self, url_ids: List[int], custom_tags: Optional[List[str]] = None
):
    """
    URL 掃描：最強力度，覆蓋 Web 核心漏洞
    + 智能技術棧偵測 (Smart Tech-based Scanning)
    """

    # 1. 取得 URL 物件，並預先加載關聯的 technologies (優化資料庫查詢)
    url_objects = URLResult.objects.filter(id__in=url_ids).prefetch_related(
        "technologies"
    )

    url_map = {obj.url: obj.id for obj in url_objects}
    scan_record_ids = []

    # 2. 設定基礎 Tags (這裡放不管什麼技術都要掃的通用漏洞)
    base_tags = [
        "cves",
        "vulnerabilities",
        "exposure",
        "sqli",
        "xss",
        "rce",
        "lfi",
        "ssrf",
        "token-spray",
        "misconfig",
    ]
    if custom_tags:
        base_tags = custom_tags

    # 3. 從 DB 提取技術並翻譯成 Nuclei Tags
    tech_tags = set()

    for obj in url_objects:
        # 透過 related_name="technologies" 訪問反向關聯
        tech_entries = obj.technologies.all()

        for tech in tech_entries:
            raw_name = tech.name
            if raw_name:
                # 呼叫翻譯官
                mapped_tags = map_tech_to_nuclei_tags(raw_name)
                if mapped_tags:
                    tech_tags.update(mapped_tags)
                    # logger.debug(f"[Nuclei] URL: {obj.url} | Tech: {raw_name} -> Tags: {mapped_tags}")

    # 4. 合併 Tags (基礎 + 技術特有)
    # 使用 set 去除重複，並過濾掉空值
    final_tags_list = list(set(base_tags) | tech_tags)
    final_tags_list = [t for t in final_tags_list if t]  # 雙重保險去空值

    final_tags_str = ",".join(final_tags_list)

    logger.info(
        f"Nuclei 智能 URL 掃描啟動 | 目標數: {len(url_map)} | Tags: {final_tags_str}"
    )

    # 建立掃描記錄 (NucleiScan)
    for url, uid in url_map.items():
        scan = NucleiScan.objects.create(
            url_asset_id=uid,
            severity_filter="low-crit",
            template_ids=[final_tags_str],  # 記錄用了哪些 tags，方便日後稽核
            status="RUNNING",
        )
        scan_record_ids.append(scan.id)

    if not url_map:
        return

    targets = []
    for url in url_map.keys():
        targets.extend(["-u", url])

    # 5. 執行命令
    command = (
        ["nuclei"]
        + targets
        + [
            "-tags",
            final_tags_str,  # 傳入動態生成的 Tags
            "-as",  # 自動掃描模式 (保留，讓 Nuclei 自己也做點事)
            "-severity",
            "low,medium,high,critical",
            "-j",  # JSON 輸出
            "-nc",  # No Color
            "-silent",  # 靜默模式
            # "-rate-limit", "150", # 如果怕被打，可以考慮加限速
        ]
    )

    # 呼叫你原本寫好的執行器
    execute_nuclei_command(command, url_map, "URL", scan_record_ids)


def execute_nuclei_command(
    command: List[str],
    asset_map: Dict[str, int],
    asset_type: str,
    scan_record_ids: List[int],
):
    """
    封裝 Nuclei 執行邏輯，實現實時流處理
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        for line in iter(process.stdout.readline, ""):
            if not line:
                continue
            try:
                result = json.loads(line.strip())
                # 根據不同的 asset_type 提取目標標識
                target_key = None
                if asset_type == "IP":
                    target_key = result.get("ip")
                elif asset_type == "Subdomain":
                    target_key = result.get("host")
                elif asset_type == "URL":
                    target_key = result.get("matched-at") or result.get("url")

                # 模糊匹配處理 (處理 URL 末尾斜槓或端口)
                asset_id = asset_map.get(target_key)
                if not asset_id and target_key:
                    asset_id = next(
                        (v for k, v in asset_map.items() if target_key.startswith(k)),
                        None,
                    )

                if asset_id:
                    save_nuclei_result_to_db(
                        result,
                        asset_id=asset_id,
                        asset_type=asset_type,
                        scan_record_id=None,  # 這裡可以根據需要傳入具體的 scan_id
                    )
            except json.JSONDecodeError:
                continue

        process.wait()
        NucleiScan.objects.filter(id__in=scan_record_ids).update(
            status="COMPLETED", completed_at=timezone.now()
        )

    except Exception as e:
        logger.exception(f"{asset_type} Nuclei 掃描執行失敗: {e}")
        NucleiScan.objects.filter(id__in=scan_record_ids).update(
            status="FAILED", completed_at=timezone.now()
        )
