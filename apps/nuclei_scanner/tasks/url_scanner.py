import logging
from typing import List, Optional
from celery import shared_task
from django.utils import timezone
from apps.core.models import NucleiScan, URLResult
from c2_core.config.logging import log_function_call
from apps.nuclei_scanner.utils.utils import map_tech_to_nuclei_tags
from .executor import execute_nuclei_command

logger = logging.getLogger(__name__)


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
        ["nice"]
        + ["nuclei"]
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
