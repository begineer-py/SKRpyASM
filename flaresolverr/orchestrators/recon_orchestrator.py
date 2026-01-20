import os
import logging
from typing import List, Dict, Any
from .bs4_handler import BS4Handler
import hashlib

from ..my_spider import MySpider
from ..web_tech.tech_scanner import TechScanner
from flaresolverr.gf.hacker_gf.pygf import PatternAnalyzer
from flaresolverr.spider_utils.content_type import ContentTypeDetector

logger = logging.getLogger(__name__)


class ReconOrchestrator:
    """
    v1.0 指揮官：
    1. 負責協調 MySpider, TechScanner 和 PatternAnalyzer。
    2. 吃進一個 URL，吐出一個包含所有戰果的字典。
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

        logger.info(f"指揮官就位，目標鎖定: {self.url}")

    def run(self) -> dict:
        logger.info(f"作戰開始: {self.url}")

        # --- 第一階段：派遣先鋒部隊 (MySpider) ---
        # response_data 是一個 dict (raw data from httpx or standard data from flaresolverr)
        response_data, used_flaresolverr, self.content_fetch_status = self.spider.send()

        tech_stack_data = {
            "technologies": [],
            "fingerprints_matched": [],
            "error": "Spider failed, tech scan skipped.",
        }
        content_type, is_text_content, is_binary_url = ContentTypeDetector(
            response_data, used_flaresolverr, self.content_fetch_status, self.url
        ).detect()
        # [修正點 1] 使用 .get() 獲取狀態碼，因為 response_data 是字典
        status_code = response_data.get("status_code")
        logger.info(f"先鋒部隊成功返回情報 for {self.url}, 狀態碼: {status_code}")

        # --- 第二階段：情報整理 ---
        # MySpider.send() 已直接回傳標準 JSON，這裡直接使用
        spider_json_report = response_data
        # 準備響應文本
        response_text = spider_json_report.get("response_text", "")

        # --- 第三階段：技術偵測 (TechScanner) ---
        # 注意：如果是 Httpx 來源，spider_json_report 裡可能已經帶有 "tech" 欄位
        # 但為了保險和統一，我們還是跑一遍 Python 版的 TechScanner (如果需要處理 raw headers/html)
        # 或者，如果 spider_json_report 已經有 tech，我們可以合併

        tech_stack_data = self.tech_scanner.scan(
            response_headers=spider_json_report.get("response_headers", {}),
            response_text=(response_text if is_text_content else ""),
            response_cookies=spider_json_report.get("response_cookies", {}),
            url=spider_json_report.get("response_url", self.url),
        )
        md5 = response_data["md5"]
        # 2. 合併 Httpx 原生偵測結果 (補強)
        # Httpx 返回格式通常是 list of strings: ["Nginx", "PHP:7.4", "React"]
        httpx_tech_list = spider_json_report.get("tech", [])

        # 取得目前已有的技術名稱集合 (避免重複)
        existing_tech_names = {
            item["name"].lower()
            for item in tech_stack_data.get("fingerprints_matched", [])
        }

        # 準備要追加的列表
        matched_fingerprints = tech_stack_data.get("fingerprints_matched", [])

        if httpx_tech_list:
            logger.info(f"Httpx 原生偵測到: {httpx_tech_list}")
            for tech_str in httpx_tech_list:
                # 解析 "Name:Version" 或 "Name"
                parts = tech_str.split(":")
                name = parts[0]
                version = parts[1] if len(parts) > 1 else None

                # 如果這個技術還沒被記錄，就加進去
                if name.lower() not in existing_tech_names:
                    matched_fingerprints.append(
                        {
                            "name": name,
                            "version": version,
                            "categories": [],  # Httpx 不提供分類，留空
                            "source": "httpx",  # 標記來源 (可選)
                        }
                    )
                    existing_tech_names.add(name.lower())

        # 更新回去
        tech_stack_data["fingerprints_matched"] = matched_fingerprints
        # --- 第四階段：HTML 結構化分析 (BS4Handler) ---
        html_analysis = self.bs4_handler.get_empty_analysis()

        if is_text_content and not is_binary_url:
            final_url = spider_json_report.get("response_url", self.url)
            html_analysis = (
                self.bs4_handler.analyze_html(response_text, base_url=final_url)
                or html_analysis
            )
            logger.info(f"HTML 分析完成。Title: {html_analysis.get('title')}")
        else:
            logger.info(f"跳過 HTML 分析 (非 HTML 內容或內容為空)。")

        # 提取 BS4 分析結果
        extracted_title = html_analysis.get("title")
        forms_found = html_analysis.get("forms", [])
        links_found = html_analysis.get("links", [])
        scripts_found = html_analysis.get("scripts", [])
        comments_found = html_analysis.get("comments", [])
        meta_tags_found = html_analysis.get("meta_tags", [])
        iframes_found = html_analysis.get("iframes", [])

        # 更新 Spider 報告中的標題 (如果 BS4 找到了更好的)
        if extracted_title:
            spider_json_report["title"] = extracted_title

        # --- 第五階段：情報洩漏分析 (HackerGF) ---
        analysis_findings = []

        if is_text_content and response_text and not is_binary_url:
            lines = response_text.splitlines()
            analysis_findings = self.analyzer.run_all_patterns(lines)
            logger.info(f"HackerGF 分析完成，發現 {len(analysis_findings)} 個潛在點。")
        else:
            logger.info(f"跳過 HackerGF 分析。")

        # --- 第六階段：打包最終戰報 ---
        logger.info(f"作戰成功結束 for {self.url}")
        actual_final_url = spider_json_report.get("response_url", self.url)

        return {
            "success": True,
            "final_url": actual_final_url,
            "error": None,
            "spider_result": spider_json_report,
            "analysis_result": analysis_findings,
            "tech_stack_result": tech_stack_data,
            "forms_result": forms_found,
            "used_flaresolverr": used_flaresolverr,
            "links_result": links_found,
            "scripts_result": scripts_found,
            "comments_result": comments_found,
            "meta_tags_result": meta_tags_found,
            "iframes_result": iframes_found,
            "content_fetch_status": self.content_fetch_status,
            "raw_response_hash": md5,
        }
