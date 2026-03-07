import subprocess
import logging
from celery import shared_task
from django.conf import settings
from apps.core.models import URLResult
from .utils import process_nuclei_tech_line  # 假設解析代碼放在 parsers.py

logger = logging.getLogger(__name__)


@shared_task(name="nuclei_scanner.tasks.url_tech.scan_url_tech_stack")
def scan_url_tech_stack(url_result_ids: list[int]):
    """
    針對指定的 URLResult 執行技術堆疊掃描
    """
    urls_to_scan = URLResult.objects.filter(id__in=url_result_ids)

    # 建議從設定檔讀取 Nuclei 模板路徑

    results_count = 0

    for url_res in urls_to_scan:
        logger.info(f"正在掃描 URL 技術堆疊: {url_res.url}")

        # 構建指令
        # -u: 目標 URL
        # -t: 技術檢測模板
        # -jsonl: 輸出 JSON Lines 格式
        # -irr: (選配) 儲存原始請求回應，如果需要更詳細資訊可加上
        command = [
            "nice",
            "nuclei",
            "-u",
            url_res.url,
            "-tags",
            "tech",
            "-jsonl",
            "-silent",
            "-nc",  # 禁用顏色輸出
        ]

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

    return f"完成 {results_count} 個 URL 的技術堆疊掃描"
