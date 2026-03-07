import subprocess
from celery import shared_task
from c2_core.config.logging import log_function_call
import logging

logger = logging.getLogger(__name__)
from apps.core.models import Subdomain
from .utils import process_nuclei_tech_line


@shared_task(name="nuclei_scanner.tasks.sub_tech.scan_subdomain_tech")
@log_function_call()
def scan_subdomain_tech(subdomain_ids: list[int]):
    """
    掃描子域名的技術堆疊並解析結果
    """
    subdomains = Subdomain.objects.filter(id__in=subdomain_ids)

    for subdomain in subdomains:
        logger.info(f"開始掃描子域名技術: {subdomain.name}")

        # 構建 Nuclei 指令 (輸出格式為 JSONL)
        target_url = f"https://{subdomain.name}"
        command = [
            "nice" "nuclei",
            "-u",
            target_url,
            "-tags",
            "tech",
            "-jsonl",
            "-silent",
        ]

        try:
            # 執行掃描
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # 逐行讀取輸出並解析
            for line in process.stdout:
                if line.strip():
                    process_nuclei_tech_line(line, subdomain)

            process.wait()

        except Exception as e:
            logger.error(f"執行 Nuclei 掃描失敗 ({subdomain.name}): {str(e)}")

    return f"已完成 {len(subdomains)} 個子域名的技術掃描"
