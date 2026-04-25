import logging
import subprocess
import json
from celery import shared_task
from django.db import transaction
from typing import Optional

from apps.core.models import Subdomain, Seed
from c2_core.config.logging import log_function_call
from .utils import ensure_seed_subdomain_exists, create_or_update_ip_objects

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
@log_function_call()
def resolve_dns_for_seed(self, seed_id: int, subfinder_scan_id: int, callback_step_id: Optional[int] = None):
    """Resolve DNS for all subdomains associated with a seed."""
    try:
        seed = Seed.objects.get(id=seed_id)
        logger.info(f"開始 DNS 解析 for Seed: '{seed.value}'")

        subdomains_qs = Subdomain.objects.filter(which_seed=seed, is_active=True)
        subdomain_map = {sub.name: sub for sub in subdomains_qs}

        # Ensure seed itself is in the check list
        if seed.value not in subdomain_map:
            seed_sub = ensure_seed_subdomain_exists(seed)
            subdomain_map[seed.value] = seed_sub

        dnsx_input_data = "\n".join(subdomain_map.keys())
        command = ["dnsx", "-a", "-aaaa", "-cname", "-json", "-silent"]
        
        process = subprocess.run(
            command, input=dnsx_input_data, capture_output=True, text=True, timeout=600
        )

        if process.returncode != 0:
            logger.error(f"dnsx 失敗: {process.stderr}")
            from .protection_tasks import check_protection_for_seed
            check_protection_for_seed.delay(seed_id, subfinder_scan_id, callback_step_id=callback_step_id)
            return

        raw_output = process.stdout.strip()
        lines = raw_output.split("\n") if raw_output else []

        with transaction.atomic():
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    host = data.get("host")
                    ipv4_list = data.get("a", [])
                    ipv6_list = data.get("aaaa", [])
                    cname_list = data.get("cname", [])

                    if not (ipv4_list or ipv6_list or cname_list):
                        continue

                    sub_obj = subdomain_map.get(host)
                    if sub_obj:
                        all_ips = create_or_update_ip_objects(ipv4_list, ipv6_list, seed)
                        if hasattr(sub_obj, "ips"):
                            sub_obj.ips.add(*all_ips)

                        sub_obj.is_resolvable = True
                        sub_obj.save(update_fields=["is_resolvable"])
                        
                        # 解析並儲存至 DNSRecord 模型
                        from apps.core.models.domain import DNSRecord
                        dns_records_to_create = []
                        
                        for ipv4 in ipv4_list:
                             dns_records_to_create.append(DNSRecord(subdomain=sub_obj, record_type='A', value=ipv4))
                        for ipv6 in ipv6_list:
                             dns_records_to_create.append(DNSRecord(subdomain=sub_obj, record_type='AAAA', value=ipv6))
                        for cname in cname_list:
                             dns_records_to_create.append(DNSRecord(subdomain=sub_obj, record_type='CNAME', value=cname))
                             
                        if dns_records_to_create:
                            DNSRecord.objects.bulk_create(dns_records_to_create, ignore_conflicts=True)
                except Exception as e:
                    logger.error(f"解析 dnsx 行失敗: {e}")

    except Exception as e:
        logger.exception(f"DNS 解析出錯: {e}")
    finally:
        from .protection_tasks import check_protection_for_seed
        check_protection_for_seed.delay(
            seed_id=seed_id, subfinder_scan_id=subfinder_scan_id, callback_step_id=callback_step_id
        )
