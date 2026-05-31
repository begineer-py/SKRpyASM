import logging
from typing import Dict, Any, Optional, List
from .base import BaseCVEClient

logger = logging.getLogger(__name__)


class EPSSClient(BaseCVEClient):
    """
    EPSS (Exploit Prediction Scoring System) 客戶端
    文件：https://www.first.org/epss/api
    """

    BASE_URL = "https://api.first.org/data/v1/epss"

    def __init__(self, timeout: int = 30):
        """初始化 EPSS 客戶端（無需 API key）"""
        super().__init__(api_key=None, timeout=timeout)

    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        查詢特定 CVE 的 EPSS 分數

        Args:
            cve_id: CVE 編號

        Returns:
            EPSS 資料，若不存在則返回 None
        """
        try:
            params = {"cve": cve_id.upper()}
            response = await self._make_request(
                method="GET",
                url=self.BASE_URL,
                headers={"Content-Type": "application/json"},
                params=params,
            )

            data = response.get("data", [])
            if not data:
                logger.warning(f"EPSS data not found for {cve_id}")
                return None

            epss_item = data[0]
            return {
                "cve_id": epss_item.get("cve", "").upper(),
                "epss_score": float(epss_item.get("epss", 0)),
                "percentile": float(epss_item.get("percentile", 0)),
                "date": epss_item.get("date", ""),
            }

        except Exception as e:
            logger.error(f"Error querying EPSS for {cve_id}: {e}")
            return None

    async def query_cves_batch(self, cve_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批次查詢多個 CVE 的 EPSS 分數

        Args:
            cve_ids: CVE ID 清單

        Returns:
            以 CVE ID 為 key 的 EPSS 資料字典
        """
        try:
            # EPSS API 支援批次查詢，用逗號分隔
            cve_list = ",".join([cve.upper() for cve in cve_ids])
            params = {"cve": cve_list}

            response = await self._make_request(
                method="GET",
                url=self.BASE_URL,
                headers={"Content-Type": "application/json"},
                params=params,
            )

            data = response.get("data", [])
            result = {}

            for epss_item in data:
                cve_id = epss_item.get("cve", "").upper()
                result[cve_id] = {
                    "cve_id": cve_id,
                    "epss_score": float(epss_item.get("epss", 0)),
                    "percentile": float(epss_item.get("percentile", 0)),
                    "date": epss_item.get("date", ""),
                }

            logger.info(f"Fetched EPSS scores for {len(result)}/{len(cve_ids)} CVEs")
            return result

        except Exception as e:
            logger.error(f"Error batch querying EPSS: {e}")
            return {}

    async def search_cves(
        self,
        keyword: Optional[str] = None,
        epss_gt: Optional[float] = None,
        percentile_gt: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜尋 EPSS 分數（注意：EPSS API 不支援關鍵字搜尋，此方法主要用於一致性）

        Args:
            keyword: 不支援
            epss_gt: EPSS 分數大於此值
            percentile_gt: 百分位數大於此值

        Returns:
            空清單（EPSS API 不支援搜尋）
        """
        logger.warning("EPSS API does not support search. Use query_cve or query_cves_batch instead.")
        return []
