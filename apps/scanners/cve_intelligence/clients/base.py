import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseCVEClient(ABC):
    """
    CVE 資料來源客戶端的抽象基礎類別
    提供通用的 HTTP 請求、重試邏輯和錯誤處理
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """非同步上下文管理器進入"""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步上下文管理器退出"""
        if self.session:
            await self.session.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        發送 HTTP 請求，包含重試邏輯

        Args:
            method: HTTP 方法 (GET, POST)
            url: 請求 URL
            headers: 請求標頭
            params: URL 參數
            json_data: JSON 請求體

        Returns:
            回應的 JSON 資料

        Raises:
            httpx.HTTPStatusError: HTTP 錯誤
            httpx.TimeoutException: 請求超時
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        try:
            response = await self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
            raise
        except httpx.TimeoutException:
            logger.warning(f"Request timeout for {url}, retrying...")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise

    @abstractmethod
    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        查詢特定 CVE ID 的詳細資訊

        Args:
            cve_id: CVE 編號 (例如 CVE-2024-12345)

        Returns:
            CVE 詳細資訊，若不存在則返回 None
        """
        pass

    @abstractmethod
    async def search_cves(
        self,
        keyword: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜尋 CVE

        Args:
            keyword: 搜尋關鍵字
            **kwargs: 其他搜尋參數

        Returns:
            CVE 清單
        """
        pass

    def _extract_cve_id(self, text: str) -> Optional[str]:
        """
        從文字中提取 CVE ID

        Args:
            text: 包含 CVE ID 的文字

        Returns:
            CVE ID 或 None
        """
        import re
        match = re.search(r'CVE-\d{4}-\d{4,}', text, re.IGNORECASE)
        return match.group(0).upper() if match else None
