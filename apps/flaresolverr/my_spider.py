import logging
import json
from typing import Optional, Any, Dict
from .spider_utils.techstack_httpx import send_httpx_request, send_httpx_request_chrome
from .spider_utils.send_flaresolverr import call_flaresolverr_api
from .spider_utils.utils import check_if_blocked, translate_response_to_json
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

        # 預設狀態為網路錯誤，直到證明有東西回來
        self.content_fetch_status: str = "FAILED_NETWORK_ERROR"

        self.final_raw_data: Optional[Any] = None
        self.final_source_type: Optional[str] = None
        self.content_type: Optional[str] = None
        self.final_url: str = url

    @log_function_call()
    def send(self) -> tuple[Optional[Any], bool, str]:
        logger.info(f"Spider 啟動: {self.url}")

        # --- 1. Docker Httpx (標準模式) ---
        raw_output = send_httpx_request(self.url)
        logger.info(f"Httpx 原始輸出: {raw_output}")

        if self._process_httpx_output(raw_output, "Standard"):
            logger.info("先鋒部隊 (Httpx Standard) 成功獲取情報。")
            json_payload = translate_response_to_json(
                self.final_raw_data,
                self.url,
                False,
                self.content_fetch_status,
                "httpx",
            )
            return json_payload, False, self.content_fetch_status

        logger.info("標準模式失敗，切換至 Httpx Chrome (Headless) 模式嘗試...")
        chrome_output = send_httpx_request_chrome(self.url)

        if self._process_httpx_output(chrome_output, "Chrome-Headless"):
            logger.info("特種部隊 (Httpx Chrome) 成功突破，無需動用 FlareSolverr。")
            json_payload = translate_response_to_json(
                self.final_raw_data,
                self.url,
                False,  # 這裡還是算 httpx，不算 flaresolverr
                self.content_fetch_status,
                "httpx",
            )
            return json_payload, False, self.content_fetch_status

        # --- 如果 Httpx 失敗，且有配置 FlareSolverr，才升級 ---
        if self.flaresolverr_url:
            logger.info(
                f"Httpx 任務失敗 (狀態: {self.content_fetch_status})，升級至 FlareSolverr..."
            )
            self.used_flaresolverr = True

            # fs_response 現在是一個 dict (由 call_flaresolverr_api 返回)
            fs_response_dict = call_flaresolverr_api(
                self.url,
                self.method,
                self.headers,
                self.cookie_string,
                self.flaresolverr_url,
                1,  # 這裡的 session_id 最好參數化
            )

            if fs_response_dict:
                self.final_raw_data = fs_response_dict  # 直接存這個 dict
                self.final_source_type = "flaresolverr"

                # 從字典中讀取狀態
                status_code = fs_response_dict.get("status_code")
                response_text = fs_response_dict.get("response_text", "")

                # 判定狀態
                if status_code == 204 or not response_text:
                    self.content_fetch_status = "FAILED_NO_CONTENT"
                elif status_code in [403, 406, 429, 503]:
                    # 這裡可以再細分，但 FlareSolverr 通常能繞過，如果還是 403 就是真的 403
                    # 不過為了保險，這裡標記為 SUCCESS_FETCHED 比較好，因為確實抓到了內容（哪怕是錯誤頁面）
                    # 除非內容真的是 Cloudflare 的 Challenge 頁面
                    if check_if_blocked(status_code, response_text):
                        self.content_fetch_status = "FAILED_BLOCKED"
                    else:
                        self.content_fetch_status = "SUCCESS_FETCHED"
                else:
                    self.content_fetch_status = "SUCCESS_FETCHED"

                # 使用統一轉換，直接回傳標準 JSON
                json_payload = translate_response_to_json(
                    self.final_raw_data,
                    self.url,
                    True,
                    self.content_fetch_status,
                    "flaresolverr",
                )
                return json_payload, True, self.content_fetch_status
            else:
                self.content_fetch_status = "FAILED_NETWORK_ERROR"

        # 全部失敗時也回傳標準格式（空內容），避免上游再轉換
        empty_payload = translate_response_to_json(
            None,
            self.url,
            self.used_flaresolverr,
            self.content_fetch_status,
            self.final_source_type or "httpx",
        )
        return empty_payload, self.used_flaresolverr, self.content_fetch_status

    @log_function_call()
    def _process_httpx_output(self, raw_output: Optional[str], mode_name: str) -> bool:
        """
        處理 httpx 的輸出，並更新 self.content_fetch_status
        返回 True 表示成功獲取有效內容 (SUCCESS_FETCHED)
        返回 False 表示失敗 (BLOCKED / NETWORK_ERROR / NO_CONTENT) 且需要繼續嘗試
        """
        if not raw_output:
            # 沒輸出視為網絡問題或 Timeout，不改變狀態 (保持上一次的狀態，或是預設 NETWORK_ERROR)
            return False

        try:
            lines = raw_output.split("\n")
            # 確保最後一行有效
            last_line = next((line for line in reversed(lines) if line.strip()), None)
            if not last_line:
                return False

            data = json.loads(last_line)

            status = data.get("status_code", 0)
            body = data.get("body") or ""
            if body == "":
                logger.warning(f"Docker Httpx ({mode_name}) 返回空內容")

            # 1. 檢查 WAF 攔截
            if check_if_blocked(status, body):
                logger.warning(f"Docker Httpx ({mode_name}) 被攔截: Status {status}")
                self.content_fetch_status = "FAILED_BLOCKED"
                return False  # 失敗，需要升級

            # 2. 檢查空內容
            if not body and status == 200:
                # 有時候 httpx 沒抓到 body 但 connection ok
                # 這種情況比較尷尬，如果不嚴重，可以當作 NO_CONTENT，但通常我們希望重試
                logger.warning(f"Docker Httpx ({mode_name}) 返回空內容")
                self.content_fetch_status = "FAILED_NO_CONTENT"
                return False  # 嘗試下一種手段看能不能拿到內容

            # 3. 成功
            self.final_raw_data = data
            self.final_source_type = "httpx"
            self.content_fetch_status = "SUCCESS_FETCHED"
            return True

        except json.JSONDecodeError:
            logger.error(f"Docker Httpx ({mode_name}) 輸出解析失敗")
            # 解析失敗視為網絡/工具錯誤
            self.content_fetch_status = "FAILED_NETWORK_ERROR"
            return False

    def translate_into_json(self, response_ignored: Optional[Any] = None) -> Any:
        """
        將內部暫存的數據轉為統一 JSON
        """
        return translate_response_to_json(
            self.final_raw_data,
            self.url,
            self.used_flaresolverr,
            self.content_fetch_status,
            self.final_source_type,
        )
