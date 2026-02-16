import logging
import hashlib
from urllib.parse import urlparse
from celery import shared_task
from django.utils import timezone
from django.db import transaction

# c2_core imports
from c2_core.config.logging import log_function_call
from apps.flaresolverr.orchestrators.recon_orchestrator import ReconOrchestrator
from c2_core.config.utils import sanitize_for_db
from c2_core.config.config import Config

# Model imports
MODEL_PATH = Config.MODEL_PATH
from apps.core.models import (
    Subdomain,
    URLScan,
    URLResult,
)
from apps.flaresolverr.tasks.utils import _save_scan_artifacts

logger = logging.getLogger(__name__)


@shared_task(bind=True)
@log_function_call()
def perform_scan_for_url(
    self,
    url: str,
    method: str = "GET",
    seed_id: int = None,
    auto_create: bool = False,
    target_id: int = None,  # 新增：直接接收已驗證的 target_id
):
    """
    對指定 URL 執行深度偵察。
    接收由 API 層驗證過的 target_id，大幅簡化內部邏輯。
    """

    scan_task = None
    url_result = None
    result = {}

    try:
        # 【步驟 1：參數驗證與資產定位】
        hostname = urlparse(url).hostname
        if not hostname:
            raise ValueError(f"URL '{url}' 格式無效，無法解析 hostname。")

        # 準備 Subdomain 的預設值
        defaults = {"is_active": True, "last_seen": timezone.now()}
        if target_id:
            defaults["target_id"] = target_id

        # 獲取或創建 Subdomain
        if auto_create:
            subdomain, created = Subdomain.objects.get_or_create(
                name=hostname,
                defaults=defaults,
            )
            if created:
                logger.info(
                    f"發現並創建了新子域名資產: {hostname} (Target ID: {target_id})"
                )
        else:
            subdomain = Subdomain.objects.get(name=hostname)
            created = False

        # 自動修復：如果傳入了 target_id 但 Subdomain 尚未綁定，則進行綁定
        if target_id and not subdomain.target_id:
            logger.info(
                f"自動修復: 將 Subdomain {subdomain.name} 綁定到 Target ID {target_id}"
            )
            subdomain.target_id = target_id
            subdomain.save(update_fields=["target_id"])

        # 【步驟 2：初始化任務記錄 (事務 1)】
        with transaction.atomic():
            # 準備 URLResult defaults
            url_defaults = {
                "content_fetch_status": "PENDING",
                "last_scan_type": "active_recon_orchestrator",
                "status_code": None,
                "title": None,
            }
            # 如果是新創建的 URLResult，直接寫入 target_id
            if target_id:
                url_defaults["target_id"] = target_id

            url_result, _ = URLResult.objects.update_or_create(
                url=url,
                defaults=url_defaults,
            )

            # 建立資產歸屬關係
            url_result.related_subdomains.add(subdomain)

            # 創建掃描任務日誌
            scan_task = URLScan.objects.create(
                target_url=url_result,
                target_subdomain=subdomain,
                tool="recon_orchestrator",
                status="RUNNING",
            )

            # 更新雙向關聯
            url_result.last_scan_id = scan_task.id
            url_result.save(update_fields=["last_scan_id"])
            scan_task.results.add(url_result)

            logger.info(f"掃描初始化完成。Task ID: {scan_task.id}, Target: {url}")

        # 【步驟 3：執行核心掃描邏輯 (Orchestrator)】
        orchestrator = ReconOrchestrator(url=url, method=method)
        result = orchestrator.run()

        # 獲取關鍵狀態位
        is_success = result.get("success", False)
        error_msg = result.get("error")
        fetch_status = result.get("content_fetch_status", "FAILED_UNKNOWN")
        spider_data = result.get("spider_result", {})

        # 【步驟 4：更新掃描結果基礎資訊 (事務 2)】
        with transaction.atomic():
            url_result_to_update = URLResult.objects.get(id=url_result.id)

            # 清空舊資料 logic...
            if is_success or fetch_status in ["FAILED_BLOCKED", "FAILED_NO_CONTENT"]:
                url_result_to_update.forms.all().delete()
                url_result_to_update.links.all().delete()
                url_result_to_update.comments.all().delete()
                url_result_to_update.meta_tags.all().delete()
                url_result_to_update.iframes.all().delete()
                url_result_to_update.findings.all().delete()

            # 寫入 HTTP 響應數據
            url_result_to_update.final_url = result.get("final_url", url)
            url_result_to_update.content_fetch_status = fetch_status
            url_result_to_update.status_code = spider_data.get("status_code")
            url_result_to_update.headers = spider_data.get("response_headers")
            url_result_to_update.content_length = spider_data.get(
                "response_body_length"
            )
            url_result_to_update.is_external_redirect = spider_data.get(
                "is_external_redirect", False
            )
            url_result_to_update.used_flaresolverr = result.get(
                "used_flaresolverr", False
            )

            # 寫入 HTML 相關
            if result.get("text"):
                url_result_to_update.title = spider_data.get("title")
                url_result_to_update.raw_response = sanitize_for_db(
                    spider_data.get("response_text", "")
                )
                url_result_to_update.text = result.get("text", "")
                url_result_to_update.cleaned_html = result.get("cleaned_html", "")
                url_result_to_update.raw_response_hash = result.get(
                    "raw_response_hash", ""
                )

            # 再次確保 Target ID (如果是舊資料更新)
            if target_id and not url_result_to_update.target_id:
                url_result_to_update.target_id = target_id

            url_result_to_update.save()

        # 【步驟 5：檢查抓取結果】
        if not is_success:
            logger.warning(f"任務回報失敗狀態: {error_msg} (Status: {fetch_status})")
            if scan_task:
                scan_task.status = "COMPLETED"
                scan_task.error_message = (
                    f"{fetch_status}: {error_msg}" if error_msg else fetch_status
                )
                scan_task.completed_at = timezone.now()
                scan_task.save()
            return

        # 【步驟 6：資產膨脹 - 處理發現的連結 (事務 3)】
        # 邏輯大幅簡化：直接使用 target_id 確定範圍
        with transaction.atomic():
            processed_links = result.get(
                "processed_links", {"internal": [], "external": []}
            )

            if processed_links["internal"] or processed_links["external"]:

                # --- 1. 準備 Scope 過濾清單 ---
                valid_hostnames = {hostname}
                sub_map = {}  # hostname -> subdomain_id

                if target_id:
                    # 有 Target ID：允許該 Target 下的所有子域名
                    sub_rows = Subdomain.objects.filter(
                        target_id=target_id
                    ).values_list("name", "id")
                    for n, i in sub_rows:
                        valid_hostnames.add(n)
                        sub_map[n] = i
                else:
                    # 無 Target ID (孤兒資產)：僅允許當前子域名
                    sub_map[hostname] = subdomain.id

                # --- 2. 過濾與清洗 ---
                all_discovered_urls = []
                for link in processed_links.get("internal", []):
                    all_discovered_urls.append({"url": link, "source": "CRAWL_html"})
                for link in processed_links.get("external", []):
                    all_discovered_urls.append({"url": link, "source": "JS_EXT"})

                valid_items = []
                seen_urls = set()

                for item in all_discovered_urls:
                    u = item["url"]
                    if u in seen_urls:
                        continue

                    h_name = urlparse(u).hostname
                    if h_name in valid_hostnames:
                        seen_urls.add(u)
                        valid_items.append(item)

                if valid_items:
                    # --- 3. 批量創建 URLResult ---
                    target_urls_list = list(seen_urls)
                    existing_map = dict(
                        URLResult.objects.filter(url__in=target_urls_list).values_list(
                            "url", "id"
                        )
                    )

                    new_objects = []
                    for item in valid_items:
                        if item["url"] not in existing_map:
                            new_objects.append(
                                URLResult(
                                    url=item["url"],
                                    discovery_source=item["source"],
                                    content_fetch_status="PENDING",
                                    target_id=target_id,  # 直接寫入 Target ID
                                )
                            )

                    if new_objects:
                        URLResult.objects.bulk_create(
                            new_objects, ignore_conflicts=True
                        )
                        logger.info(f"批量創建了 {len(new_objects)} 個新 URLResult")

                    # --- 4. 建立關聯 ---
                    final_url_map = dict(
                        URLResult.objects.filter(url__in=target_urls_list).values_list(
                            "url", "id"
                        )
                    )

                    RelSubdomainThrough = URLResult.related_subdomains.through
                    DiscoveredByThrough = URLResult.discovered_by_scans.through
                    sub_relations = []
                    scan_relations = []
                    involved_url_ids = []

                    for item in valid_items:
                        url_str = item["url"]
                        url_id = final_url_map.get(url_str)
                        if not url_id:
                            continue

                        involved_url_ids.append(url_id)
                        hn = urlparse(url_str).hostname
                        target_sub_id = sub_map.get(hn)

                        if target_sub_id:
                            sub_relations.append(
                                RelSubdomainThrough(
                                    urlresult_id=url_id, subdomain_id=target_sub_id
                                )
                            )

                        scan_relations.append(
                            DiscoveredByThrough(
                                urlresult_id=url_id, urlscan_id=scan_task.id
                            )
                        )

                    if sub_relations:
                        RelSubdomainThrough.objects.bulk_create(
                            sub_relations, ignore_conflicts=True
                        )

                        # 補漏：如果是舊有的 URLResult 被重新發現，且尚未標記 Target，這裡補上
                        if target_id:
                            URLResult.objects.filter(
                                id__in=involved_url_ids, target__isnull=True
                            ).update(target_id=target_id)

                    if scan_relations:
                        DiscoveredByThrough.objects.bulk_create(
                            scan_relations, ignore_conflicts=True
                        )

                    scan_task.urls_found_count = len(all_discovered_urls)
                    scan_task.save(update_fields=["urls_found_count"])

        # 使用批量寫入 (bulk_create) 提高效能
        url_result_final = URLResult.objects.get(id=url_result.id)

        # 寫入表單
        _save_scan_artifacts(url_result_final, result)

        # 【步驟 11：完成掃描任務】
        # 標記任務為 COMPLETED 並記錄結束時間
        if scan_task:
            scan_task.status = "COMPLETED"
            scan_task.completed_at = timezone.now()
            scan_task.save()

        logger.info(f"任務完成: {url} (狀態: {fetch_status})")

    except ValueError as e:
        # 專門處理參數或格式錯誤
        logger.error(f"參數錯誤: {e}")
        if scan_task:
            URLScan.objects.filter(id=scan_task.id).update(
                status="FAILED", error_message=str(e), completed_at=timezone.now()
            )

    except Exception as e:
        # 處理任何未預期的系統程式錯誤
        logger.exception(f"任務執行發生未預期錯誤 {url}: {e}")
        if scan_task:
            URLScan.objects.filter(id=scan_task.id).update(
                status="FAILED",
                error_message=f"System Error: {str(e)}",
                completed_at=timezone.now(),
            )
        if url_result:
            URLResult.objects.filter(id=url_result.id).update(
                content_fetch_status="FAILED_SYSTEM_ERROR"
            )
