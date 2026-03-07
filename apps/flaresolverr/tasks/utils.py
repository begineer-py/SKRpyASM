from apps.core.models import (
    AnalysisFinding,
    Form,
    JavaScriptFile,
    Link,
    Comment,
    MetaTag,
    Iframe,
    ExtractedJS,
)
from apps.flaresolverr.utils import save_tech_stack_to_db
import hashlib
from c2_core.config.logging import log_function_call
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


@log_function_call()
def _save_scan_artifacts(url_result_final, result):
    """輔助函數：保存所有掃描產出物，保持主函數整潔"""
    # 這裡放入原本代碼 Step 7 到 Step 10 的 bulk_create 邏輯
    # Forms
    forms_data = result.get("forms_result", [])
    if forms_data:
        Form.objects.bulk_create(
            [Form(which_url=url_result_final, **i) for i in forms_data],
            ignore_conflicts=True,
        )

    # Links (Page Links)
    links_data = result.get("links_result", [])
    if links_data:
        Link.objects.bulk_create(
            [Link(which_url=url_result_final, **i) for i in links_data],
            ignore_conflicts=True,
        )

    # Comments
    comments_data = result.get("comments_result", [])
    if comments_data:
        Comment.objects.bulk_create(
            [Comment(which_url=url_result_final, **i) for i in comments_data],
            ignore_conflicts=True,
        )

    # Meta Tags
    meta_tags_data = result.get("meta_tags_result", [])
    if meta_tags_data:
        MetaTag.objects.bulk_create(
            [MetaTag(which_url=url_result_final, attributes=i) for i in meta_tags_data],
            ignore_conflicts=True,
        )

    # Iframes
    iframes_data = result.get("iframes_result", [])
    if iframes_data:
        Iframe.objects.bulk_create(
            [Iframe(which_url=url_result_final, **i) for i in iframes_data],
            ignore_conflicts=True,
        )

    # JS Files
    scripts_data = result.get("scripts_result", [])
    if scripts_data:
        unique_scripts = {
            item.get("src"): item for item in scripts_data if item.get("src")
        }.values()
        for script in unique_scripts:
            src_url = script.get("src")
            content = script.get("content")
            c_hash = (
                hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None
            )
            js_file, _ = JavaScriptFile.objects.get_or_create(
                src=src_url,
                defaults={
                    "content": content,
                    "content_hash": c_hash,
                    "status": "DOWNLOADED" if content else "PENDING",
                },
            )
            js_file.related_pages.add(url_result_final)

    # Findings
    analysis_data = result.get("analysis_result", [])
    if analysis_data:
        findings = [
            AnalysisFinding(
                which_url_result=url_result_final,
                pattern_name=group.get("pattern"),
                line_number=match.get("line"),
                match_content=match.get("match"),
            )
            for group in analysis_data
            for match in group.get("matches", [])
        ]
        AnalysisFinding.objects.bulk_create(findings, ignore_conflicts=True)

    # Tech Stack
    tech_stack_data = result.get("tech_stack_result", {})
    if tech_stack_data:
        save_tech_stack_to_db(url_result_final, tech_stack_data)

    # Extracted JS
    extracted_js_content = result.get("extracted_js", "")

    if extracted_js_content:
        # 計算 SHA-256 Hash (符合你 max_length=64 的設計)
        new_hash = hashlib.sha256(extracted_js_content.encode("utf-8")).hexdigest()

        # 獲取現有的 Hash (如果有的話)，用來判斷內容是否變動
        # 注意：因為是 OneToOne，可以直接透過 related_name 訪問
        existing_obj = getattr(url_result_final, "extracted_js_blocks", None)

        # 決定是否需要更新 is_analyzed
        # 如果內容變了，就標記為 False 需要重新分析
        is_changed = (
            True if not existing_obj or existing_obj.content_hash != new_hash else False
        )

        # 執行更新或創建
        ExtractedJS.objects.update_or_create(
            which_url=url_result_final,
            defaults={
                "content": extracted_js_content,
                "content_hash": new_hash,
                "is_analyzed": (
                    False
                    if is_changed
                    else (existing_obj.is_analyzed if existing_obj else False)
                ),
            },
        )
        logger.info(f"ExtractedJS 已同步 (Hash: {new_hash[:10]}...)")
    else:
        # 如果掃描結果沒東西，直接刪除現有的 OneToOne 關聯對象（淘汰舊的）
        if hasattr(url_result_final, "extracted_js_blocks"):
            url_result_final.extracted_js_blocks.delete()
            logger.info(f"已清理 URL {url_result_final.url} 的舊 ExtractedJS 數據")
