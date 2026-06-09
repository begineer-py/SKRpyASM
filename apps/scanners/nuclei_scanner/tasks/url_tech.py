import subprocess
import logging
from celery import shared_task
from django.conf import settings
from apps.core.models import URLResult
from .utils import process_nuclei_tech_line  # 假設解析代碼放在 parsers.py
from apps.core.header_injection import get_tagged_headers

logger = logging.getLogger(__name__)


@shared_task(name="nuclei_scanner.tasks.url_tech.scan_url_tech_stack")
def scan_url_tech_stack(url_result_ids: list[int], target_id: int = None, execution_graph_id: int | None = None, execution_node_id: int | None = None):
    """
    針對指定的 URLResult 執行技術堆疊掃描
    """
    urls_to_scan = URLResult.objects.filter(id__in=url_result_ids)

    if not target_id and urls_to_scan.exists():
        resolved_target_id = urls_to_scan.first().target_id
    else:
        resolved_target_id = target_id

    results_count = 0

    for url_res in urls_to_scan:
        logger.info(f"正在掃描 URL 技術堆疊: {url_res.url}")

        command = [
            "nice",
            "nuclei",
            "-u",
            url_res.url,
            "-tags",
            "tech",
            "-jsonl",
            "-silent",
            "-nc",
        ]

        tagged_headers = get_tagged_headers(target_id=resolved_target_id)
        for h_key, h_val in tagged_headers.items():
            command.extend(["-H", f"{h_key}: {h_val}"])

        from apps.core.header_injection import build_rate_limit_args
        command.extend(build_rate_limit_args("nuclei", resolved_target_id))

        try:
            # 執行並實時讀取輸出
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            for line in process.stdout:
                if line.strip():
                    # 呼叫我們先前寫好的通用解析函數
                    process_nuclei_tech_line(line, url_res)

            process.wait()
            results_count += 1

        except Exception as e:
            logger.error(f"掃描 URL 失敗 {url_res.url}: {str(e)}")
            continue

    # === CVE 對應：自動觸發 TechStack CVE 同步 ===
    if urls_to_scan.exists():
        from apps.scanners.cve_intelligence.tasks.enrichment_tasks import sync_techstack_cves

        # 取得所有相關的 target_id
        target_ids = set(urls_to_scan.values_list("target_id", flat=True))

        for target_id in target_ids:
            if target_id:
                logger.info(f"Triggering TechStack CVE sync for target {target_id}")
                sync_techstack_cves.delay(target_id)

    result = f"完成 {results_count} 個 URL 的技術堆疊掃描"
    _complete_execution_node(execution_node_id, content=result, output={"results_count": results_count})
    return result


def _complete_execution_node(execution_node_id: int | None, *, content: str, output: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.complete_node_by_id(execution_node_id, output=output, content=content)
