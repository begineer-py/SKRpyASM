import logging
from typing import Dict, Any, Optional, List
from .base import BaseCVEClient

logger = logging.getLogger(__name__)


class CISAKEVClient(BaseCVEClient):
    """
    CISA KEV (Known Exploited Vulnerabilities) 客戶端
    文件：https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    """

    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    def __init__(self, timeout: int = 30):
        """初始化 CISA KEV 客戶端（無需 API key）"""
        super().__init__(api_key=None, timeout=timeout)
        self._kev_cache: Optional[Dict[str, Dict[str, Any]]] = None

    async def fetch_kev_catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        抓取完整的 CISA KEV 目錄

        Returns:
            以 CVE ID 為 key 的字典
        """
        try:
            response = await self._make_request(
                method="GET",
                url=self.KEV_URL,
                headers={"Content-Type": "application/json"},
            )

            vulnerabilities = response.get("vulnerabilities", [])
            kev_dict = {}

            for vuln in vulnerabilities:
                cve_id = vuln.get("cveID", "").upper()
                if cve_id:
                    kev_dict[cve_id] = {
                        "cve_id": cve_id,
                        "vendor_project": vuln.get("vendorProject", ""),
                        "product": vuln.get("product", ""),
                        "vulnerability_name": vuln.get("vulnerabilityName", ""),
                        "date_added": vuln.get("dateAdded", ""),
                        "short_description": vuln.get("shortDescription", ""),
                        "required_action": vuln.get("requiredAction", ""),
                        "due_date": vuln.get("dueDate", ""),
                        "known_ransomware_use": vuln.get("knownRansomwareCampaignUse", "Unknown"),
                        "notes": vuln.get("notes", ""),
                    }

            self._kev_cache = kev_dict
            logger.info(f"Fetched {len(kev_dict)} CVEs from CISA KEV catalog")
            return kev_dict

        except Exception as e:
            logger.error(f"Error fetching CISA KEV catalog: {e}")
            return {}

    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        查詢特定 CVE 是否在 CISA KEV 清單中

        Args:
            cve_id: CVE 編號

        Returns:
            KEV 資料，若不在清單中則返回 None
        """
        if not self._kev_cache:
            await self.fetch_kev_catalog()

        cve_id_upper = cve_id.upper()
        return self._kev_cache.get(cve_id_upper) if self._kev_cache else None

    async def search_cves(
        self,
        keyword: Optional[str] = None,
        vendor: Optional[str] = None,
        product: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜尋 CISA KEV 清單

        Args:
            keyword: 關鍵字搜尋（在描述中搜尋）
            vendor: 廠商名稱
            product: 產品名稱

        Returns:
            符合條件的 KEV 清單
        """
        if not self._kev_cache:
            await self.fetch_kev_catalog()

        if not self._kev_cache:
            return []

        results = []
        for kev_data in self._kev_cache.values():
            # 關鍵字過濾
            if keyword:
                keyword_lower = keyword.lower()
                if not any([
                    keyword_lower in kev_data.get("vulnerability_name", "").lower(),
                    keyword_lower in kev_data.get("short_description", "").lower(),
                    keyword_lower in kev_data.get("product", "").lower(),
                ]):
                    continue

            # 廠商過濾
            if vendor:
                if vendor.lower() not in kev_data.get("vendor_project", "").lower():
                    continue

            # 產品過濾
            if product:
                if product.lower() not in kev_data.get("product", "").lower():
                    continue

            results.append(kev_data)

        return results

    async def check_cves_in_kev(self, cve_ids: List[str]) -> Dict[str, bool]:
        """
        批次檢查多個 CVE 是否在 KEV 清單中

        Args:
            cve_ids: CVE ID 清單

        Returns:
            以 CVE ID 為 key，是否在 KEV 中為 value 的字典
        """
        if not self._kev_cache:
            await self.fetch_kev_catalog()

        result = {}
        for cve_id in cve_ids:
            cve_id_upper = cve_id.upper()
            result[cve_id_upper] = cve_id_upper in (self._kev_cache or {})

        return result
