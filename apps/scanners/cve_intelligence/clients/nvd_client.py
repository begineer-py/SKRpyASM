import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseCVEClient

logger = logging.getLogger(__name__)


class NVDClient(BaseCVEClient):
    """
    NVD (National Vulnerability Database) API 2.0 客戶端
    文件：https://nvd.nist.gov/developers/vulnerabilities
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化 NVD 客戶端

        Args:
            api_key: NVD API key (選用，但強烈建議申請以提高速率限制)
                     無 key: 5 requests/30s
                     有 key: 50 requests/30s
            timeout: 請求超時時間（秒）
        """
        # 直接使用提供的 API key，不在 __init__ 中查詢資料庫
        # 資料庫查詢應該在調用方（CVEEnrichmentService）中完成
        super().__init__(api_key, timeout)

    @staticmethod
    def _get_api_key_from_db() -> Optional[str]:
        """
        從 APIKey 模型獲取 NVD API key

        注意：此方法已棄用，請在調用方使用 sync_to_async 包裝 get_rotated_key
        """
        try:
            from apps.api_keys.utils import get_rotated_key
            api_key = get_rotated_key("nvd")
            if api_key:
                logger.info("✅ 使用資料庫中的 NVD API Key（速率限制: 50 req/30s）")
            else:
                logger.warning("⚠️ 未找到 NVD API Key，使用無 key 模式（速率限制: 5 req/30s）")
            return api_key
        except Exception as e:
            logger.warning(f"無法從資料庫獲取 NVD API Key: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """取得請求標頭"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["apiKey"] = self.api_key
        return headers

    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        查詢特定 CVE ID 的詳細資訊

        Args:
            cve_id: CVE 編號 (例如 CVE-2024-12345)

        Returns:
            標準化的 CVE 資料，若不存在則返回 None
        """
        try:
            params = {"cveId": cve_id.upper()}
            response = await self._make_request(
                method="GET",
                url=self.BASE_URL,
                headers=self._get_headers(),
                params=params,
            )

            vulnerabilities = response.get("vulnerabilities", [])
            if not vulnerabilities:
                logger.warning(f"CVE {cve_id} not found in NVD")
                return None

            # 提取第一個結果
            cve_item = vulnerabilities[0].get("cve", {})
            return self._normalize_cve_data(cve_item)

        except Exception as e:
            logger.error(f"Error querying NVD for {cve_id}: {e}")
            return None

    async def search_cves(
        self,
        keyword: Optional[str] = None,
        cpe_name: Optional[str] = None,
        cvss_v3_severity: Optional[str] = None,
        pub_start_date: Optional[datetime] = None,
        pub_end_date: Optional[datetime] = None,
        results_per_page: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜尋 CVE

        Args:
            keyword: 關鍵字搜尋（在描述中搜尋）
            cpe_name: CPE 名稱 (例如 cpe:2.3:a:apache:struts:2.5.30:*:*:*:*:*:*:*)
            cvss_v3_severity: CVSS v3 嚴重性 (LOW, MEDIUM, HIGH, CRITICAL)
            pub_start_date: 發布日期起始
            pub_end_date: 發布日期結束
            results_per_page: 每頁結果數 (最大 2000)

        Returns:
            標準化的 CVE 清單
        """
        try:
            params = {"resultsPerPage": min(results_per_page, 2000)}

            if keyword:
                params["keywordSearch"] = keyword
            if cpe_name:
                params["cpeName"] = cpe_name
            if cvss_v3_severity:
                params["cvssV3Severity"] = cvss_v3_severity.upper()
            if pub_start_date:
                params["pubStartDate"] = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
            if pub_end_date:
                params["pubEndDate"] = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

            response = await self._make_request(
                method="GET",
                url=self.BASE_URL,
                headers=self._get_headers(),
                params=params,
            )

            vulnerabilities = response.get("vulnerabilities", [])
            return [
                self._normalize_cve_data(vuln.get("cve", {}))
                for vuln in vulnerabilities
            ]

        except Exception as e:
            logger.error(f"Error searching NVD: {e}")
            return []

    def _normalize_cve_data(self, cve_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 NVD API 回應標準化為統一格式

        Args:
            cve_item: NVD API 的 CVE 項目

        Returns:
            標準化的 CVE 資料
        """
        cve_id = cve_item.get("id", "")

        # 提取描述（優先英文）
        descriptions = cve_item.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        if not description and descriptions:
            description = descriptions[0].get("value", "")

        # 提取 CVSS 分數（優先 v3.1，其次 v3.0，最後 v2.0）
        metrics = cve_item.get("metrics", {})
        cvss_score = None
        cvss_vector = None
        severity = "UNKNOWN"

        # CVSS v3.1
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            cvss_data = cvss_v31[0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            cvss_vector = cvss_data.get("vectorString")
            severity = cvss_data.get("baseSeverity", "UNKNOWN")

        # CVSS v3.0 (fallback)
        if not cvss_score:
            cvss_v30 = metrics.get("cvssMetricV30", [])
            if cvss_v30:
                cvss_data = cvss_v30[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "UNKNOWN")

        # CVSS v2.0 (fallback)
        if not cvss_score:
            cvss_v2 = metrics.get("cvssMetricV2", [])
            if cvss_v2:
                cvss_data = cvss_v2[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                # v2 沒有 severity，根據分數推算
                if cvss_score >= 7.0:
                    severity = "HIGH"
                elif cvss_score >= 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

        # 提取受影響的產品（CPE）
        affected_products = []
        configurations = cve_item.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    if cpe_match.get("vulnerable"):
                        cpe_uri = cpe_match.get("criteria", "")
                        # 解析 CPE URI: cpe:2.3:a:vendor:product:version:...
                        parts = cpe_uri.split(":")
                        if len(parts) >= 5:
                            affected_products.append({
                                "vendor": parts[3],
                                "product": parts[4],
                                "version": parts[5] if len(parts) > 5 else "*",
                                "cpe": cpe_uri,
                            })

        # 提取參考連結
        references = []
        for ref in cve_item.get("references", []):
            references.append({
                "url": ref.get("url", ""),
                "source": ref.get("source", ""),
                "tags": ref.get("tags", []),
            })

        # 提取日期
        published_date = cve_item.get("published")
        last_modified_date = cve_item.get("lastModified")

        return {
            "cve_id": cve_id,
            "description": description,
            "severity": severity,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "affected_products": affected_products,
            "references": references,
            "published_date": published_date,
            "last_modified_date": last_modified_date,
            "source": "nvd",
        }
