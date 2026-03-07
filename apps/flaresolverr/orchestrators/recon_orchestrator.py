import os
import logging
from typing import List, Dict, Any, Optional

from c2_core.config.logging import log_function_call
from .bs4_handler import BS4Handler
import hashlib

from ..my_spider import MySpider
from ..web_tech.tech_scanner import TechScanner
from apps.flaresolverr.gf.hacker_gf.pygf import PatternAnalyzer
from apps.flaresolverr.spider_utils.content_type import ContentTypeDetector
from apps.flaresolverr.url_scanner.html_scanner import XurlsScanner
from apps.flaresolverr.url_scanner.jsluice import jsluice
from .utils import process_all_discovered_links
from apps.flaresolverr.security_parser import SecurityAnalyzer


logger = logging.getLogger(__name__)


class ReconOrchestrator:
    """
    v2.0 指揮官 (Refactored):
    具備錯誤感知能力，根據 Spider 的回傳狀態動態決定執行哪些分析模組。
    """

    def __init__(self, url: str, method: str = "GET", cookie_string: str = ""):
        self.url = url
        self.method = method
        self.cookie_string = cookie_string
        self.spider = MySpider(
            url=self.url,
            method=self.method,
            cookie_string=self.cookie_string,
            flaresolverr_url=os.getenv("FLARESOLVERR_URL") or "http://127.0.0.1:8191",
        )
        self.analyzer = PatternAnalyzer()
        self.tech_scanner = TechScanner()
        self.bs4_handler = BS4Handler()
        self.content_fetch_status = "PENDING"
        self.param_hunter = SecurityAnalyzer()
        logger.info(f"指揮官就位，目標鎖定: {self.url}")

    def _get_base_result(self, final_url: str = None) -> Dict[str, Any]:
        """
        [輔助方法] 生成一個標準的、空的結果字典。
        確保無論在哪個階段退出，回傳的資料結構都是一致的，避免 KeyError。
        """
        return {
            "success": False,  # 預設失敗，成功流程會覆寫為 True
            "final_url": final_url or self.url,
            "error": None,
            "spider_result": {},
            "analysis_result": [],
            "tech_stack_result": {
                "technologies": [],
                "fingerprints_matched": [],
                "error": None,
            },
            "forms_result": [],
            "used_flaresolverr": False,
            "links_result": [],
            "scripts_result": [],
            "comments_result": [],
            "meta_tags_result": [],
            "iframes_result": [],
            "content_fetch_status": "PENDING",
            "raw_response_hash": "",
            "cleaned_html": "",
            "extracted_js": "",
            "processed_links": {"internal": [], "external": []},
            "text": "",
        }

    @log_function_call()
    def run(self) -> dict:
        logger.info(f"作戰開始: {self.url}")

        # 初始化基礎結果結構
        result = self._get_base_result()

        # --- 第一階段：派遣先鋒部隊 (Spider Fetch) ---
        response_data, used_flaresolverr, self.content_fetch_status = self.spider.send()

        # 填充基礎資訊
        result["used_flaresolverr"] = used_flaresolverr
        result["content_fetch_status"] = self.content_fetch_status
        result["spider_result"] = response_data or {}
        logger.info(response_data["content_length"])
        # 獲取重要參數
        final_url = (
            response_data.get("response_url", self.url) if response_data else self.url
        )
        result["final_url"] = final_url
        status_code = response_data.get("status_code", 0) if response_data else 0

        logger.info(
            f"先鋒部隊回報: {self.url} -> Status: {self.content_fetch_status} (Code: {status_code})"
        )

        # =========================================================================
        # 錯誤路由處理 (Error Routing)
        # =========================================================================

        # 1. [致命錯誤]：連線失敗、DNS 錯誤、超時
        # 這些情況下沒有 Headers 也沒有 Body，什麼都分析不了，直接退出。
        FATAL_ERRORS = ["FAILED_DNS_ERROR", "FAILED_NETWORK_ERROR", "FAILED_TIMEOUT"]
        if self.content_fetch_status in FATAL_ERRORS:
            logger.error(f"遭遇致命錯誤 {self.content_fetch_status}，中止任務。")
            result["error"] = self.content_fetch_status
            result["success"] = False  # 標記為失敗
            return result

        # 2. [部分資料]：被攔截 (Blocked)、無內容 (No Content)、客戶端/伺服器錯誤 (4xx/5xx)
        # 這些情況下我們通常有 Headers，可以跑 TechStack，但不能跑 BS4/HackerGF。
        PARTIAL_SUCCESS_STATUSES = [
            "FAILED_BLOCKED",
            "FAILED_NO_CONTENT",
            "FAILED_CLIENT_ERROR",
            "FAILED_SERVER_ERROR",
        ]

        # 進行內容類型檢測 (即使失敗也可能有 Content-Type header)
        content_type, is_text_content, is_binary_url = ContentTypeDetector(
            response_data, used_flaresolverr, self.content_fetch_status, self.url
        ).detect()

        # 如果是二進制文件，也視為一種「部分成功」(不需要深入分析)
        is_partial_analysis = (
            self.content_fetch_status in PARTIAL_SUCCESS_STATUSES
        ) or is_binary_url

        if is_partial_analysis:
            logger.warning(
                f"進入部分分析模式 (Status: {self.content_fetch_status}, Binary: {is_binary_url})。僅執行 TechScan。"
            )

            # 執行 TechScan (只依賴 Headers 和 Cookie)
            tech_result = self._run_tech_scan(
                response_data, result["final_url"], is_text_content=False
            )  # 強制不傳 Body
            result["tech_stack_result"] = tech_result
            result["success"] = True  # 任務本身算執行完成，雖然沒拿到內容

            # 如果是被攔截，記錄錯誤訊息
            if self.content_fetch_status == "FAILED_BLOCKED":
                result["error"] = "WAF Blocked"

            return result

        # 3. [完全成功]：SUCCESS_FETCHED (且不是二進制)
        # 只有這種情況才執行耗時的 BS4 解析和正則匹配
        if self.content_fetch_status in [
            "SUCCESS_FETCHED",
            "SUCCESS_REDIRECTED_EXTERNAL",
        ]:
            logger.info("進入全量分析模式。")

            # --- A. 技術偵測 (TechScanner) ---
            # 這裡傳入完整的 response_text
            tech_result = self._run_tech_scan(
                response_data, result["final_url"], is_text_content=True
            )
            result["tech_stack_result"] = tech_result

            # --- B. HTML 結構化分析 (BS4Handler) ---
            response_text = response_data.get("response_text", "")
            bs4_result = self._run_bs4_analysis(response_text, result["final_url"])

            # 合併 BS4 結果到主結果
            result.update(bs4_result)

            # 更新 Title (如果 BS4 找到了更好的)
            if bs4_result.get("title"):
                result["spider_result"]["title"] = bs4_result.get("title")

            # --- C. 情報洩漏分析 (HackerGF) ---
            # HackerGF 吃資源，只在有內容時跑
            if response_text:
                lines = response_text.splitlines()
                result["analysis_result"] = self.analyzer.run_all_patterns(lines)
                logger.info(
                    f"HackerGF 發現 {len(result['analysis_result'])} 個潛在點。"
                )

            # --- D. 高級連結提取 (JS & Comments) ---
            extracted_links = self._extract_advanced_links(
                result["extracted_js"], result["comments_result"]
            )

            # --- E. 連結池聚合 (Link Pooling) ---
            raw_link_pool = []
            # 來自 BS4
            if result["links_result"]:
                raw_link_pool.extend(
                    [l.get("href") for l in result["links_result"] if l.get("href")]
                )
            # 來自 高級提取
            raw_link_pool.extend(extracted_links)

            # --- F. 連結歸一化 ---
            logger.info(f"正在處理共 {len(raw_link_pool)} 個原始連結標籤...")
            processed_links = process_all_discovered_links(
                result["final_url"], raw_link_pool
            )
            result["processed_links"] = processed_links

            # 補充雜項
            result["raw_response_hash"] = response_data.get("md5", "")
            result["success"] = True

            logger.info(
                f"作戰成功結束，內鏈: {len(processed_links['internal'])}, 外鏈: {len(processed_links['external'])}"
            )
            return result

        # 4. [未知狀態]
        # 理論上不該到這裡，但為了保底
        logger.error(f"未處理的狀態: {self.content_fetch_status}")
        result["error"] = f"Unhandled status: {self.content_fetch_status}"
        return result

    # =========================================================================
    # 私有方法：將邏輯拆分，讓 run() 更乾淨
    # =========================================================================

    def _run_tech_scan(
        self, spider_data: dict, url: str, is_text_content: bool
    ) -> dict:
        """執行技術棧掃描並合併 Httpx 原生結果"""
        try:
            response_text = (
                spider_data.get("response_text", "") if is_text_content else ""
            )

            # 1. Python TechScanner
            tech_stack_data = self.tech_scanner.scan(
                response_headers=spider_data.get("response_headers", {}),
                response_text=response_text,
                response_cookies=spider_data.get("response_cookies", {}),
                url=url,
            )

            # 2. 合併 Docker Httpx 的原生結果
            httpx_tech_list = spider_data.get("tech", [])
            existing_tech_names = {
                item["name"].lower()
                for item in tech_stack_data.get("fingerprints_matched", [])
            }

            if httpx_tech_list:
                for tech_str in httpx_tech_list:
                    parts = tech_str.split(":")
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else None

                    if name.lower() not in existing_tech_names:
                        tech_stack_data["fingerprints_matched"].append(
                            {
                                "name": name,
                                "version": version,
                                "categories": [],
                                "source": "httpx",
                            }
                        )
                        existing_tech_names.add(name.lower())

            return tech_stack_data
        except Exception as e:
            logger.error(f"TechScan 執行失敗: {e}")
            return {"technologies": [], "fingerprints_matched": [], "error": str(e)}

    def _run_bs4_analysis(self, html_text: str, base_url: str) -> dict:
        """執行 BS4 HTML 分析"""
        try:
            if not html_text:
                return {}

            analysis = self.bs4_handler.analyze_html(html_text, base_url=base_url)
            if not analysis:
                return {}

            # 將 BS4 的輸出鍵名映射到 Orchestrator 的輸出鍵名
            return {
                "forms_result": analysis.get("forms", []),
                "links_result": analysis.get("links", []),
                "scripts_result": analysis.get("scripts", []),
                "comments_result": analysis.get("comments", []),
                "meta_tags_result": analysis.get("meta_tags", []),
                "iframes_result": analysis.get("iframes", []),
                "cleaned_html": analysis.get("cleaned_html", ""),
                "extracted_js": analysis.get("extracted_js", ""),
                "text": analysis.get("text", ""),
                # title 會在外部處理
                "title": analysis.get("title"),
            }
        except Exception as e:
            logger.error(f"BS4 分析失敗: {e}")
            return {}

    def _extract_advanced_links(
        self, extracted_js: str, comments_found: List[Dict]
    ) -> List[str]:
        """從 JS 和 註解中提取連結"""
        links = []

        # 1. JS Link Extraction
        if extracted_js:
            try:
                js_obj = jsluice(extracted_js)
                js_links = js_obj.js_files_scan()
                links.extend(js_links)
                logger.debug(f"JSLuice 提取了 {len(js_links)} 個連結")
            except Exception as e:
                logger.error(f"JSLuice 分析失敗: {e}")

        # 2. Comment Link Extraction
        if comments_found:
            try:
                data = "\n".join([c["content"] for c in comments_found])
                html_obj = XurlsScanner(data)
                comment_links = html_obj.scan()
                links.extend(comment_links)
                logger.debug(f"XurlsScanner 從註解提取了 {len(comment_links)} 個連結")
            except Exception as e:
                logger.error(f"XurlsScanner 分析失敗: {e}")

        return links
