# get_all_url/tasks.py (或其他定義 perform_scan_for_url 的文件)

import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from urllib.parse import urlparse

from c2_core.config.logging import log_function_call
from .orchestrators.recon_orchestrator import ReconOrchestrator
from c2_core.config.utils import sanitize_for_db

from apps.core.models import (
    Subdomain,
    Seed,
    URLScan,
    URLResult,
    AnalysisFinding,
    Form,
    JavaScriptFile,
    Link,
    Comment,
    MetaTag,
    Iframe,
    TechStack,
)

logger = logging.getLogger(__name__)


def save_tech_stack_to_db(url_result_obj, tech_stack_result: dict):
    """
    全量更新模式：
    1. 刪除該 URL 關聯的所有舊 TechStack。
    2. 寫入本次掃描發現的所有新 TechStack。
    """
    from apps.core.models.assets import TechStack

    fingerprints = tech_stack_result.get("fingerprints_matched", [])
    if not fingerprints:
        # 如果這次沒掃到任何技術，也要清空舊的嗎？
        # 通常是的，這代表目標隱藏了指紋
        TechStack.objects.filter(which_url_result=url_result_obj).delete()
        return

    # 1. 清理舊數據 (這一步確保資料庫裡不會有殘留的過時版本)
    TechStack.objects.filter(which_url_result=url_result_obj).delete()

    to_create = []
    seen_in_batch = set()

    for item in fingerprints:
        name = item.get("name")
        if not name:
            continue

        version = item.get("version")
        clean_version = version if version and version.lower() != "n/a" else None

        # 本次批次內去重
        if (name, clean_version) in seen_in_batch:
            continue
        seen_in_batch.add((name, clean_version))

        categories = item.get("categories", [])
        if not isinstance(categories, list):
            categories = []

        to_create.append(
            TechStack(
                which_url_result=url_result_obj,
                name=name,
                version=clean_version,
                categories=categories,
            )
        )

    # 2. 寫入新數據 (不需要 ignore_conflicts 了，因為舊的都刪了)
    if to_create:
        TechStack.objects.bulk_create(to_create)
        logger.info(
            f"已更新 {url_result_obj.url} 的技術棧: 寫入 {len(to_create)} 條記錄。"
        )


@shared_task(bind=True)
@log_function_call()
def perform_scan_for_url(self, url: str, method: str = "GET", seed_id: int = None):
    """
    對指定 URL 執行深度偵察。
    適配：URLScan (target_url/target_subdomain) 和 URLResult (related_subdomains M2M)。
    """

    scan_task = None

    try:

        # 2. 解析 Subdomain (資產上下文)
        hostname = urlparse(url).hostname
        if not hostname:
            raise ValueError(f"URL '{url}' 格式無效，無法解析 hostname。")

        subdomain, created = Subdomain.objects.get_or_create(
            name=hostname,
            defaults={"is_active": True, "last_seen": timezone.now()},
        )
        # 將子域名與 Seed 綁定 (M2M)
        if seed_id:
            try:
                seed_obj = Seed.objects.get(id=seed_id)
                subdomain.which_seed.add(seed_obj)
            except Seed.DoesNotExist:
                logger.warning(f"提供的 seed_id 不存在: {seed_id}")
        if created:
            logger.info(f"發現並創建了新子域名資產: {hostname}")
        # --- 初始化階段 (Atomic) ---
        with transaction.atomic():
            # 3. 準備 URLResult (被掃描的對象)
            # 注意：這裡不填 subdomain 關聯，因為現在是 M2M，稍後用 .add()
            url_result, created = URLResult.objects.update_or_create(
                url=url,
                defaults={
                    "content_fetch_status": "PENDING",
                    "last_scan_type": "active_recon_orchestrator",  # 更新來源標記
                    # 重置關鍵欄位以反映這是一次新掃描的開始
                    "status_code": None,
                    "title": None,
                },
            )

            # 4. 建立資產歸屬 (M2M)
            # 確保這個 URL 被歸類到當前的子域名下
            url_result.related_subdomains.add(subdomain)

            # 5. 創建掃描任務記錄 (Input Target)
            # 這是針對「特定 URL」的掃描，但也屬於「特定子域名」的上下文
            scan_task = URLScan.objects.create(
                target_url=url_result,  # 主要目標
                target_subdomain=subdomain,  # 上下文目標
                tool="recon_orchestrator",  # 標記工具
                status="RUNNING",
            )

            # 更新 URLResult 的 last_scan_id
            url_result.last_scan_id = scan_task.id
            url_result.save(update_fields=["last_scan_id"])

            # 6. 建立掃描產出關聯 (Output Result - M2M)
            # 雖然是掃描它自己，但在數據模型上，這個 URL 也是這次掃描的「結果」
            scan_task.results.add(url_result)

            logger.info(f"掃描初始化完成。Task ID: {scan_task.id}, Target: {url}")

        # --- 執行階段 (耗時操作) ---
        orchestrator = ReconOrchestrator(url=url, method=method)
        result = orchestrator.run()

        if not result.get("success"):
            raise Exception(f"偵察流水線回報錯誤: {result.get('error')}")

        # --- 入庫階段 (Atomic) ---
        with transaction.atomic():
            # 鎖定行，防止競爭
            url_result_to_update = URLResult.objects.select_for_update().get(
                id=url_result.id
            )

            # 7. 清理舊的關聯數據 (子表)
            # 這裡的邏輯不變，因為這些子表依然是透過 ForeignKey 指向 URLResult
            url_result_to_update.forms.all().delete()
            url_result_to_update.js_files.all().delete()
            url_result_to_update.links.all().delete()
            url_result_to_update.comments.all().delete()
            url_result_to_update.meta_tags.all().delete()
            url_result_to_update.iframes.all().delete()
            url_result_to_update.findings.all().delete()

            # 8. 更新 URLResult 本體數據
            spider_data = result.get("spider_result", {})

            url_result_to_update.final_url = result.get("final_url")
            url_result_to_update.is_external_redirect = spider_data.get(
                "is_external_redirect", False
            )
            url_result_to_update.status_code = spider_data.get("status_code")
            url_result_to_update.headers = spider_data.get("response_headers")
            url_result_to_update.content_length = spider_data.get(
                "response_body_length"
            )
            url_result_to_update.used_flaresolverr = result.get(
                "used_flaresolverr", False
            )
            url_result_to_update.raw_response = sanitize_for_db(
                spider_data.get("response_text", "")
            )
            url_result_to_update.title = spider_data.get("title")
            url_result_to_update.content_fetch_status = result.get(
                "content_fetch_status", "COMPLETED"
            )
            url_result_to_update.raw_response_hash = result.get("raw_response_hash", "")
            url_result_to_update.cleaned_html = result.get("cleaned_html", "")
            url_result_to_update.extracted_js = result.get("extracted_js", "")

            url_result_to_update.save()

            # 9. 批量寫入子表 (Forms, JS, etc.)
            # 這些寫法完全保持不變，因為它們依賴 which_url (FK)
            forms_data = result.get("forms_result", [])
            if forms_data:
                Form.objects.bulk_create(
                    [Form(which_url=url_result_to_update, **i) for i in forms_data]
                )

            scripts_data = result.get("scripts_result", [])
            if scripts_data:
                JavaScriptFile.objects.bulk_create(
                    [
                        JavaScriptFile(which_url=url_result_to_update, **i)
                        for i in scripts_data
                    ],
                    ignore_conflicts=True,
                )

            links_data = result.get("links_result", [])
            if links_data:
                Link.objects.bulk_create(
                    [Link(which_url=url_result_to_update, **i) for i in links_data]
                )

            comments_data = result.get("comments_result", [])
            if comments_data:
                Comment.objects.bulk_create(
                    [
                        Comment(which_url=url_result_to_update, **i)
                        for i in comments_data
                    ]
                )

            meta_tags_data = result.get("meta_tags_result", [])
            if meta_tags_data:
                MetaTag.objects.bulk_create(
                    [
                        MetaTag(which_url=url_result_to_update, attributes=i)
                        for i in meta_tags_data
                    ]
                )

            iframes_data = result.get("iframes_result", [])
            if iframes_data:
                Iframe.objects.bulk_create(
                    [Iframe(which_url=url_result_to_update, **i) for i in iframes_data]
                )

            analysis_data = result.get("analysis_result", [])
            if analysis_data:
                findings = [
                    AnalysisFinding(
                        which_url_result=url_result_to_update,
                        pattern_name=group.get("pattern"),
                        line_number=match.get("line"),
                        match_content=match.get("match"),
                    )
                    for group in analysis_data
                    for match in group.get("matches", [])
                ]
                AnalysisFinding.objects.bulk_create(findings, ignore_conflicts=True)
            tech_stack_data = result.get("tech_stack_result", {})
            if tech_stack_data:
                save_tech_stack_to_db(url_result_to_update, tech_stack_data)

        # 10. 完成任務
        if scan_task:
            scan_task.status = "COMPLETED"
            scan_task.completed_at = timezone.now()
            scan_task.save()

        logger.info(f"任務完成: {url}")

    except ValueError as e:
        logger.error(f"參數錯誤: {e}")
        if scan_task:
            URLScan.objects.filter(id=scan_task.id).update(
                status="FAILED", error_message=str(e), completed_at=timezone.now()
            )

    except Exception as e:
        logger.exception(f"任務執行失敗 {url}: {e}")
        if scan_task:
            URLScan.objects.filter(id=scan_task.id).update(
                status="FAILED", error_message=str(e), completed_at=timezone.now()
            )
