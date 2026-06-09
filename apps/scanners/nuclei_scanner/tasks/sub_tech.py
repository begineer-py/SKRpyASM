import subprocess
from celery import shared_task
from c2_core.config.logging import log_function_call
import logging

logger = logging.getLogger(__name__)
from apps.core.models import Subdomain
from .utils import process_nuclei_tech_line
from apps.core.header_injection import get_tagged_headers


@shared_task(name="nuclei_scanner.tasks.sub_tech.scan_subdomain_tech")
@log_function_call()
def scan_subdomain_tech(subdomain_ids: list[int], target_id: int = None, execution_graph_id: int | None = None, execution_node_id: int | None = None):
    """
    掃描子域名的技術堆疊並解析結果
    """
    subdomains = Subdomain.objects.filter(id__in=subdomain_ids)

    if not target_id and subdomains.exists():
        resolved_target_id = subdomains.first().target_id
    else:
        resolved_target_id = target_id

    for subdomain in subdomains:
        logger.info(f"開始掃描子域名技術: {subdomain.name}")

        target_url = f"https://{subdomain.name}"
        command = [
            "nice",
            "nuclei",
            "-u",
            target_url,
            "-tags",
            "tech",
            "-jsonl",
            "-silent",
        ]

        tagged_headers = get_tagged_headers(target_id=resolved_target_id)
        for h_key, h_val in tagged_headers.items():
            command.extend(["-H", f"{h_key}: {h_val}"])

        from apps.core.header_injection import build_rate_limit_args
        command.extend(build_rate_limit_args("nuclei", resolved_target_id))

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

    result = f"已完成 {len(subdomains)} 個子域名的技術掃描"
    _complete_execution_node(execution_node_id, content=result)
    return result


def _complete_execution_node(execution_node_id: int | None, *, content: str) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.complete_node_by_id(execution_node_id, content=content)
