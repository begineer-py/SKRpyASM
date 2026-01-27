# flaresolverr/orchestrators/bs4_handler.py

import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
from c2_core.config.logging import log_function_call

# 媽的，用 DEBUG 級別來看最詳細的情報，用 INFO 來看總結
# 你可以在 settings.py 裡調整日誌級別來控制輸出
logger = logging.getLogger(__name__)


class BS4Handler:
    """
    媽的，這是 BeautifulSoup 的專家。
    所有跟 HTML 解析相關的髒活累活都歸他管。
    吃進 HTML，吐出結構化的 JSON 數據。
    (v2.0 審訊室版本，帶全程詳細日誌)
    """

    @classmethod
    def get_empty_analysis(cls) -> Dict[str, Any]:
        return {
            "title": None,
            "forms": [],
            "links": [],
            "scripts": [],
            "comments": [],
            "meta_tags": [],
            "iframes": [],
            "cleaned_html": "",
            "extracted_js": "",
        }

    # 每個 _parse_* 方法都加上詳細日誌

    @log_function_call()
    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        logger.info("--- 開始解析 Title (<title>) ---")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            logger.info(f"成功提取 Title: '{title}'")
            return title
        logger.warning("未找到 <title> 標籤或內容為空。")
        return None

    @log_function_call()
    def _parse_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        logger.info("--- 開始解析表單 (<form>) ---")
        forms_data = []
        form_tags = soup.find_all("form")
        logger.info(f"找到 {len(form_tags)} 個 <form> 標籤。")
        for i, form_tag in enumerate(form_tags):
            logger.debug(f"  [表單 {i+1}/{len(form_tags)}] 正在處理...")
            action = form_tag.get("action", "")
            method = form_tag.get("method", "GET").upper()
            parameters = []
            input_tags = form_tag.find_all(["input", "textarea", "select", "button"])
            logger.debug(f"    - 在此表單中找到 {len(input_tags)} 個輸入相關標籤。")
            for tag in input_tags:
                name = tag.get("name")
                if not name:
                    logger.debug(f"      - 跳過一個沒有 'name' 屬性的標籤: {tag.name}")
                    continue
                # ... (其餘邏輯不變)
                parameters.append({"name": name, "type": tag.get("type", "text")})

            form_info = {"action": action, "method": method, "parameters": parameters}
            logger.debug(f"    - 收集到表單數據: {form_info}")
            forms_data.append(form_info)

        logger.info(f"表單解析完成，共收集到 {len(forms_data)} 個表單。")
        return forms_data

    @log_function_call()
    def _parse_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        logger.info("--- 開始解析連結 (<a>) ---")
        links = []
        a_tags = soup.find_all("a", href=True)
        logger.info(f"找到 {len(a_tags)} 個帶 'href' 的 <a> 標籤。")
        for i, tag in enumerate(a_tags):
            href = tag["href"]
            logger.debug(f"  [連結 {i+1}/{len(a_tags)}] 正在處理 href: '{href}'")

            if href.strip() and not href.startswith("#"):
                logger.debug(f"    - href 有效，準備合併 URL。")
                absolute_url = urljoin(base_url, href)
                link_data = {"text": tag.get_text(strip=True), "href": absolute_url}
                logger.debug(f"    - 收集到連結數據: {link_data}")
                links.append(link_data)
            else:
                logger.debug(f"    - 操，這個 href 是空的或是錨點，跳過。")

        logger.info(f"連結解析完成，共收集到 {len(links)} 條有效連結。")
        return links

    def _parse_iframes(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        logger.info("--- 開始解析內聯框架 (<iframe>) ---")
        iframes = []
        iframe_tags = soup.find_all("iframe", src=True)
        logger.info(f"找到 {len(iframe_tags)} 個帶 'src' 的 <iframe> 標籤。")
        for i, tag in enumerate(iframe_tags):
            src = tag["src"]
            logger.debug(f"  [Iframe {i+1}/{len(iframe_tags)}] 正在處理 src: '{src}'")
            absolute_src = urljoin(base_url, src)
            iframe_data = {"src": absolute_src}
            logger.debug(f"    - 收集到 iframe 數據: {iframe_data}")
            iframes.append(iframe_data)
        logger.info(f"Iframe 解析完成，共收集到 {len(iframes)} 個。")
        return iframes

    @log_function_call()
    def _parse_comments(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        logger.info("--- 開始解析註釋 (<!--...-->) ---")
        comments = []
        comment_nodes = soup.find_all(string=lambda text: isinstance(text, Comment))
        logger.info(f"找到 {len(comment_nodes)} 條註釋。")
        for i, comment in enumerate(comment_nodes):
            content = comment.strip()
            logger.debug(
                f"  [註釋 {i+1}/{len(comment_nodes)}] 內容 (前80字符): {content[:80]}"
            )
            comments.append({"content": content})
        logger.info(f"註釋解析完成，共收集到 {len(comments)} 條。")
        return comments

    @log_function_call()
    def _parse_meta_tags(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        logger.info("--- 開始解析元標籤 (<meta>) ---")
        meta_tags = []
        all_meta_tags = soup.find_all("meta")
        logger.info(f"找到 {len(all_meta_tags)} 個 <meta> 標籤。")
        for i, tag in enumerate(all_meta_tags):
            attrs = {k: v for k, v in tag.attrs.items()}
            logger.debug(f"  [Meta {i+1}/{len(all_meta_tags)}] 收集到屬性: {attrs}")
            meta_tags.append(attrs)
        logger.info(f"Meta 標籤解析完成，共收集到 {len(meta_tags)} 個。")
        return meta_tags

    @log_function_call()
    def _parse_scripts(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, Optional[str]]]:
        logger.info("--- 開始解析腳本 (<script>) ---")
        scripts = []
        script_tags = soup.find_all("script")
        logger.info(f"找到 {len(script_tags)} 個 <script> 標籤。")
        for i, tag in enumerate(script_tags):
            src = tag.get("src")
            logger.debug(
                f"  [腳本 {i+1}/{len(script_tags)}] 正在處理標籤: {str(tag)[:100]}..."
            )
            if src:
                logger.debug(f"    - 判斷為外部腳本。src: '{src}'")
                absolute_src = urljoin(base_url, src)
                script_data = {"src": absolute_src, "content": None}
                logger.debug(f"    - 收集到外部腳本數據: {script_data}")
                scripts.append(script_data)
            else:
                logger.debug(f"    - 判斷為內聯腳本。")
                content = tag.get_text(strip=True)
                if content:
                    logger.debug(
                        f"    - 成功提取內聯內容 (前80字符): {content[:80]}..."
                    )
                    script_data = {"src": None, "content": content}
                    scripts.append(script_data)
                else:
                    logger.debug(f"    - 內聯腳本內容為空，跳過。")
        logger.info(f"腳本解析完成，共收集到 {len(scripts)} 條。")
        return scripts

    @log_function_call()
    @log_function_call()
    def script_parse(self, scripts: List[Dict[str, Any]], base_url: str) -> str:
        logger.info("--- 開始重組 JS 代碼 (Extraction & Sanitation) ---")

        js_lines = []
        js_lines.append(f"/* extracted from {base_url} */\n")

        for script in scripts:
            s_type = script.get("type", "")

            # 1. 根據 Type 判斷 (既有邏輯)
            is_explicit_data = (
                "json" in s_type
                or "importmap" in s_type
                or "template" in s_type
                or "html" in s_type
            )

            # -----------------------------------------------------------
            # [新增] 2. 根據「內容」判斷 (針對那種沒寫 type 的隱形地雷)
            # -----------------------------------------------------------
            is_implicit_data = False
            raw_content = script.get("content", "")
            if raw_content:
                clean_content = raw_content.strip()
                # 特徵：以 { 開頭，以 } 結尾，且內容包含 "imports" 關鍵字
                # 這 100% 就是 ImportMap，絕對不是普通 JS
                if (
                    clean_content.startswith("{")
                    and clean_content.endswith("}")
                    and '"imports"' in clean_content
                ):
                    is_implicit_data = True

            # 只要符合任一條件，就當作垃圾處理
            should_ignore = is_explicit_data or is_implicit_data

            if script.get("src"):
                js_lines.append(
                    f"\n/* [EXTERNAL SCRIPT] SRC: {script['src']} (Type: {s_type}) */\n"
                )

            elif script.get("content"):
                content = script["content"].strip()

                if should_ignore:
                    # === 抓到了！隱藏的 JSON/ImportMap ===
                    # 把它包在註釋裡
                    js_lines.append(
                        f"\n/* [IGNORED DATA BLOCK] (Type: {s_type} - Detected via Sniffing)"
                    )
                    js_lines.append(content)
                    js_lines.append(f"*/\n")
                else:
                    # === 真正的 JS ===
                    js_lines.append(f"\n/* [INLINE SCRIPT START] (Type: {s_type}) */\n")
                    js_lines.append(content)

                    # 強制補分號
                    if not content.endswith(";"):
                        js_lines.append(";")

                    js_lines.append(f"\n/* [INLINE SCRIPT END] */\n")

        js_content = "\n".join(js_lines)
        logger.info(f"JS 內容重組完成，總長度: {len(js_content)} 字元")
        return js_content

    @log_function_call()
    def analyze_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        logger.info(
            f"BS4Handler 開始對 base_url='{base_url}' 的 HTML 內容進行全面分析。"
        )
        if not html_content:
            logger.warning("傳入的 HTML 內容為空，返回空的分析結果。")
            return self.get_empty_analysis()

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            logger.info(f"傳入的 Base URL: {base_url}")

            # 1. 先抓資料
            title = self._parse_title(soup)
            forms = self._parse_forms(soup)
            links = self._parse_links(soup, base_url)
            scripts = self._parse_scripts(soup, base_url)  # 這裡已經拿到 script 列表了
            comments = self._parse_comments(soup)
            meta_tags = self._parse_meta_tags(soup)
            iframes = self._parse_iframes(soup, base_url)
            extracted_js = self.script_parse(scripts, base_url)

            # --- [新增邏輯] 組合純 JS 字串 ---
            # 把碎片化的 script list 縫合成一個大的 JS 檔案內容

            # 2. 再洗 HTML (大掃除)
            logger.info("正在執行 HTML 清洗，移除 <script> 和 <style> 標籤...")
            for junk in soup.find_all(["script", "style"]):
                junk.decompose()

            cleaned_html = soup.prettify()

            # 3. 封裝結果
            analysis_result = {
                "title": title,
                "forms": forms,
                "links": links,
                "scripts": scripts,
                "comments": comments,
                "meta_tags": meta_tags,
                "iframes": iframes,
                "cleaned_html": cleaned_html,  # 骨
                "extracted_js": extracted_js,  # 肉 (一定要存這個！)
            }

            # --- 最終總結報告 ---
            logger.info(
                f"BS4Handler 完成全方位分析。摘要: "
                f"Title='{bool(title)}', "
                f"Forms={len(forms)}, Links={len(links)}, Scripts={len(scripts)}, "
                f"Comments={len(comments)}, Meta={len(meta_tags)}, Iframes={len(iframes)}"
            )

            return analysis_result

        except Exception as e:
            logger.exception(f"媽的，BS4Handler 在解析 HTML 時發生了致命錯誤: {e}")
            return self.get_empty_analysis()
