import re
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# //# sourceMappingURL=... 或 //@ sourceMappingURL=... (舊格式)
_SOURCEMAP_RE = re.compile(r"//[#@]\s*sourceMappingURL=([^\s\r\n]+)")


class SourceMapDetector:
    """偵測 JavaScript 中的 Source Map 指向位置。"""

    def from_response_headers(self, headers: dict) -> list[str]:
        """從 HTTP response headers 取得 source map URL (SourceMap / X-SourceMap)。"""
        for key, val in headers.items():
            if key.lower() in ("sourcemap", "x-sourcemap") and val:
                return [val.strip()]
        return []

    def from_js_content(self, js_content: str, base_url: str) -> list[str]:
        """從 JS 原始碼末尾的 sourceMappingURL 註解取得 source map URL。

        支援：
        - 一般相對/絕對 URL
        - data:application/json;base64,... 內嵌 source map
        """
        if not js_content:
            return []
        urls = []
        for match in _SOURCEMAP_RE.finditer(js_content):
            raw = match.group(1).strip()
            if raw.startswith("data:application/json"):
                urls.append(raw)
            else:
                try:
                    urls.append(urljoin(base_url, raw))
                except Exception:
                    pass
        return urls

    def probe_common_paths(self, js_url: str) -> list[str]:
        """當 JS 內容中沒有明確 sourceMappingURL 時，嘗試 <js_url>.map 作為探測。"""
        return [js_url + ".map"]
