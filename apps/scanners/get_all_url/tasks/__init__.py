# get_all_url/tasks.py

import logging
import subprocess
import os
from urllib.parse import urlparse
from typing import Optional

from celery import shared_task
from django.db import transaction

from c2_core.config.logging import log_function_call
from apps.core.models import Subdomain, URLScan, URLResult
from apps.api_keys.utils import get_active_api_keys, generate_gau_config
from apps.core.utils import with_auto_callback
from apps.scanners.base_task import ScannerLifecycle

logger = logging.getLogger(__name__)

BLACKLIST_EXTS = "png,jpg,jpeg,gif,webp,svg,ico,css,js,woff,woff2,ttf,eot,mp4,mp3,pdf"


@shared_task(bind=True)
@log_function_call()
@with_auto_callback
def scan_all_url(self, subdomain_id: int, threads: int = 50, callback_step_id: Optional[int] = None):
    """
    對指定子域名執行被動 URL 掃描（使用 gau）。
    使用 ScannerLifecycle 管理 URLScan 記錄的狀態機。
    """
    config_file = None
    try:
        subdomain = Subdomain.objects.prefetch_related("which_seed").get(id=subdomain_id)
        seed_values = ",".join([s.value for s in subdomain.which_seed.all()])
        logger.info(f"開始對 {subdomain.name} (Seeds: {seed_values}) 進行被動 URL 掃描")

        scan_batch = URLScan.objects.create(
            target_subdomain=subdomain, tool="gau", status="PENDING"
        )

        api_keys = get_active_api_keys()
        config_file = generate_gau_config(api_keys)

        command = [
            "docker",
            "run",
            "--rm",
            "-v", f"{config_file}:/root/.gau.toml",
            "sxcurity/gau:latest",
            subdomain.name,
            "--threads", "50",
            "--blacklist", BLACKLIST_EXTS,
        ]

        with ScannerLifecycle(scan_batch, logger):
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # 過濾有效 URL
            valid_urls = set()
            for line in process.stdout:
                url_str = line.strip()
                if not url_str:
                    continue
                try:
                    parsed = urlparse(url_str)
                    if subdomain.name in parsed.hostname:
                        valid_urls.add(url_str)
                except Exception:
                    continue

            if not valid_urls:
                logger.info(f"Gau 未發現任何有效 URL for {subdomain.name}。")
                # 正常結束（0 results），lifecycle 仍會更新為 COMPLETED
                return f"GAU URL 掃描完成。子域名: {subdomain.name}（無結果）"

            logger.info(f"Gau 發現 {len(valid_urls)} 個有效 URL，開始入庫處理...")

            # 批量創建 URL
            new_objects = [
                URLResult(
                    url=url,
                    target=subdomain.target,
                    last_scan_type="passive_gau",
                    last_scan_id=scan_batch.id,
                )
                for url in valid_urls
            ]
            URLResult.objects.bulk_create(new_objects, ignore_conflicts=True)

            # 建立雙重關聯 (M2M)
            url_results = URLResult.objects.filter(url__in=valid_urls)
            subdomain.related_urls.add(*url_results)
            scan_batch.results.add(*url_results)

            logger.info(f"已關聯 {url_results.count()} 條 URL 到 Subdomain: {subdomain.name}")
            scan_batch.urls_found_count = len(valid_urls)
            scan_batch.save(update_fields=["urls_found_count"])

            logger.info(
                f"被動 URL 掃描完成 for {subdomain.name}。共處理 {len(valid_urls)} 條 URL。"
            )

    except Subdomain.DoesNotExist:
        logger.error(f"任務中止：找不到 Subdomain ID: {subdomain_id}")
    except Exception as e:
        logger.error(f"被動 URL 掃描失敗 for subdomain ID {subdomain_id}: {e}")
    finally:
        # 清理臨時配置文件
        if config_file and os.path.exists(config_file):
            os.remove(config_file)
            logger.debug(f"已清理 gau 臨時配置文件: {config_file}")

    return f"GAU URL 掃描完成。子域名: {subdomain.name if 'subdomain' in locals() else 'Unknown'}"
