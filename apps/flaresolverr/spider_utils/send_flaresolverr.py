# flaresovlerr/spider_utils/send_flaresolverr.py
import httpx
import time
import logging
from .utils import translate_response_to_json
from apps.core.header_injection import get_tagged_headers

logger = logging.getLogger(__name__)


def call_flaresolverr_api(
    url,
    method,
    headers,
    cookie_string,
    flaresolverr_url,
    flaresolverr_max_retries,
    *,
    body: str | None = None,
    content_type: str | None = None,
    host_header: str | None = None,
    session: str | None = None,
):
    """
    Calls FlareSolverr API to bypass Cloudflare protections.
    RETURNS A DICT (Not a Response Object) that fits the translator.
    """

    def _get_cookies_dict(cookie_string):
        cookies_dict = {}
        if cookie_string:
            for part in cookie_string.split(";"):
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    cookies_dict[key] = value
        return cookies_dict

    cookies_dict = _get_cookies_dict(cookie_string)
    for fs_retry_count in range(flaresolverr_max_retries + 1):
        try:
            injected_headers = get_tagged_headers(headers)
            custom_headers_list = [{"name": k, "value": v} for k, v in injected_headers.items()]
            flaresolverr_payload = {
                "cmd": f"request.{method.lower()}",
                "url": url,
                "maxTimeout": 60000,
                "cookies": (
                    [{"name": k, "value": v} for k, v in cookies_dict.items()]
                    if cookies_dict
                    else []
                ),
                "customHeaders": custom_headers_list,
            }

            # Host header override (for vhost routing / CTF challenges).
            if host_header:
                custom_headers_list.append({"name": "Host", "value": host_header})

            # POST/PUT/PATCH body support.
            if body is not None and method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
                flaresolverr_payload["postData"] = body
                if content_type:
                    custom_headers_list.append({"name": "Content-Type", "value": content_type})

            # Session support (reuse browser context).
            if session:
                flaresolverr_payload["session"] = session

            with httpx.Client() as client:
                fs_response = client.post(
                    f"{flaresolverr_url}/v1",
                    json=flaresolverr_payload,
                    timeout=65,
                )
            fs_response.raise_for_status()
            fs_json_data = fs_response.json()

            if fs_json_data.get("status") == "ok":
                solution = fs_json_data["solution"]
                status_code = solution["status"]

                # [FIX] 不需要建立 httpx.Response 物件了，直接組裝 Dict
                # 這樣直接對應 translate_response_to_json 的 dict 處理邏輯

                # 處理 Headers (轉成標準字典)
                response_headers = {
                    h["name"]: h["value"] for h in solution.get("headers", [])
                }

                # 處理 Cookies (如果需要的話，這裡簡單處理，或者讓上層去解析 header)
                # FlareSolverr 的 cookies 通常在 solution['cookies'] 是一堆 dict

                response_data = {
                    "status_code": status_code,
                    "response_text": solution["response"],  # 這裡是 String
                    "response_headers": response_headers,
                    "response_url": solution["url"],
                    # Pass back cookies if present.
                    "response_cookies": solution.get("cookies", []),
                    "user_agent": solution.get("userAgent"),
                    # 如果需要 cookies，可以加在這裡，但 utils 裡目前主要看 headers
                }

                logger.info(
                    f"Spider 通过 FlareSolverr 成功请求 {solution['url']}，状态码 {status_code}。"
                )

                # 直接傳 Dict 進去！
                return translate_response_to_json(
                    response_data, url, True, "SUCCESS_FETCHED", "flaresolverr"
                )

            else:
                logger.error(
                    f"Flaresolverr 服务回应失败: {fs_json_data.get('message')} (第 {fs_retry_count+1} 次)"
                )

        except httpx.RequestError as e:
            logger.error(f"连接 FlareSolverr 失败: {e} (第 {fs_retry_count+1} 次)")

        if fs_retry_count < flaresolverr_max_retries:
            time.sleep(3)
    return None


def create_flaresolverr_session(*, flaresolverr_url: str, max_timeout_ms: int = 60000) -> str | None:
    """Create a FlareSolverr session and return session id."""
    payload = {"cmd": "sessions.create", "maxTimeout": max_timeout_ms}
    try:
        with httpx.Client() as client:
            resp = client.post(f"{flaresolverr_url}/v1", json=payload, timeout=65)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            return None
        return data.get("session")
    except Exception:
        return None


def destroy_flaresolverr_session(*, flaresolverr_url: str, session: str) -> bool:
    payload = {"cmd": "sessions.destroy", "session": session}
    try:
        with httpx.Client() as client:
            resp = client.post(f"{flaresolverr_url}/v1", json=payload, timeout=30)
        return resp.status_code == 200
    except Exception:
        return False
