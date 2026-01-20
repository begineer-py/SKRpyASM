import logging
import re
import json
import hashlib

# 假設 c2_core 是你的頂層 App 之一
from c2_core.config.logging import log_function_call
from .content_type import ContentTypeDetector

logger = logging.getLogger(__name__)


@log_function_call()
def get_cookies_dict(cookie_string):
    cookies_dict = {}
    if cookie_string:
        for part in cookie_string.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                cookies_dict[key.strip()] = value.strip()
    return cookies_dict


@log_function_call()
def check_if_blocked(status_code, body):
    """
    WAF 檢測邏輯
    """
    if status_code in [403, 406, 429, 503]:
        return True

    blocked_patterns = [
        r"challenge-form",
        r"jschl_vc",
        r"cf-browser-verification",
        r"Just a moment...",
        r"checking your browser",
        r"DDOS-GUARD",
        r"<noscript>You need to enable JavaScript",
        r"Enable JavaScript and cookies to continue",
        r"/cdn-cgi/challenge-platform/",
    ]
    for p in blocked_patterns:
        if body and re.search(p, body, re.IGNORECASE):
            return True
    return False


@log_function_call()
def translate_response_to_json(data, url, used_flaresolverr, status, source_type):
    """
    統一格式化輸出，兼容 dict 和 object
    """
    result = {
        "status_code": 0,
        "response_headers": {},
        "response_text": "",
        "response_url": url,
        "title": None,
        "tech": [],
        "used_flaresolverr": used_flaresolverr,
        "content_fetch_status": status,
        "source_type": source_type,
        # 預設為空字串，避免 downstream .lower() 報錯
        "content_type": "",
        "is_text_content": False,
        "is_binary_url": False,
        "md5": "",
    }

    if not data:
        return result
    detector = ContentTypeDetector(
        data,
        used_flaresolverr,
        status,
        url,
    )
    # 1. 處理 httpx 來源 (始終是 dict)
    if source_type == "httpx":
        if isinstance(data, dict):
            result["status_code"] = data.get("status_code")
            result["response_text"] = data.get("body")
            result["title"] = data.get("title")
            result["tech"] = data.get("tech", [])
            result["response_url"] = data.get("url", url)
            result["response_headers"] = data.get("headers", {})
            # 使用 ContentTypeDetector 來檢測 content type

            (
                result["content_type"],
                result["is_text_content"],
                result["is_binary_url"],
            ) = detector.detect()
            result["md5"] = hashlib.md5(
                result["response_text"].encode("utf-8", errors="ignore")
            ).hexdigest()
    # 2. 處理 flaresolverr 來源 (dict)
    elif source_type == "flaresolverr":
        if isinstance(data, dict):
            # 已經是 dict 了，直接搬運
            result["status_code"] = data.get("status_code")
            result["response_headers"] = data.get(
                "response_headers", {}
            )  # 注意 key 可能叫 response_headers
            # 如果 dict 是由自己產生的，key 應該是 response_text
            result["response_text"] = (
                data.get("response_text") or data.get("text") or ""
            )
            result["response_url"] = data.get("response_url") or data.get("url", url)

            # 補丁：如果上一次轉換把 headers 放在 'headers' 裡而不是 'response_headers'
            if not result["response_headers"] and "headers" in data:
                result["response_headers"] = data["headers"]
            (
                result["content_type"],
                result["is_text_content"],
                result["is_binary_url"],
            ) = detector.detect()
            result["md5"] = hashlib.md5(
                result["response_text"].encode("utf-8", errors="ignore")
            ).hexdigest()
    return result
