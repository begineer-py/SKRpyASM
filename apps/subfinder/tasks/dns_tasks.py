import logging
import subprocess
import json
from celery import shared_task
from django.db import transaction

from apps.core.models import Subdomain, Seed
from c2_core.config.logging import log_function_call
from .utils import ensure_seed_subdomain_exists, create_or_update_ip_objects

logger = logging.getLogger(__name__)


@log_function_call()
@shared_task(bind=True, ignore_result=True)
def resolve_dns_for_seed(self, seed_id: int, subfinder_scan_id: int):
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
            # Continue to next task even if DNS resolution fails
            from .protection_tasks import check_protection_for_seed
            check_protection_for_seed.delay(seed_id, subfinder_scan_id)
            return

        raw_output = process.stdout.strip()
        lines = raw_output.split("\n") if raw_output else []

        updates_count = 0
        resolved_hosts = set()

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

                    # Only consider resolution successful if there are A, AAAA, or CNAME records
                    if not (ipv4_list or ipv6_list or cname_list):
                        continue

                    sub_obj = subdomain_map.get(host)
                    if sub_obj:
                        resolved_hosts.add(host)

                        # Handle IP addresses
                        all_ips = create_or_update_ip_objects(ipv4_list, ipv6_list, seed)

                        # Associate IPs with subdomain
                        if hasattr(sub_obj, "ips"):
                            sub_obj.ips.add(*all_ips)

                        # Update subdomain status
                        sub_obj.is_resolvable = True
                        sub_obj.cname = ",".join(cname_list)
                        sub_obj.dns_records = data
                        sub_obj.save(
                            update_fields=["is_resolvable", "cname", "dns_records"]
                        )
                        updates_count += 1

                except Exception as e:
                    logger.error(f"解析 dnsx 行失敗: {e}")

        # Mark unresolved domains
        unresolved_hosts = set(subdomain_map.keys()) - resolved_hosts
        if unresolved_hosts:
            logger.info(f"標記 {len(unresolved_hosts)} 個子域名為不可解析。")
            Subdomain.objects.filter(
                which_seed=seed, name__in=unresolved_hosts, is_resolvable=True
            ).update(is_resolvable=False)

        logger.info(
            f"DNS 解析完成。成功解析: {updates_count}, 失敗: {len(unresolved_hosts)}。"
        )

    except Exception as e:
        logger.exception(f"DNS 解析出錯: {e}")
    finally:
        # Continue to next task regardless of success/failure
        from .protection_tasks import check_protection_for_seed
        check_protection_for_seed.delay(
            seed_id=seed_id, subfinder_scan_id=subfinder_scan_id
        )
