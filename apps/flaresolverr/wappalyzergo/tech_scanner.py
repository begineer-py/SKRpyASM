# flaresolverr/web_tech/tech_scanner.py
import os
import json
import re
import logging

# 媽的，引入這個第三方庫！這才是現成貨！
try:
    from Wappalyzer import Wappalyzer, WebPage
except ImportError:
    logging.error(
        "媽的，找不到 `python-wappalyzer` 庫！請執行 `pip install python-wappalyzer`。"
    )

    # 提供一個假實現，避免崩潰
    class Wappalyzer:
        def __init__(self, *args, **kwargs):
            pass

        def analyze(self, webpage):
            logging.warning("Wappalyzer 庫未安裝，技術偵測功能將不可用。")
            return []

    class WebPage:
        def __init__(self, url, html, headers, *args, **kwargs):
            pass


logger = logging.getLogger(__name__)


class TechScanner:
    """
    媽的，這是網站技術偵測器！
    它會吃進 HTTP 響應頭、響應體和 Cookie，
    然後直接用 `python-wappalyzer` 這個現成貨來識別網站使用了什麼技術。
    """

    def __init__(self):
        try:
            # 使用最新的指紋數據
            # 媽的，這裡 Wappalyzer.latest() 可能會返回一個 set，導致後面沒有 .analyze 方法
            # 檢查一下 Wappalyzer 庫的原始碼，`latest` 應該返回 Wappalyzer 實例
            self.wappalyzer_instance = Wappalyzer.latest()
            logger.info("TechScanner 初始化完成，已加載 `python-wappalyzer`。")
        except Exception as e:
            logger.error(
                f"媽的，初始化 `python-wappalyzer` 失敗: {e}。技術偵測功能可能受限。"
            )
            self.wappalyzer_instance = None  # 標記為不可用

    @log_function_call()
    def scan(
        self,
        response_headers: dict,
        response_text: str,
        response_cookies: dict,
        url: str,
    ) -> dict:
        """
        執行技術掃描，透過 `python-wappalyzer` 庫來獲取結果。

        Parameters
        ----------
        response_headers : dict
            HTTP 響應頭的字典。
        response_text : str
            HTTP 響應體的文本內容。
        response_cookies : dict
            HTTP 響應中包含的 Cookie 字典。
        url : str
            原始請求的 URL，或最終重定向後的 URL。

        Returns
        -------
        dict
            包含偵測到的技術列表和匹配詳情。
            範例:
            {
                "technologies": ["Nginx", "jQuery"],
                "fingerprints_matched": [
                    {"tech_name": "Nginx", "match_type": "header", "key": "Server", "value": "nginx/1.20.1"},
                    {"tech_name": "jQuery", "match_type": "body", "pattern": "jquery\\.min\\.js", "value": "<script src=\"jquery.min.js\">"}
                ],
                "error": null
            }
        """
        result = {"technologies": [], "fingerprints_matched": [], "error": None}

        if not self.wappalyzer_instance:
            logger.error("`python-wappalyzer` 實例不可用，跳過技術掃描。")
            result["error"] = "python-wappalyzer instance not initialized"
            return result

        logger.debug(f"呼叫 `python-wappalyzer` 進行掃描 for URL: {url}")

        try:
            # 媽的，這裡的 `url` 參數很重要，要從 MySpider 的 response_url 傳過來！
            # `WebPage` 構造器可能需要原始的 headers 字典，而不是 httpx.Headers 物件
            # 我們傳入的 dict(response.headers) 是正確的
            webpage = WebPage(url=url, html=response_text, headers=response_headers)

            # 執行分析
            # wappalyzer.analyze() 返回的是一個集合 (set) 或列表，包含技術名稱字符串
            # 或者，如果是 analyze_with_versions_and_categories，它返回的是字典列表
            # 我們的目標是獲得更詳細的字典列表，所以要用 analyze_with_versions_and_categories

            # 媽的，`python-wappalyzer` 的 `analyze()` 方法只返回一個技術名稱的集合！
            # 如果要版本和類別，得調用 `analyze_with_versions_and_categories()`。
            # 讓我們使用最詳盡的那個，並適應它的輸出格式。
            detected_apps_raw = (
                self.wappalyzer_instance.analyze_with_versions_and_categories(webpage)
            )

            technologies = []
            fingerprints_info = []

            # 檢查 detected_apps_raw 是否為字典，因為 `analyze_with_versions_and_categories` 返回的是字典
            if isinstance(detected_apps_raw, dict):
                for tech_name, tech_data in detected_apps_raw.items():
                    technologies.append(tech_name)
                    fingerprints_info.append(
                        {
                            "tech_name": tech_name,
                            "version": (
                                tech_data.get("versions", ["N/A"])[0]
                                if tech_data.get("versions")
                                else "N/A"
                            ),
                            "categories": [
                                cat for cat in tech_data.get("categories", [])
                            ],
                            "confidence": tech_data.get(
                                "confidenceTotal", "N/A"
                            ),  # 庫裡有個 confidenceTotal
                            "match_type": "N/A",  # python-wappalyzer 不會提供這麼細的匹配類型
                            "key": "N/A",
                            "pattern": "N/A",
                            "value": "N/A",
                        }
                    )
            else:  # 如果不是預期的字典，那就退化處理，只記錄原始輸出
                result["error"] = (
                    f"Unexpected output format from python-wappalyzer: {type(detected_apps_raw).__name__}"
                )
                logger.warning(result["error"])
                # 嘗試從原始輸出中提取技術名稱，如果它是集合或列表
                if isinstance(detected_apps_raw, (set, list)):
                    technologies = sorted(list(detected_apps_raw))
                    fingerprints_info = [
                        {
                            "tech_name": t,
                            "version": "N/A",
                            "categories": [],
                            "confidence": "N/A",
                            "match_type": "N/A",
                            "key": "N/A",
                            "pattern": "N/A",
                            "value": "N/A",
                        }
                        for t in technologies
                    ]

            result["technologies"] = sorted(list(set(technologies)))  # 去重並排序
            result["fingerprints_matched"] = fingerprints_info

            logger.debug(f"TechScanner 完成掃描，偵測到技術: {result['technologies']}")

        except Exception as e:
            logger.exception(
                f"媽的，執行 `python-wappalyzer` 時發生未知錯誤。錯誤: {e}"
            )
            result["error"] = str(e)

        return result
