# flaresolverr/orchestrators/bs4_handler.py

import logging
from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
from c2_core.config.logging import log_function_call

# 設置日誌
logger = logging.getLogger(__name__)


class BS4Handler:
    """
    BeautifulSoup 解析專家類別。
    """

    @classmethod
    def get_empty_analysis(cls) -> Dict[str, Any]:
        """
        回傳初始化的空分析結果字典。
        """
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
            "text": "",
        }

    # @log_function_call()
    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        logger.info("--- 開始解析 Title (<title>) ---")
        if soup.title and soup.title.string:
            title: str = soup.title.string.strip()
            logger.info(f"成功提取 Title: '{title}'")
            return title
        logger.warning("未找到 <title> 標籤或內容為空。")
        return None

    # @log_function_call()
    def _parse_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        logger.info("--- 開始解析表單 (<form>) ---")
        forms_data: List[Dict[str, Any]] = []
        form_tags = soup.find_all("form")
        logger.info(f"找到 {len(form_tags)} 個 <form> 標籤。")

        for i, form_tag in enumerate(form_tags):
            logger.debug(f"  [表單 {i+1}/{len(form_tags)}] 正在處理...")
            action: str = form_tag.get("action", "")
            method: str = form_tag.get("method", "GET").upper()

            parameters: List[Dict[str, str]] = []
            input_tags = form_tag.find_all(["input", "textarea", "select", "button"])

            for tag in input_tags:
                name: Optional[str] = tag.get("name")
                if not name:
                    continue
                parameters.append({"name": name, "type": str(tag.get("type", "text"))})

            form_info: Dict[str, Any] = {
                "action": action,
                "method": method,
                "parameters": parameters,
            }
            forms_data.append(form_info)

        return forms_data

    # @log_function_call()
    def _parse_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        logger.info("--- 開始解析連結 (<a>) ---")
        links: List[Dict[str, str]] = []
        a_tags = soup.find_all("a", href=True)

        for i, tag in enumerate(a_tags):
            href: str = tag["href"]
            if href.strip() and not href.startswith("#"):
                absolute_url: str = urljoin(base_url, href)
                link_data: Dict[str, str] = {
                    "text": tag.get_text(strip=True),
                    "href": absolute_url,
                }
                links.append(link_data)
        return links

    # @log_function_call()
    def _parse_iframes(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        logger.info("--- 開始解析內聯框架 (<iframe>) ---")
        iframes: List[Dict[str, str]] = []
        iframe_tags = soup.find_all("iframe", src=True)

        for i, tag in enumerate(iframe_tags):
            src: str = tag["src"]
            absolute_src: str = urljoin(base_url, src)
            iframes.append({"src": absolute_src})
        return iframes

    # @log_function_call()
    def _parse_comments(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        logger.info("--- 開始解析註釋 (<!--...-->) ---")
        comments: List[Dict[str, str]] = []
        comment_nodes = soup.find_all(string=lambda text: isinstance(text, Comment))

        for comment in comment_nodes:
            content: str = comment.strip()
            comments.append({"content": content})
        return comments

    # @log_function_call()
    def _parse_meta_tags(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        logger.info("--- 開始解析元標籤 (<meta>) ---")
        meta_tags: List[Dict[str, Any]] = []
        all_meta_tags = soup.find_all("meta")

        for tag in all_meta_tags:
            # tag.attrs 回傳的是 Dict[str, Union[str, List[str]]]
            attrs: Dict[str, Any] = {k: v for k, v in tag.attrs.items()}
            meta_tags.append(attrs)
        return meta_tags

    # @log_function_call()
    def _parse_scripts(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, Optional[str]]]:
        logger.info("--- 開始解析腳本 (<script>) ---")
        scripts: List[Dict[str, Optional[str]]] = []
        script_tags = soup.find_all("script")

        for tag in script_tags:
            src: Optional[str] = tag.get("src")
            s_type: str = tag.get("type", "")

            if src:
                scripts.append(
                    {"src": urljoin(base_url, src), "content": None, "type": s_type}
                )
            else:
                content: str = tag.get_text(strip=True)
                if content:
                    scripts.append({"src": None, "content": content, "type": s_type})
        return scripts

    @log_function_call()
    def _parse_text(self, soup: BeautifulSoup) -> str:
        """
        [新增] 提取純淨的人類可讀內文。
        """
        logger.info("--- 開始提取純文字內容 ---")
        # 拷貝一份 soup，避免影響到其他的解析
        temp_soup = BeautifulSoup(str(soup), "html.parser")

        # 1. 踢掉絕對不是人類閱讀內容的標籤
        for junk in temp_soup(
            ["script", "style", "meta", "noscript", "header", "footer", "nav"]
        ):
            junk.decompose()

        # 2. 獲取文字，用換行符號隔開，避免文字擠在一起
        # strip=True 會修剪掉多餘空格
        pure_text = temp_soup.get_text(separator="\n", strip=True)

        logger.info(f"成功提取純文字，長度: {len(pure_text)}")
        return pure_text

    # @log_function_call()
    def script_parse(self, scripts: List[Dict[str, Any]], base_url: str) -> str:
        """
        將碎片化的 Script 列表重組成完整的 JS 字串。
        """
        logger.info("--- 開始重組 JS 代碼 ---")
        js_lines: List[str] = [f"/* extracted from {base_url} */\n"]

        for script in scripts:
            s_type: str = str(script.get("type", ""))
            raw_content: Optional[str] = script.get("content")
            src: Optional[str] = script.get("src")

            # 判定是否為數據塊而非執行碼
            is_explicit_data: bool = any(
                x in s_type for x in ["json", "importmap", "template", "html"]
            )
            is_implicit_data: bool = False

            if raw_content:
                clean_content: str = raw_content.strip()
                if (
                    clean_content.startswith("{")
                    and clean_content.endswith("}")
                    and '"imports"' in clean_content
                ):
                    is_implicit_data = True

            should_ignore: bool = is_explicit_data or is_implicit_data

            if src:
                js_lines.append(
                    f"\n/* [EXTERNAL SCRIPT] SRC: {src} (Type: {s_type}) */\n"
                )
            elif raw_content:
                content: str = raw_content.strip()
                if should_ignore:
                    js_lines.append(
                        f"\n/* [IGNORED DATA BLOCK] (Type: {s_type})\n{content}\n*/\n"
                    )
                else:
                    js_lines.append(
                        f"\n/* [INLINE SCRIPT START] (Type: {s_type}) */\n{content}"
                    )
                    if not content.endswith(";"):
                        js_lines.append(";")
                    js_lines.append("\n/* [INLINE SCRIPT END] */\n")

        return "\n".join(js_lines)

    # @log_function_call()
    def analyze_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        執行全方位的 HTML 分析。
        """
        logger.info(f"BS4Handler 開始分析 HTML。Base URL: {base_url}")
        if not html_content:
            return self.get_empty_analysis()

        try:
            soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")

            # 1. 解析各項組件
            title: Optional[str] = self._parse_title(soup)
            forms: List[Dict[str, Any]] = self._parse_forms(soup)
            links: List[Dict[str, str]] = self._parse_links(soup, base_url)
            scripts_list: List[Dict[str, Any]] = self._parse_scripts(soup, base_url)
            comments: List[Dict[str, str]] = self._parse_comments(soup)
            meta_tags: List[Dict[str, Any]] = self._parse_meta_tags(soup)
            iframes: List[Dict[str, str]] = self._parse_iframes(soup, base_url)
            pure_text = self._parse_text(soup)

            # 2. 提取 JS
            extracted_js: str = self.script_parse(scripts_list, base_url)

            # 3. 清洗 HTML
            for junk in soup.find_all(["script", "style"]):
                junk.decompose()
            cleaned_html: str = soup.prettify()

            # 4. 回傳封裝
            result: Dict[str, Any] = {
                "title": title,
                "forms": forms,
                "links": links,
                "scripts": scripts_list,
                "comments": comments,
                "meta_tags": meta_tags,
                "iframes": iframes,
                "cleaned_html": cleaned_html,
                "extracted_js": extracted_js,
                "text": pure_text,
            }

            logger.info("BS4Handler 分析完成。")
            return result

        except Exception as e:
            logger.exception(f"解析失敗: {e}")
            return self.get_empty_analysis()
