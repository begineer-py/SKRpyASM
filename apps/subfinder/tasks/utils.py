import logging
import json
from collections import defaultdict
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


def parse_subfinder_output(raw_output):
    """Parse subfinder JSON output into a dictionary mapping subdomains to sources."""
    current_subdomains_map = defaultdict(set)

    if not raw_output:
        return current_subdomains_map

    lines = raw_output.split("\n")
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        try:
            data = json.loads(clean_line)
            subdomain = data.get("host")
            if subdomain:
                current_subdomains_map[subdomain].add(data.get("source"))
        except json.JSONDecodeError:
            logger.warning(f"無法解析 JSON 格式: {clean_line}")

    return current_subdomains_map


def update_subdomain_assets(seed, current_subdomains_map, scan):
    """Update subdomain assets based on current scan results."""
    current_subdomains_set = set(current_subdomains_map.keys())

    # Import here to avoid circular imports
    from apps.core.models.assets import Subdomain

    known_subdomains_qs = Subdomain.objects.filter(which_seed=seed)
    known_subdomains_map = {s.name: s for s in known_subdomains_qs}
    known_subdomains_set = set(known_subdomains_map.keys())

    new_subdomain_names = current_subdomains_set - known_subdomains_set
    reactivated_names = current_subdomains_set.intersection(known_subdomains_set)
    missing_names = known_subdomains_set - current_subdomains_set

    with transaction.atomic():
        # Create new subdomains
        for name in new_subdomain_names:
            sources_set = current_subdomains_map[name]
            sub_obj = Subdomain.objects.create(
                name=name,
                is_active=True,
                sources_text=",".join(sorted(list(sources_set))),
                last_scan_type="SubfinderScan",
                last_scan_id=scan.id,
            )
            sub_obj.which_seed.add(seed)

        # Update existing subdomains
        for name in reactivated_names:
            sub_obj = known_subdomains_map[name]
            existing_sources = set(
                sub_obj.sources_text.split(",") if sub_obj.sources_text else []
            )
            new_sources = current_subdomains_map[name]
            combined_sources = existing_sources.union(new_sources)
            new_sources_str = ",".join(sorted(list(combined_sources)))

            update_fields_list = []
            if not sub_obj.is_active:
                sub_obj.is_active = True
                update_fields_list.append("is_active")
            if new_sources_str != sub_obj.sources_text:
                sub_obj.sources_text = new_sources_str
                update_fields_list.append("sources_text")

            sub_obj.last_seen = timezone.now()
            sub_obj.last_scan_type = "SubfinderScan"
            sub_obj.last_scan_id = scan.id
            update_fields_list.extend(["last_seen", "last_scan_type", "last_scan_id"])

            if update_fields_list:
                sub_obj.save(update_fields=update_fields_list)

        # Mark missing subdomains as inactive
        if missing_names:
            Subdomain.objects.filter(
                which_seed=seed, name__in=missing_names, is_active=True
            ).update(is_active=False)
            seed_sub, _ = Subdomain.objects.get_or_create(
                name=seed.value,
                defaults={"is_active": True, "sources_text": "seed_self"},
            )
            if not seed_sub.is_active:
                seed_sub.is_active = True
                seed_sub.save(update_fields=["is_active"])
            seed_sub.which_seed.add(seed)

    return {
        "new_count": len(new_subdomain_names),
        "reactivated_count": len(reactivated_names),
        "missing_count": len(missing_names),
    }


def ensure_seed_subdomain_exists(seed):
    """Ensure the seed itself exists as a subdomain record."""
    from apps.core.models.assets import Subdomain

    seed_sub, created = Subdomain.objects.get_or_create(
        name=seed.value,
        defaults={"is_active": True, "sources_text": "seed_self"},
    )
    if not seed_sub.is_active:
        seed_sub.is_active = True
        seed_sub.save(update_fields=["is_active"])
    seed_sub.which_seed.add(seed)
    return seed_sub


def create_or_update_ip_objects(ipv4_list, ipv6_list, seed):
    """Create or update IP objects and associate them with seed."""
    from apps.core.models.assets import IP

    all_ips = []
    for ip_val in ipv4_list:
        ip_obj, _ = IP.objects.get_or_create(ipv4=ip_val)
        ip_obj.which_seed.add(seed)
        all_ips.append(ip_obj)
    for ip_val in ipv6_list:
        ip_obj, _ = IP.objects.get_or_create(ipv6=ip_val)
        ip_obj.which_seed.add(seed)
        all_ips.append(ip_obj)

    return all_ips


# {"name":"owasp.com","domain":"owasp.com","addresses":[{"ip":"104.20.29.134","cidr":"104.20.16.0/20","asn":13335,"desc":"CLOUDFLARENET - Cloudflare, Inc., US"},{"ip":"172.66.159.45","cidr":"172.66.144.0/20","asn":13335,"desc":"CLOUDFLARENET - Cloudflare, Inc., US"}],"tag":"cert","sources":["DNS","Bing","Yahoo","HyperStat","CertSpotter","Mnemonic","DNSSpy","HAW","Crtsh","Google","RapidDNS"]}


def parse_amass_output(raw_output):
    """Parse amass JSON output into a dictionary mapping subdomains to sources."""
    current_subdomains_map = defaultdict(set)

    if not raw_output:
        return current_subdomains_map

    lines = raw_output.split("\n")
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        try:
            data = json.loads(clean_line)
            subdomain = data.get("name")
            if subdomain:
                current_subdomains_map[subdomain].add(data.get("sources"))
        except json.JSONDecodeError:
            logger.warning(f"無法解析 JSON 格式: {clean_line}")

    return current_subdomains_map
