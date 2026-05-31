import logging
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class AssetCreationMixin:
    """
    Asset Creation Tools Mixin
    Provides tools for registering newly discovered assets (URLs, subdomains, IPs) in the database.
    """

    @method_tool
    def create_discovered_url(self, target_id: int, url: str, discovery_source: str = "API", subdomain_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新 URL（如隱藏的 API 端點、管理面板路徑等），
        使用此工具將它登記進資料庫，以便後續掃描器自動對其進行抓取與漏洞掃描。

        Args:
            target_id: 此 URL 所屬的 Target ID。
            url: 完整的 URL（如 'https://example.com/admin/api/users'）。
            discovery_source: 發現來源 ('SCAN', 'CRAWL_html', 'JS_EXT', 'BRUTE', 'API')。預設 'API'。
            subdomain_id: (選填) 關聯的 Subdomain ID。
        """
        try:
            from apps.core.models.url_assets import URLResult

            existing = URLResult.objects.filter(url=url, target_id=target_id).first()
            if existing:
                return f"URL 已存在: ID={existing.id}, url={existing.url}, fetch_status={existing.content_fetch_status}。不需要重複建立。"

            url_obj = URLResult.objects.create(
                target_id=target_id,
                url=url,
                discovery_source=discovery_source,
                content_fetch_status="PENDING",
            )
            if subdomain_id:
                url_obj.related_subdomains.add(subdomain_id)

            return (
                f"✅ 新 URL 已登記: ID={url_obj.id}, url={url_obj.url}。\n"
                f"系統將在下一個排程週期自動使用 Flaresolverr 抓取此 URL 的內容。"
            )
        except Exception as e:
            logger.error(f"create_discovered_url failed: {e}")
            return f"建立 URL 資產失敗: {e}"

    @method_tool
    def create_discovered_subdomain(self, target_id: int, name: str, seed_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新子域名（如從 JS 檔案、API 回應中提取），
        使用此工具將它登記進資料庫，以便後續自動進行 DNS 解析、技術分析與漏洞掃描。

        Args:
            target_id: 此子域名所屬的 Target ID。
            name: 子域名名稱（如 'api.example.com'）。
            seed_id: (選填) 發現此子域名的 Seed ID，會自動建立關聯。
        """
        try:
            from apps.core.models.domain import Subdomain, SubdomainSeed

            existing = Subdomain.objects.filter(name=name, target_id=target_id).first()
            if existing:
                return f"子域名已存在: ID={existing.id}, name={existing.name}, resolvable={existing.is_resolvable}。不需要重複建立。"

            sub = Subdomain.objects.create(
                target_id=target_id,
                name=name,
                is_active=True,
                is_resolvable=True,  # 預設可解析，後續掃描器再驗證
                sources_text="AI_DISCOVERY",
            )
            if seed_id:
                SubdomainSeed.objects.get_or_create(subdomain=sub, seed_id=seed_id)

            return (
                f"✅ 新子域名已登記: ID={sub.id}, name={sub.name}。\n"
                f"系統將在下一個排程週期自動進行 DNS 解析與技術棧偵測。"
            )
        except Exception as e:
            logger.error(f"create_discovered_subdomain failed: {e}")
            return f"建立子域名資產失敗: {e}"

    @method_tool
    def create_discovered_ip(self, target_id: int, address: str, seed_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新 IP 位址（如從 DNS 解析、API 回應中提取），
        使用此工具將它登記進資料庫，以便後續自動進行端口掃描與漏洞分析。

        Args:
            target_id: 此 IP 所屬的 Target ID。
            address: IP 位址字串（如 '192.168.1.1' 或 '2001:db8::1'）。
            seed_id: (選填) 發現此 IP 的 Seed ID。
        """
        try:
            from apps.core.models.network import IP

            existing = IP.objects.filter(address=address, target_id=target_id).first()
            if existing:
                return f"IP 已存在: ID={existing.id}, address={existing.address}。不需要重複建立。"

            version = 6 if ':' in address else 4
            ip_obj = IP.objects.create(
                target_id=target_id,
                address=address,
                version=version,
            )
            if seed_id:
                ip_obj.which_seed.add(seed_id)

            return (
                f"✅ 新 IP 已登記: ID={ip_obj.id}, address={ip_obj.address} (IPv{version})。\n"
                f"系統將在下一個排程週期自動使用 Nmap 掃描此 IP 的端口。"
            )
        except Exception as e:
            logger.error(f"create_discovered_ip failed: {e}")
            return f"建立 IP 資產失敗: {e}"
