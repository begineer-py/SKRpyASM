class ContentTypeDetector:
    def __init__(
        self,
        response_data: dict,
        used_flaresolverr: bool,
        content_fetch_status: str,
        url: str,
    ) -> None:
        self.response_data: dict = response_data
        self.used_flaresolverr: bool = used_flaresolverr
        self.content_fetch_status: str = content_fetch_status
        self.url: str = url

    def detect(self) -> tuple[str, bool, bool]:
        """
        Returns (content_type, is_text_content, is_binary_url)
        """
        is_binary_url = self._binary_url_detector()

        # 1. 嘗試從 Header 找 (雖然你說會是空的，但還是留著尊重一下)
        content_type = self.response_data.get("content_type")
        if not content_type:
            headers = self.response_data.get("response_headers") or {}
            for k in ("content-type", "Content-Type"):
                if k in headers:
                    content_type = headers.get(k)
                    break
        content_type = (content_type or "").lower()

        # 2. 透過 Content-Type 判斷是否為文字
        is_text_content = (
            ("text/" in content_type)
            or ("json" in content_type)
            or ("xml" in content_type)
            or ("html" in content_type)
        )

        # [FIX] 這裡就是你要的救命稻草！
        # 如果上面判斷失敗 (因為沒 Header)，且不是二進制檔案，就直接嗅探內容
        if not is_text_content and not is_binary_url:
            response_text = self.response_data.get("response_text", "")
            # 確保內容存在且是字串
            if response_text and isinstance(response_text, str):
                # 抓前 500 個字元轉小寫來檢查
                snippet = response_text[:500].lower().strip()

                # 特徵判斷：像不像 HTML?
                if (
                    "<html" in snippet
                    or "<!doctype html" in snippet
                    or "<head" in snippet
                    or "<body" in snippet
                ):
                    is_text_content = True
                    if not content_type:
                        content_type = "text/html"  # 幫它貼上標籤，讓後面好做事

                # 特徵判斷：像不像 JSON? (以防萬一)
                elif snippet.startswith("{") or snippet.startswith("["):
                    # 簡單粗暴判斷，不一定準，但夠用
                    is_text_content = True
                    if not content_type:
                        content_type = "application/json"

        return content_type, is_text_content, is_binary_url

    def _binary_url_detector(self) -> bool:
        return any(
            self.url.lower().endswith(ext)
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".ico",
                ".woff",
                ".ttf",
                ".pdf",
                ".zip",
                ".svg",
                ".webp",
            ]
        )
