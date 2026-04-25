import logging
import hashlib
import subprocess
import json
import os
import tempfile
import requests
from urllib.parse import urlparse
from typing import Dict, Optional, Any, List, Union

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# c2_core imports
from c2_core.config.logging import log_function_call
from apps.flaresolverr.orchestrators.recon_orchestrator import ReconOrchestrator
from c2_core.config.utils import sanitize_for_db
from c2_core.config.config import Config
from apps.flaresolverr.spider_utils.send_flaresolverr import call_flaresolverr_api

# Logger setup
logger = logging.getLogger(__name__)

# Hasura & FlareSolverr Configurations
HASURA_GRAPHQL_URL = f"{Config.HASURA_URL}/v1/graphql" if Config.HASURA_URL else None
HASURA_ADMIN_SECRET = Config.HASURA_ADMIN_SECRET
FLARESOLVERR_URL = Config.FLARESOLVERR_URL

# ==========================================
# 字典路徑配置 (請確保伺服器上有這些檔案)
# ==========================================
WORDLIST_MAP = {
    "email": "/usr/share/wordlists/SecLists/Fuzzing/SQLi/SQLi.txt",  # 針對 email 欄位的 fuzzing 字典
    "phone": "/usr/share/wordlists/SecLists/Fuzzing/numbers.txt",  # 針對電話的數字字典
    "string": "/usr/share/wordlists/SecLists/Fuzzing/XSS/XSS-RSnake.txt",  # 針對字串的 XSS 字典
    "integer": "/usr/share/wordlists/SecLists/Fuzzing/numbers.txt",
    "default": "/usr/share/wordlists/dirb/common.txt",  # 預設字典
}

# 導入增強的 payload 映射
from apps.http_sender.payload_mapping import (
    get_payload_for_parameter,
    PAYLOAD_STRUCTURE,
)


@log_function_call()
def get_graphql_client() -> Client:
    headers = (
        {"x-hasura-admin-secret": HASURA_ADMIN_SECRET} if HASURA_ADMIN_SECRET else {}
    )
    transport = RequestsHTTPTransport(
        url=HASURA_GRAPHQL_URL, headers=headers, use_json=True
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


# GraphQL 查詢字串
endpoint_query = """query endpoint($id: bigint!) {
  core_endpoint(where: {id: {_eq: $id}}) {
    path
    created_at
    method
    core_urlparameters {
      key
      line_number
      param_hash
      source_type
      param_location
      data_type
      value
    }
    core_endpoint_discovered_by_urls {
      core_urlresult {
        content_length
        content_fetch_status
        headers
        is_external_redirect
        status_code
        title
        final_url
        used_flaresolverr
      }
      endpoint_id
    }
  }
}
"""


class Myfuzz:
    def __init__(
        self,
        base_url: str,
        path: str,
        method: str,
        target_key: str,  # 要被替換成 FUZZ 的參數名
        all_params: List[Dict],  # 原始參數列表
        wordlist_path: str,
        flaresolverr_url: str,
        user_cookies: str = "",  # 使用者自定義的 Cookies
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.path = path.lstrip("/")
        self.method = method.upper()
        self.target_key = target_key
        self.all_params = all_params
        self.wordlist_path = wordlist_path
        self.flaresolverr_url = flaresolverr_url
        self.user_cookies = user_cookies

        # FlareSolverr 獲取到的憑證
        self.cf_cookie_string = ""
        self.cf_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

    def _get_cf_credentials(self):
        """透過 FlareSolverr 取得目標網站的 cf_clearance Cookie 和 User-Agent"""
        if not self.flaresolverr_url:
            logger.warning("未設定 FLARESOLVERR_URL，將跳過 Cloudflare 繞過步驟。")
            return

        logger.info(f"正在透過 FlareSolverr 獲取 {self.base_url} 的通關憑證...")
        try:
            payload = {"cmd": "request.get", "url": self.base_url, "maxTimeout": 60000}
            res = requests.post(f"{self.flaresolverr_url}/v1", json=payload, timeout=65)
            res_data = res.json()

            if res_data.get("status") == "ok":
                cookies_list = res_data["solution"]["cookies"]
                self.cf_cookie_string = "; ".join(
                    [f"{c['name']}={c['value']}" for c in cookies_list]
                )
                self.cf_user_agent = res_data["solution"]["userAgent"]
                logger.info("成功獲取 Cloudflare clearance Cookie 與對應 User-Agent。")
            else:
                logger.error(f"FlareSolverr 失敗: {res_data.get('message')}")
        except Exception as e:
            logger.error(f"呼叫 FlareSolverr 時發生錯誤: {e}")

    def _get_smart_default(self, key: str) -> str:
        """根據參數名稱提供智慧型預設值，避免 API 因為欄位空白而直接拒絕"""
        key_lower = key.lower()
        if "email" in key_lower:
            return "test_user@example.com"
        if "phone" in key_lower or "mobile" in key_lower:
            return "0912345678"
        if "id" in key_lower:
            return "101"
        if "fname" in key_lower or "first" in key_lower:
            return "John"
        if "lname" in key_lower or "last" in key_lower:
            return "Doe"
        if "country" in key_lower:
            return "US"
        if "source" in key_lower:
            return "direct"
        if "campaign" in key_lower:
            return "default_campaign"
        # 如果都沒對中，給一個基礎字串
        return "test_value"

    def _build_fuzz_params(self) -> str:
        """
        組裝參數字串。
        非目標參數若為空值，則填入智慧預設值。
        """
        payload_parts = []
        for p in self.all_params:
            key = p["key"]
            if key == self.target_key:
                # 這是我們要爆破的目標
                payload_parts.append(f"{key}=FUZZ")
            else:
                # 取得原始值
                val = p.get("value")

                # 如果原始值是空的 (None 或 "")，補上預設值
                if not val:
                    val = self._get_smart_default(key)

                payload_parts.append(f"{key}={val}")
        return "&".join(payload_parts)

    def run(self) -> List[Dict]:
        """執行完整 Fuzzing 流程"""
        # 1. 取得 Cloudflare 憑證
        self._get_cf_credentials()

        # 2. 準備暫存輸出檔
        fd, output_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)

        # 3. 合併 Cookies
        final_cookies = "; ".join(
            filter(None, [self.user_cookies, self.cf_cookie_string])
        )

        # 4. 準備 URL 與參數
        params_string = self._build_fuzz_params()

        # 基礎指令
        cmd = [
            "ffuf",
            "-w",
            self.wordlist_path,
            "-X",
            self.method,
            "-H",
            f"User-Agent: {self.cf_user_agent}",
            "-o",
            output_path,
            "-of",
            "json",
            "-t",
            "10",
            "-p",
            "0.5",
            "-ac",  # 自動校準 (Auto-Calibration)
            "-fc",
            "403,404",  # 這裡要補上 "-", Filter Code: 排除 403 和 404
        ]
        if final_cookies:
            cmd.extend(["-H", f"Cookie: {final_cookies}"])

        if self.method in ["POST", "PUT", "PATCH"]:
            cmd.extend(["-u", f"{self.base_url}/{self.path}"])
            cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
            cmd.extend(["-d", params_string])
        else:
            full_url_with_fuzz = f"{self.base_url}/{self.path}?{params_string}"
            cmd.extend(["-u", full_url_with_fuzz])

        logger.info(f"🚀 執行 ffuf 指令: {' '.join(cmd)}")

        # 5. 執行 ffuf 並捕獲輸出
        try:
            # 修改處：不再使用 DEVNULL，改為捕獲輸出以供偵錯
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # 打印 ffuf 的標準輸出與錯誤訊息 (偵錯用)
            if process.stdout:
                logger.info(f"--- ffuf STDOUT ---\n{process.stdout}")

            # 6. 解析結果
            results = []
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size == 0:
                    logger.error(
                        f"❌ 錯誤：ffuf 輸出檔案 {output_path} 是空的 (0 bytes)。這通常代表 ffuf 沒有找到任何匹配或執行失敗。"
                    )
                else:
                    with open(output_path, "r") as f:
                        content = f.read()
                        try:
                            data = json.loads(content)
                            results = data.get("results", [])
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"❌ 無法解析 ffuf 輸出的 JSON。內容前 500 字元: {content[:500]}"
                            )
                            logger.error(f"JSON 錯誤原因: {e}")
            else:
                logger.error(f"❌ 找不到 ffuf 輸出檔案: {output_path}")

            return results
        except Exception as e:
            logger.error(f"🔥 執行 subprocess 時發生異常: {e}")
            return []
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


@shared_task(name="http_sender.fuzz_endpoint")
@log_function_call()
def fuzz_endpoint(endpoint_id: int, cookies: Union[dict, str, None] = None):
    """
    Celery Task: 針對指定的 Endpoint 遍歷所有參數執行智慧 Fuzzing
    """
    client = get_graphql_client()

    # 執行 GraphQL 獲取 Endpoint 資料
    parsed_query = gql(endpoint_query)
    result = client.execute(parsed_query, variable_values={"id": endpoint_id})

    if not result.get("core_endpoint"):
        logger.error(f"找不到 ID 為 {endpoint_id} 的 Endpoint 資料")
        return {"error": "Endpoint not found"}

    endpoint_data = result["core_endpoint"][0]

    try:
        url_info = endpoint_data["core_endpoint_discovered_by_urls"][0][
            "core_urlresult"
        ]
        base_url = url_info["final_url"]
    except (IndexError, KeyError):
        logger.error("Endpoint 缺少對應的 URL 資訊")
        return {"error": "Missing URL information"}

    path = endpoint_data["path"]
    method = endpoint_data["method"]
    all_params = endpoint_data.get("core_urlparameters", [])

    if not all_params:
        logger.warning(f"Endpoint {endpoint_id} 沒有任何參數可供 Fuzzing。")
        return {"error": "No parameters to fuzz"}

    # --- 1. 預先處理使用者自定義的 Cookies ---
    user_cookie_str = ""
    if isinstance(cookies, dict):
        user_cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    elif isinstance(cookies, str):
        user_cookie_str = cookies

    all_fuzz_results = []

    # --- 2. 遍歷所有參數進行 Fuzzing ---
    for param in all_params:
        p_key = param.get("key", "")
        p_type = param.get("data_type", "string").lower()

        # 取得該參數最適合的字典
        payload_info = get_payload_for_parameter(p_key, p_type)

        # 確保路徑存在，否則使用預設
        if payload_info.get("paths"):
            selected_wordlist = payload_info["paths"][0]
        else:
            selected_wordlist = WORDLIST_MAP["default"]

        logger.info(f"🎯 準備爆破參數: [{p_key}] (類型: {p_type})")
        logger.info(f"📖 使用字典: {selected_wordlist}")

        # 初始化 Fuzzer
        fuzzer = Myfuzz(
            base_url=base_url,
            path=path,
            method=method,
            target_key=p_key,
            all_params=all_params,
            wordlist_path=selected_wordlist,
            flaresolverr_url=FLARESOLVERR_URL,
            user_cookies=user_cookie_str,
        )

        # 執行 Fuzzing
        current_param_results = fuzzer.run()

        # 如果該參數有發現匹配的結果（ffuf 找到了東西）
        if current_param_results:
            all_fuzz_results.append(
                {
                    "parameter": p_key,
                    "payload_type": payload_info.get("type", "unknown"),
                    "results": current_param_results,
                }
            )

    # --- 3. 處理並打印最終結果 ---
    if all_fuzz_results:
        logger.info(
            f"✨ Fuzzing 任務完成。在 {len(all_fuzz_results)} 個參數中發現了潛在問題："
        )

        for item in all_fuzz_results:
            param_name = item["parameter"]
            payload_type = item["payload_type"]
            hits = item["results"]

            logger.info(
                f"📦 參數 [{param_name}] (測試類型: {payload_type}) 發現 {len(hits)} 個匹配項："
            )

            for hit in hits:
                # 從 ffuf 的 JSON 結構中提取資訊
                payload_used = hit.get("input", {}).get("FUZZ", "N/A")
                status_code = hit.get("status")
                length = hit.get("length")

                logger.info(
                    f"   ∟ [Status: {status_code}] [Size: {length}] Payload: {payload_used}"
                )
    else:
        logger.info("🏁 Fuzzing 完成，所有參數均未發現匹配結果。")

    return all_fuzz_resultss
