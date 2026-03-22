import logging
import subprocess
import json
from typing import Optional
from celery import shared_task
from django.db import transaction
from eventlet.greenpool import GreenPool

from apps.core.models import Subdomain, Seed
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)


from apps.core.utils import with_auto_callback

@shared_task(bind=True, ignore_result=True)
@with_auto_callback
def check_protection_for_seed(
    self,
    seed_id: int,
    subfinder_scan_id: int,
    chunk_size: int = 100,
    greenpool_size: int = 20,
    callback_step_id: Optional[int] = None,
):
    """Check CDN/WAF protection for all resolvable subdomains of a seed."""
    seed = None
    try:
        seed = Seed.objects.get(id=seed_id)
        logger.info(f"開始 CDN/WAF 檢測 for Seed: '{seed.value}' (Step: {callback_step_id})")

        subdomains_to_check = Subdomain.objects.filter(
            which_seed=seed, is_active=True, is_resolvable=True
        )
        
        if not subdomains_to_check.exists():
            logger.info("沒有需要檢測 CDN/WAF 的子域名。")
            return

        # Prepare subdomain mapping and chunks
        subdomain_map = {sub.name: sub for sub in subdomains_to_check}
        all_names = list(subdomain_map.keys())
        chunks = [
            all_names[i : i + chunk_size] for i in range(0, len(all_names), chunk_size)
        ]

        command = [
            "cdncheck",
            "-jsonl",
            "-silent",
        ]
        
        logger.info(f"将 {len(all_names)} 個子域名分成 {len(chunks)} 批進行連發檢測。")

        def run_cdncheck_on_chunk(chunk):
            """Run cdncheck on a chunk of subdomains."""
            input_data = "\n".join(chunk)
            try:
                process = subprocess.run(
                    command, input=input_data, capture_output=True, text=True, timeout=300
                )
                if process.returncode == 0:
                    return [line for line in process.stdout.strip().split("\n") if line]
                else:
                    logger.error(f"cdncheck 批次執行失敗: {process.stderr}")
                    return []
            except Exception as e:
                logger.error(f"cdncheck 批次執行異常: {e}")
                return []

        # Execute cdncheck concurrently
        pool = GreenPool(size=greenpool_size)
        all_lines = []
        for lines_chunk in pool.imap(run_cdncheck_on_chunk, chunks):
            all_lines.extend(lines_chunk)

        updates_count = 0
        
        with transaction.atomic():
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

                        # Only update if values have changed
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

                            sub_obj.save()
                            updates_count += 1
                except (json.JSONDecodeError, KeyError):
                    pass
                    
        logger.info(f"CDN/WAF 檢測完成。共更新 {updates_count} 個子域名的信息。")
        
    except Exception as e:
        logger.exception(f"CDN/WAF 檢測任務 for Seed ID {seed_id} 失敗: {e}")
    finally:
        return f"Subfinder 偵察鏈完成。種子: {seed.value if seed else 'Unknown'}"
