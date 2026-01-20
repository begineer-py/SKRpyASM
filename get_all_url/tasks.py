# get_all_url/tasks.py

import logging
import subprocess
from urllib.parse import urlparse
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from c2_core.config.logging import log_function_call
from core.models import Subdomain, URLScan, URLResult

logger = logging.getLogger(__name__)

BLACKLIST_EXTS = "png,jpg,jpeg,gif,webp,svg,ico,css,js,woff,woff2,ttf,eot,mp4,mp3,pdf"


@shared_task(bind=True)
@log_function_call()
def scan_all_url(self, subdomain_id: int, threads: int = 50):
    try:
        subdomain = Subdomain.objects.prefetch_related("which_seed").get(
            id=subdomain_id
        )
        seed_values = ",".join([s.value for s in subdomain.which_seed.all()])
        logger.info(f"开始对 {subdomain.name} (Seeds: {seed_values}) 进行被动 URL 扫描")

        # === 修正點 1: 適配新的 URLScan 模型 ===
        # 使用 target_subdomain，並標記工具為 gau
        scan_batch = URLScan.objects.create(
            target_subdomain=subdomain, tool="gau", status="RUNNING"
        )

        command = [
            "docker",
            "run",
            "--rm",
            "sxcurity/gau:latest",
            subdomain.name,
            "--threads",
            str(threads),
            "--blacklist",
            BLACKLIST_EXTS,
        ]

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # === 數據過濾邏輯 ===
        valid_urls = set()
        for line in process.stdout:
            url_str = line.strip()
            if not url_str:
                continue

            try:
                parsed = urlparse(url_str)
                # 寬鬆過濾：只要 hostname 包含子域名名字即可 (視需求調整)
                if subdomain.name in parsed.hostname:
                    valid_urls.add(url_str)
            except Exception:
                continue

        if not valid_urls:
            logger.info(f"Gau 未发现任何有效 URL for {subdomain.name}。")
            scan_batch.status = "COMPLETED"
            scan_batch.completed_at = timezone.now()
            scan_batch.save()
            return

        logger.info(f"Gau 发现 {len(valid_urls)} 个有效 URL，开始入库處理...")

        # === 修正點 2: 批量創建 URL (不帶外鍵) ===
        # 因為現在是 M2M，創建時不需要 (也不能) 指定 subdomain
        new_objects = []
        for url in valid_urls:
            new_objects.append(
                URLResult(
                    url=url,
                    last_scan_type="passive_gau",
                    last_scan_id=scan_batch.id,
                )
            )

        URLResult.objects.bulk_create(new_objects, ignore_conflicts=True)

        # === 修正點 3: 建立雙重關聯 (M2M) ===
        # 撈取這些 URL 對象
        url_results = URLResult.objects.filter(url__in=valid_urls)

        # 動作 A: 關聯到 Subdomain (資產歸屬 - M2M)
        subdomain.related_urls.add(*url_results)

        # 動作 B: 關聯到 Scan Task (任務產出 - M2M)
        scan_batch.results.add(*url_results)

        logger.info(
            f"已关联 {url_results.count()} 条 URL 到 Subdomain: {subdomain.name}"
        )

        # === 統計與收尾 ===
        scan_batch.urls_found_count = len(valid_urls)  # 更新統計
        scan_batch.status = "COMPLETED"
        scan_batch.completed_at = timezone.now()
        scan_batch.save()

        logger.info(
            f"被动 URL 扫描完成 for {subdomain.name}。共处理 {len(valid_urls)} 条 URL。"
        )

    except Subdomain.DoesNotExist:
        logger.error(f"任务中止：找不到 Subdomain ID: {subdomain_id}")
    except Exception as e:
        logger.error(f"被动 URL 扫描失败 for subdomain ID {subdomain_id}: {e}")
        if "scan_batch" in locals() and scan_batch:
            URLScan.objects.filter(id=scan_batch.id).update(
                status="FAILED", completed_at=timezone.now(), error_message=str(e)
            )
