# katana_scanner/tasks/__init__.py

import json
import logging
import subprocess
from typing import Optional
from urllib.parse import urlparse

from celery import shared_task

from apps.core.models import Subdomain, URLResult, URLScan
from apps.scanners.base_task import ScannerLifecycle
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)


@shared_task(bind=True)
@log_function_call()
def scan_katana(
    self,
    subdomain_id: int,
    depth: int = 3,
    js_crawl: bool = True,
    execution_graph_id: Optional[int] = None,
    execution_node_id: Optional[int] = None,
):
    """
    對指定子域名執行主動 URL 爬取（使用 katana）。
    填補 GAU 被動歷史資料與 ReconOrchestrator 深度單 URL 分析之間的缺口。
    使用 ScannerLifecycle 管理 URLScan 記錄的狀態機。
    """
    try:
        subdomain = Subdomain.objects.get(id=subdomain_id)
    except Subdomain.DoesNotExist:
        _fail_execution_node(execution_node_id, content=f"Katana 爬取中止：找不到 Subdomain ID {subdomain_id}")
        raise
    logger.info(f"開始對 {subdomain.name} 執行 Katana 主動 URL 爬取 (depth={depth})")

    scan_batch = URLScan.objects.create(
        target_subdomain=subdomain, tool="katana", status="PENDING"
    )

    command = [
        "katana",
        "-u", f"https://{subdomain.name}",
        "-depth", str(depth),
        "-known-files", "all",
        "-field-scope", "rdn",
        "-json",
        "-silent",
        "-no-color",
    ]
    if js_crawl:
        command.append("-js-crawl")

    try:
        with ScannerLifecycle(scan_batch, logger):
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            valid_urls = set()
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    endpoint = data.get("request", {}).get("endpoint", "")
                    if not endpoint:
                        continue
                    parsed = urlparse(endpoint)
                    if parsed.hostname and subdomain.name in parsed.hostname:
                        valid_urls.add(endpoint)
                except (json.JSONDecodeError, Exception):
                    continue

            process.wait()

            if not valid_urls:
                logger.info(f"Katana 未發現任何有效 URL for {subdomain.name}")
                content = f"Katana 爬取完成。子域名: {subdomain.name}（無結果）"
                _complete_execution_node(execution_node_id, content=content, output={"urls_found_count": 0})
                return content

            logger.info(f"Katana 發現 {len(valid_urls)} 個有效 URL，開始入庫...")

            new_objects = [
                URLResult(
                    url=url,
                    target=subdomain.target,
                    last_scan_type="active_katana",
                    last_scan_id=scan_batch.id,
                )
                for url in valid_urls
            ]
            URLResult.objects.bulk_create(new_objects, ignore_conflicts=True)

            url_results = URLResult.objects.filter(url__in=valid_urls)
            subdomain.related_urls.add(*url_results)
            scan_batch.results.add(*url_results)
            scan_batch.urls_found_count = len(valid_urls)
            scan_batch.save(update_fields=["urls_found_count"])

            logger.info(f"Katana 爬取完成 for {subdomain.name}。共處理 {len(valid_urls)} 條 URL。")
    except Exception as exc:
        _fail_execution_node(
            execution_node_id,
            content=f"Katana 爬取失敗。Subdomain: {subdomain.name}: {exc}",
            error={"error_type": type(exc).__name__, "message": str(exc)},
        )
        raise

    content = f"Katana 爬取完成。子域名: {subdomain.name}，發現 {len(valid_urls)} 個 URL。"
    _complete_execution_node(execution_node_id, content=content, output={"urls_found_count": len(valid_urls)})
    return content


def _complete_execution_node(execution_node_id: Optional[int], *, content: str, output: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.complete_node_by_id(execution_node_id, output=output, content=content)


def _fail_execution_node(execution_node_id: Optional[int], *, content: str, error: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.fail_node_by_id(execution_node_id, content=content, error=error)
