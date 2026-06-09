import asyncio
import json
import logging
import subprocess
from typing import Optional

from asgiref.sync import sync_to_async
from celery import shared_task

from apps.core.models import Subdomain, Seed
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)

_CDNCHECK_COMMAND = ["cdncheck", "-jsonl", "-silent"]


async def _run_cdncheck_on_chunk(chunk: list[str]) -> list[str]:
    input_data = "\n".join(chunk).encode()
    try:
        proc = await asyncio.create_subprocess_exec(
            *_CDNCHECK_COMMAND,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=input_data), timeout=300)
        if proc.returncode == 0:
            return [line for line in stdout.decode().strip().split("\n") if line]
        else:
            logger.error(f"cdncheck 批次執行失敗: {stderr.decode()}")
            return []
    except Exception as e:
        logger.error(f"cdncheck 批次執行異常: {e}")
        return []


async def _run_all_chunks(chunks: list[list[str]]) -> list[str]:
    results = await asyncio.gather(*[_run_cdncheck_on_chunk(c) for c in chunks])
    return [line for chunk_lines in results for line in chunk_lines]


@shared_task(bind=True, ignore_result=True)
async def check_protection_for_seed(
    self,
    seed_id: int,
    subfinder_scan_id: int,
    chunk_size: int = 100,
    greenpool_size: int = 20,
    execution_graph_id: Optional[int] = None,
    execution_node_id: Optional[int] = None,
):
    """Check CDN/WAF protection for all resolvable subdomains of a seed."""
    seed = None
    try:
        def _fetch_seed_and_subdomains():
            s = Seed.objects.get(id=seed_id)
            subs = list(
                Subdomain.objects.filter(
                    which_seed=s, is_active=True, is_resolvable=True
                )
            )
            return s, subs

        seed, subdomains_to_check = await sync_to_async(_fetch_seed_and_subdomains)()
        logger.info(f"開始 CDN/WAF 檢測 for Seed: '{seed.value}' (ExecutionNode: {execution_node_id})")

        if not subdomains_to_check:
            logger.info("沒有需要檢測 CDN/WAF 的子域名。")
            await _complete_execution_node(
                execution_node_id,
                content=f"Subfinder 偵察鏈完成。種子: {seed.value}（無 CDN/WAF 檢測目標）",
                output={"updated_count": 0},
            )
            return

        subdomain_map = {sub.name: sub for sub in subdomains_to_check}
        all_names = list(subdomain_map.keys())
        chunks = [
            all_names[i : i + chunk_size] for i in range(0, len(all_names), chunk_size)
        ]

        logger.info(f"将 {len(all_names)} 個子域名分成 {len(chunks)} 批進行連發檢測。")

        all_lines = await _run_all_chunks(chunks)

        to_update = []
        for line in all_lines:
            try:
                data = json.loads(line)
                host = data.get("input")
                if host in subdomain_map:
                    sub_obj = subdomain_map[host]
                    is_cdn = data.get("cdn", False)
                    is_waf = data.get("waf", False)
                    cdn_name = data.get("cdn_name")
                    waf_name = data.get("waf_name")

                    if (
                        sub_obj.is_cdn != is_cdn
                        or sub_obj.is_waf != is_waf
                        or sub_obj.cdn_name != cdn_name
                        or sub_obj.waf_name != waf_name
                    ):
                        sub_obj.is_cdn, sub_obj.is_waf = is_cdn, is_waf
                        sub_obj.cdn_name, sub_obj.waf_name = cdn_name, waf_name
                        sub_obj.last_scan_type = "CdnCheckScan"
                        sub_obj.last_scan_id = subfinder_scan_id
                        to_update.append(sub_obj)
            except (json.JSONDecodeError, KeyError):
                pass

        if to_update:
            await sync_to_async(
                lambda: Subdomain.objects.bulk_update(
                    to_update,
                    ['is_cdn', 'is_waf', 'cdn_name', 'waf_name', 'last_scan_type', 'last_scan_id'],
                    batch_size=500,
                )
            )()

        updates_count = len(to_update)
        logger.info(f"CDN/WAF 檢測完成。共更新 {updates_count} 個子域名的信息。")
        await _complete_execution_node(
            execution_node_id,
            content=f"Subfinder 偵察鏈完成。種子: {seed.value}，CDN/WAF 更新 {updates_count} 筆。",
            output={"updated_count": updates_count, "checked_count": len(subdomains_to_check)},
        )

    except Exception as e:
        logger.exception(f"CDN/WAF 檢測任務 for Seed ID {seed_id} 失敗: {e}")
        await _fail_execution_node(
            execution_node_id,
            content=f"Subfinder CDN/WAF 檢測失敗。Seed ID: {seed_id}: {e}",
            error={"error_type": type(e).__name__, "message": str(e)},
        )
    finally:
        return f"Subfinder 偵察鏈完成。種子: {seed.value if seed else 'Unknown'}"


async def _complete_execution_node(execution_node_id: Optional[int], *, content: str, output: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    await sync_to_async(ExecutionService.complete_node_by_id)(execution_node_id, output=output, content=content)


async def _fail_execution_node(execution_node_id: Optional[int], *, content: str, error: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    await sync_to_async(ExecutionService.fail_node_by_id)(execution_node_id, content=content, error=error)
