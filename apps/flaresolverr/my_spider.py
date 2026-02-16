import logging
import json
import socket
import httpx
from urllib.parse import urlparse
from typing import Optional, Any, Dict
from .spider_utils.techstack_httpx import send_httpx_request
from .spider_utils.send_flaresolverr import call_flaresolverr_api
from .spider_utils.utils import check_if_blocked, translate_response_to_json, if_spa
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)


class MySpider:
    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        cookie_string: str = "",
        flaresolverr_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.url: str = url
        self.headers: Dict[str, str] = headers or {}
        self.method: str = method
        self.cookie_string: str = cookie_string
        self.flaresolverr_url: Optional[str] = flaresolverr_url
        self.used_flaresolverr: bool = False

        self.content_fetch_status: str = "FAILED_NETWORK_ERROR"
        self.final_raw_data: Optional[Any] = None
        self.final_source_type: Optional[str] = None
        self.final_url: str = url

        # 建立一個輕量的 httpx client 用於預檢和非瀏覽器下載
        # verify=False 忽略 SSL 錯誤，timeout 設定短一點避免阻塞
        self.client = httpx.Client(verify=False, timeout=15.0, follow_redirects=True)
        # 如果有 cookie，設定到 client
        if self.cookie_string:
            cookies = {}
            for item in self.cookie_string.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    cookies[k] = v
            self.client.cookies.update(cookies)
        self.client.headers.update(self.headers)

    def _check_dns(self) -> bool:
        """
        [預檢階段 1] 快速檢查域名是否可以解析。
        如果這裡失敗，絕對不要去煩 FlareSolverr。
        """
        try:
            parsed = urlparse(self.url)
            hostname = parsed.hostname
            if not hostname:
                logger.error(f"URL 格式無效，無法解析 hostname: {self.url}")
                return False

            # 使用 socket 進行 DNS 查詢
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            logger.error(f"[Pre-flight] DNS 解析失敗: {self.url}。將跳過所有後續請求。")
            self.content_fetch_status = "FAILED_DNS_ERROR"
            return False
        except Exception as e:
            logger.error(f"[Pre-flight] DNS 檢查發生未預期錯誤: {e}")
            return False

    def _check_content_type_and_download(self) -> tuple[bool, Optional[Dict]]:
        """
        [預檢階段 2 - 強化版] 檢查 Content-Type。
        策略：
        1. 嘗試 HEAD。
        2. 如果 HEAD 失敗 (405/403/400/500)，改用 GET (Stream 模式) 只讀取 Headers。
        3. 判斷是否需要瀏覽器。
        """

        # 定義不需要瀏覽器渲染的類型
        NON_BROWSER_TYPES = [
            "image/",
            "video/",
            "audio/",
            "application/pdf",
            "application/zip",
            "application/octet-stream",
            "application/json",
            "text/xml",
            "application/xml",
            "text/plain",
            "font/",
        ]

        def is_direct_download_type(headers):
            c_type = headers.get("content-type", "").lower()
            return any(t in c_type for t in NON_BROWSER_TYPES)

        def create_fake_response(resp, body_text):
            return {
                "status_code": resp.status_code,
                "body": body_text,
                "header": dict(resp.headers),
                "url": str(resp.url),
                "tech": [],
            }

        try:
            logger.info(f"[Pre-flight] 嘗試 HEAD 請求: {self.url}")
            # --- 策略 A: 嘗試 HEAD ---
            head_resp = self.client.head(self.url)

            # 如果 HEAD 成功且正常
            if head_resp.status_code == 200:
                if is_direct_download_type(head_resp.headers):
                    logger.info(f"[Pre-flight] HEAD 確認為非 HTML 資源，開始下載。")
                    # 重新發起 GET 下載內容
                    get_resp = self.client.get(self.url)
                    return False, create_fake_response(get_resp, get_resp.text)
                else:
                    # 是 HTML，轉交 FlareSolverr
                    return True, None

            # 如果 HEAD 被攔截 (403/429)，直接轉交 FlareSolverr
            elif head_resp.status_code in [403, 429, 503]:
                logger.warning(
                    f"[Pre-flight] HEAD 返回 {head_resp.status_code} (可能由 WAF 攔截)，轉交 FlareSolverr。"
                )
                return True, None

            # 如果是 405 (Method Not Allowed) 或其他錯誤，進入策略 B
            logger.info(
                f"[Pre-flight] HEAD 返回 {head_resp.status_code}，切換至 GET Stream 模式探測。"
            )

        except httpx.RequestError as e:
            logger.warning(
                f"[Pre-flight] HEAD 請求異常 ({e})，切換至 GET Stream 模式探測。"
            )

        # --- 策略 B: 嘗試 GET (Stream) ---
        # 這是最穩的方法：像正常瀏覽器一樣發起 GET，但只讀頭部
        try:
            with self.client.stream("GET", self.url) as response:
                # 這裡已經拿到了 Headers，但還沒下載 Body

                # 檢查狀態碼
                if response.status_code in [403, 406, 429, 503]:
                    logger.warning(
                        f"[Pre-flight] GET Stream 返回 {response.status_code}，轉交 FlareSolverr。"
                    )
                    return True, None

                # 檢查 Content-Type
                if is_direct_download_type(response.headers):
                    logger.info(
                        f"[Pre-flight] GET Stream 確認為非 HTML 資源，下載內容。"
                    )
                    # 讀取全部內容
                    response.read()
                    return False, create_fake_response(response, response.text)

                # 如果是 HTML，我們不需要在這裡讀取 Body (可能需要 JS 渲染)
                # 這裡有個優化選擇：
                # 選項 1: 直接回傳 True，讓 FlareSolverr 再跑一次 (浪費一次請求但結構簡單)
                # 選項 2: 如果 response.text 包含 <script> 則回傳 True，否則直接用這個結果
                # 為了保險起見 (SPA 檢測)，我們假設如果是 HTML 就給 FlareSolverr (或者你也可以在這裡讀取 body 做進一步 SPA 檢測)

                # 簡單起見：是 HTML 就交給大部隊
                return True, None

        except Exception as e:
            logger.error(
                f"[Pre-flight] GET Stream 探測失敗: {e}，最後手段：轉交 FlareSolverr。"
            )
            return True, None

    @log_function_call()
    def send(self) -> tuple[Optional[Any], bool, str]:
        # --- 0. DNS 預檢 ---
        if not self._check_dns():
            return (
                translate_response_to_json(
                    None, self.url, False, "FAILED_DNS_ERROR", "httpx"
                ),
                False,
                "FAILED_DNS_ERROR",
            )

        # --- 1. Docker Httpx ---
        raw_output = send_httpx_request(self.url)
        is_parsed_success = self._process_httpx_output(raw_output, "Standard")

        # 暫存 Httpx 資訊
        tech = self.final_raw_data.get("tech", []) if self.final_raw_data else []
        response_headers = (
            self.final_raw_data.get("header", {}) if self.final_raw_data else {}
        )

        if is_parsed_success:
            if not if_spa(self.final_raw_data):
                # 情況 A: 標準 HTML 且 Httpx 抓取成功 -> 結束
                return (
                    translate_response_to_json(
                        self.final_raw_data,
                        self.url,
                        False,
                        self.content_fetch_status,
                        "httpx",
                    ),
                    False,
                    self.content_fetch_status,
                )
            # 情況 B: 是 SPA -> 繼續交給 FlareSolverr
            logger.warning(f"偵測到 SPA，準備升級 FlareSolverr: {self.url}")
        else:
            # 情況 C: Httpx 失敗，如果是 DNS 錯誤 -> 直接結束
            if self.content_fetch_status == "FAILED_DNS_ERROR":
                return (
                    translate_response_to_json(
                        None, self.url, False, "FAILED_DNS_ERROR", "httpx"
                    ),
                    False,
                    "FAILED_DNS_ERROR",
                )
            # 情況 D: 其他失敗 (Blocked/Timeout) -> 嘗試用 FlareSolverr 救救看

        # --- 2. Content-Type 預檢 (避免將大文件交給 FlareSolverr) ---
        should_use_fs, direct_data = self._check_content_type_and_download()
        if not should_use_fs and direct_data:
            return (
                translate_response_to_json(
                    direct_data, self.url, False, "SUCCESS_FETCHED", "httpx"
                ),
                False,
                "SUCCESS_FETCHED",
            )

        # --- 3. FlareSolverr ---
        if self.flaresolverr_url:
            self.used_flaresolverr = True
            try:
                fs_response_dict = call_flaresolverr_api(
                    self.url,
                    self.method,
                    self.headers,
                    self.cookie_string,
                    self.flaresolverr_url,
                    1,
                )

                if fs_response_dict:
                    self.final_raw_data = fs_response_dict
                    self.final_source_type = "flaresolverr"
                    status_code = fs_response_dict.get("status_code")
                    response_text = fs_response_dict.get("response_text", "")

                    if status_code == 204 or not response_text:
                        self.content_fetch_status = "FAILED_NO_CONTENT"
                    elif status_code in [403, 406, 429, 503]:
                        self.content_fetch_status = (
                            "FAILED_BLOCKED"
                            if check_if_blocked(status_code, response_text)
                            else "SUCCESS_FETCHED"
                        )
                    else:
                        self.content_fetch_status = "SUCCESS_FETCHED"

                    if tech:
                        self.final_raw_data["tech"] = tech
                    if response_headers and not self.final_raw_data.get(
                        "response_headers"
                    ):
                        self.final_raw_data["response_headers"] = response_headers

                    return (
                        translate_response_to_json(
                            self.final_raw_data,
                            self.url,
                            True,
                            self.content_fetch_status,
                            "flaresolverr",
                        ),
                        True,
                        self.content_fetch_status,
                    )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 500:
                    logger.warning(f"FlareSolverr 遇到跳轉死連結 (500): {self.url}")
                    return (
                        translate_response_to_json(
                            None, self.url, True, "FAILED_DNS_ERROR", "flaresolverr"
                        ),
                        True,
                        "FAILED_DNS_ERROR",
                    )
                self.content_fetch_status = "FAILED_SERVER_ERROR"
            except httpx.TimeoutException:
                self.content_fetch_status = "FAILED_TIMEOUT"
            except Exception as e:
                logger.error(f"FlareSolverr 異常: {e}")
                self.content_fetch_status = "FAILED_NETWORK_ERROR"

        # 全部失敗
        return (
            translate_response_to_json(
                None,
                self.url,
                self.used_flaresolverr,
                self.content_fetch_status,
                self.final_source_type or "httpx",
            ),
            self.used_flaresolverr,
            self.content_fetch_status,
        )

    @log_function_call()
    def _process_httpx_output(self, raw_output: Optional[str], mode_name: str) -> bool:
        if not raw_output:
            self.content_fetch_status = "FAILED_DNS_ERROR"
            return False
        try:
            lines = raw_output.split("\n")
            last_line = next((line for line in reversed(lines) if line.strip()), None)
            if not last_line:
                return False
            data = json.loads(last_line)
            status = data.get("status_code", 0)
            body = data.get("body") or ""

            if check_if_blocked(status, body):
                self.content_fetch_status = "FAILED_BLOCKED"
                return False
            if not body and status == 200:
                self.content_fetch_status = "FAILED_NO_CONTENT"
                return False
            if status == 0:
                self.content_fetch_status = "FAILED_DNS_ERROR"
                return False

            self.final_raw_data = data
            self.final_source_type = "httpx"
            self.content_fetch_status = "SUCCESS_FETCHED"
            return True
        except json.JSONDecodeError:
            self.content_fetch_status = "FAILED_NETWORK_ERROR"
            return False

    def translate_into_json(self, response_ignored: Optional[Any] = None) -> Any:
        return translate_response_to_json(
            self.final_raw_data,
            self.url,
            self.used_flaresolverr,
            self.content_fetch_status,
            self.final_source_type,
        )
