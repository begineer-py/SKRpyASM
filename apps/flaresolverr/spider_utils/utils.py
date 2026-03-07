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
        "content_length": 0,
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
            result["response_headers"] = data.get("header", {})
            # 使用 ContentTypeDetector 來檢測 content type
            result["content_length"] = len(data.get("body", ""))
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
            result["tech"] = data.get("tech", [])

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
            result["content_length"] = len(result["response_text"])
    return result


@log_function_call()
def if_spa(data: dict) -> bool:
    """
    判斷解析後的 httpx 數據中是否包含 SPA 框架指紋。
    """
    if not data or not isinstance(data, dict):
        return False

    # httpx 返回的 tech 通常是一個 list of strings，例如 ["React", "Nginx", "jQuery"]
    tech_list = data.get("tech", [])
    if not tech_list:
        return False

    # 定義 SPA 關鍵字 (轉小寫比對)
    spa_keywords = {
        "vue",
        "react",
        "angular",
        "svelte",
        "next.js",
        "nuxt.js",
        "backbone",
        "ember",
        "cloudflare",
    }

    # 檢查每一個技術組件
    for tech_item in tech_list:
        # tech_item 可能是 "React:16.8" 這種格式，我們只取名稱部分並轉小寫
        t_name = (
            tech_item.split(":")[0].lower() if ":" in tech_item else tech_item.lower()
        )

        # 檢查是否包含關鍵字
        # 這裡用包含檢查 (in) 是為了抓到像 "vue.js" 這種
        for keyword in spa_keywords:
            if keyword in t_name:
                return True

    return False
