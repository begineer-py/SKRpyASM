# apps/subfinder/tasks/utils.py
# 子域名掃描工具函數與資產更新邏輯

import logging
import json
from collections import defaultdict
from django.utils import timezone
from django.db import transaction

# 初始化日誌記錄器
logger = logging.getLogger(__name__)


def parse_subfinder_output(raw_output):
    """
    解析 subfinder 的 JSON 輸出，轉換為子域名與其來源的映射字典。

    參數:
        raw_output (str): subfinder 執行的原始字串輸出 (通常是多行 JSON)。

    回傳:
        defaultdict(set): 鍵為子域名 (host)，值為來源 (source) 的集合。
    """
    current_subdomains_map = defaultdict(set)

    if not raw_output:
        return current_subdomains_map

    # 按行切割並過濾空行
    lines = raw_output.split("\n")
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        try:
            # 解析單行 JSON，提取 host 與 source
            data = json.loads(clean_line)
            subdomain = data.get("host")
            if subdomain:
                current_subdomains_map[subdomain].add(data.get("source"))
        except json.JSONDecodeError:
            logger.warning(f"無法解析 JSON 格式: {clean_line}")

    return current_subdomains_map


def update_subdomain_assets(seed, current_subdomains_map, scan):
    """
    根據當前掃描結果更新子域名資產。

    此函數會與資料庫中的現有資產進行比對，自動處理：
    1. 新增子域名 (New)
    2. 重新啟用/更新已存在的子域名 (Reactivated)
    3. 標記消失的子域名為不活動 (Missing)

    參數:
        seed: 當前的種子對象 (Seed model instance)。
        current_subdomains_map: 此次掃描發現的子域名映射。
        scan: 當前的掃描紀錄物件。
    """
    current_subdomains_set = set(current_subdomains_map.keys())

    # 在函數內導入以避免循環導入 (Circular Import)
    from apps.core.models import Subdomain, SubdomainSeed

    # 獲取該種子下已知的所有子域名
    known_subdomains_qs = Subdomain.objects.filter(which_seed=seed)
    known_subdomains_map = {s.name: s for s in known_subdomains_qs}
    known_subdomains_set = set(known_subdomains_map.keys())

    # 使用集合運算找出差異
    new_subdomain_names = current_subdomains_set - known_subdomains_set
    reactivated_names = current_subdomains_set.intersection(known_subdomains_set)
    missing_names = known_subdomains_set - current_subdomains_set

    # 使用事務原子性確保資料一致性
    with transaction.atomic():
        # 1. 批次建立新發現的子域名
        new_subdomains = []
        for name in new_subdomain_names:
            sources_set = current_subdomains_map[name]
            sub_obj = Subdomain(
                name=name,
                is_active=True,
                sources_text=",".join(sorted(list(sources_set))),
                last_scan_type="SubfinderScan",
                last_scan_id=scan.id,
            )
            new_subdomains.append(sub_obj)

        if new_subdomains:
            # bulk_create 比逐個 create 快得多
            created_subdomains = Subdomain.objects.bulk_create(new_subdomains)
            # 建立多對多關聯 (Through model)
            SubdomainSeed.objects.bulk_create(
                [SubdomainSeed(subdomain=sub, seed=seed) for sub in created_subdomains]
            )

        # 2. 批次更新已存在的子域名
        updated_subdomains = []
        for name in reactivated_names:
            sub_obj = known_subdomains_map[name]
            existing_sources = set(
                sub_obj.sources_text.split(",") if sub_obj.sources_text else []
            )
            new_sources = current_subdomains_map[name]
            # 合併新舊來源
            combined_sources = existing_sources.union(new_sources)
            new_sources_str = ",".join(sorted(list(combined_sources)))

            update_fields_list = []
            # 如果原本是不活動，則重新設為活動
            if not sub_obj.is_active:
                sub_obj.is_active = True
                update_fields_list.append("is_active")
            # 如果來源有更新
            if new_sources_str != sub_obj.sources_text:
                sub_obj.sources_text = new_sources_str
                update_fields_list.append("sources_text")

            # 更新掃描紀錄資訊
            sub_obj.last_seen = timezone.now()
            sub_obj.last_scan_type = "SubfinderScan"
            sub_obj.last_scan_id = scan.id
            update_fields_list.extend(["last_seen", "last_scan_type", "last_scan_id"])

            if update_fields_list:
                updated_subdomains.append(sub_obj)

        if updated_subdomains:
            # 使用 bulk_update 減少資料庫交互次數
            Subdomain.objects.bulk_update(
                updated_subdomains,
                [
                    "is_active",
                    "sources_text",
                    "last_seen",
                    "last_scan_type",
                    "last_scan_id",
                ],
            )

        # 3. 標記此次掃描未發現但原本存在的子域名為「不活動」
        if missing_names:
            Subdomain.objects.filter(
                which_seed=seed, name__in=missing_names, is_active=True
            ).update(is_active=False)

        # 4. 確保種子本身也作為一個子域名記錄存在 (Self-referencing)
        seed_sub, created = Subdomain.objects.get_or_create(
            name=seed.value,
            defaults={"is_active": True, "sources_text": "seed_self"},
        )
        if not seed_sub.is_active:
            seed_sub.is_active = True
            seed_sub.save(update_fields=["is_active"])
        if (
            created
            or not SubdomainSeed.objects.filter(subdomain=seed_sub, seed=seed).exists()
        ):
            SubdomainSeed.objects.get_or_create(subdomain=seed_sub, seed=seed)

    return {
        "new_count": len(new_subdomain_names),
        "reactivated_count": len(reactivated_names),
        "missing_count": len(missing_names),
    }


def ensure_seed_subdomain_exists(seed):
    """
    確保種子本身在子域名模型中有一條對應記錄。

    參數:
        seed: 種子模型實例。

    回傳:
        seed_sub: 子域名模型實例。
    """
    from apps.core.models import Subdomain, SubdomainSeed

    # 檢查或建立
    seed_sub, created = Subdomain.objects.get_or_create(
        name=seed.value,
        defaults={"is_active": True, "sources_text": "seed_self"},
    )
    # 如果已存在但被標記為不活動，重新啟用
    if not seed_sub.is_active:
        seed_sub.is_active = True
        seed_sub.save(update_fields=["is_active"])

    # 建立多對多關聯
    if not SubdomainSeed.objects.filter(subdomain=seed_sub, seed=seed).exists():
        SubdomainSeed.objects.create(subdomain=seed_sub, seed=seed)
    return seed_sub


def create_or_update_ip_objects(ipv4_list, ipv6_list, seed):
    """
    建立或更新 IP 物件，並將其與種子關聯。

    參數:
        ipv4_list (list): IPv4 地址列表。
        ipv6_list (list): IPv6 地址列表。
        seed: 種子物件。

    回傳:
        all_ips (list): 處理後的 IP 物件列表。
    """
    from apps.core.models import IP

    # --- 處理 IPv4 ---
    # 先一次性查找現有的 IP，避免在循環中進行資料庫查詢
    existing_ipv4 = {ip.ipv4: ip for ip in IP.objects.filter(ipv4__in=ipv4_list)}
    new_ipv4_objs = []
    for ip_val in ipv4_list:
        if ip_val not in existing_ipv4:
            new_ipv4_objs.append(IP(ipv4=ip_val))

    # 批次建立新的 IPv4 撥錄
    if new_ipv4_objs:
        created_ipv4 = IP.objects.bulk_create(new_ipv4_objs)
        for ip in created_ipv4:
            existing_ipv4[ip.ipv4] = ip

    # --- 處理 IPv6 ---
    existing_ipv6 = {ip.ipv6: ip for ip in IP.objects.filter(ipv6__in=ipv6_list)}
    new_ipv6_objs = []
    for ip_val in ipv6_list:
        if ip_val not in existing_ipv6:
            new_ipv6_objs.append(IP(ipv6=ip_val))

    # 批次建立新的 IPv6 紀錄
    if new_ipv6_objs:
        created_ipv6 = IP.objects.bulk_create(new_ipv6_objs)
        for ip in created_ipv6:
            existing_ipv6[ip.ipv6] = ip

    all_ips = list(existing_ipv4.values()) + list(existing_ipv6.values())
    ThroughModel = IP.which_seed.through
    existing_relations = set(
        ThroughModel.objects.filter(
            seed_id=seed.id, ip_id__in=[ip.id for ip in all_ips]
        ).values_list("ip_id", flat=True)
    )
    new_relations = [
        ThroughModel(seed_id=seed.id, ip_id=ip_id)
        for ip_id in [ip.id for ip in all_ips]
        if ip_id not in existing_relations
    ]  # 將所有 IP 與種子建立關聯
    if new_relations:
        with transaction.atomic():
            ThroughModel.objects.bulk_create(new_relations, ignore_conflicts=True)

            # 2. 【核心替代方案】手動批次同步 Target
            # 既然訊號沒觸發，我們就自己來。
            # 找出這批 IP 裡還沒有 target 的，直接一次性更新為 seed 的 target
            IP.objects.filter(
                id__in=[ip.id for ip in all_ips], target__isnull=True
            ).update(target=seed.target)

    return all_ips


# {"name":"owasp.com","domain":"owasp.com","addresses":[{"ip":"104.20.29.134","cidr":"104.20.16.0/20","asn":13335,"desc":"CLOUDFLARENET - Cloudflare, Inc., US"},{"ip":"172.66.159.45","cidr":"172.66.144.0/20","asn":13335,"desc":"CLOUDFLARENET - Cloudflare, Inc., US"}],"tag":"cert","sources":["DNS","Bing","Yahoo","HyperStat","CertSpotter","Mnemonic","DNSSpy","HAW","Crtsh","Google","RapidDNS"]}


def parse_amass_output(raw_output):
    """
    解析 amass 的 JSON 輸出，轉換為子域名與其來源的映射字典。

    參數:
        raw_output (str): amass 執行的原始字串輸出。

    回傳:
        defaultdict(set): 鍵為子域名，值為來源名稱的集合。
    """
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
                # amass 的輸出結構略有不同，sources 可能是一個列表或單一字串
                sources = data.get("sources")
                if isinstance(sources, list):
                    for s in sources:
                        current_subdomains_map[subdomain].add(s)
                else:
                    current_subdomains_map[subdomain].add(sources)
        except json.JSONDecodeError:
            logger.warning(f"無法解析 JSON 格式: {clean_line}")

    return current_subdomains_map
