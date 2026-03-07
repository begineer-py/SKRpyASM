import re
import tldextract
from urllib.parse import urljoin, urlparse


def robust_link_resolver(base_url: str, raw_link: str) -> str:
    """
    使用 tldextract 精準識別域名與路徑，解決 index.php 誤判問題。
    """
    raw_link = raw_link.strip()
    if not raw_link:
        return None

    # 1. 優先處理具備協議特徵的 URL (https://, http://, //)
    # urljoin 會自動處理這些情況，直接返回正確的絕對 URL
    if re.match(r"^(https?:)?//", raw_link, re.IGNORECASE):
        return urljoin(base_url, raw_link)

    # 2. 處理以斜槓開頭的絕對路徑 (e.g., /api/v1/user)
    if raw_link.startswith("/"):
        return urljoin(base_url, raw_link)

    # 3. 提取第一個路徑片段，判斷其是否為「域名」
    # 例如: "api.target.com/v1" -> first_segment 是 "api.target.com"
    # 例如: "index.php?id=1" -> first_segment 是 "index.php"
    first_segment = raw_link.split("/")[0]

    # 過濾掉以點開頭的相對路徑 (e.g., ./path, ../path)
    if not raw_link.startswith("."):
        # 使用 tldextract 解析該片段
        ext = tldextract.extract(first_segment)

        # tldextract 的邏輯：
        # 如果是域名 (api.google.com): domain="google", suffix="com"
        # 如果是文件 (index.php): domain="index", suffix="" (因為 .php 不是公認的頂級域名)
        # 如果是 IP (1.1.1.1): domain="1.1.1.1", suffix=""

        if ext.suffix and ext.domain:
            # 只有當它同時具備「主域名」和「合法公網後綴」時，才判定為漏掉協議的域名
            potential_url = f"https://{raw_link}"
            return potential_url

        # 額外處理 IP 地址的情況 (tldextract 對純 IP 的 suffix 為空)
        # 簡單的正則檢查是否為 IP
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}", first_segment):
            return f"https://{raw_link}"

    # 4. 剩下的全部交給 urljoin 作為相對路徑處理
    # 這裡會正確處理 index.php, ./api, ../config 等
    return urljoin(base_url, raw_link)


def process_all_discovered_links(actual_final_url: str, raw_link_pool: list) -> dict:
    """
    將 pool 中所有的原始字符串轉化為標準 URL，並進行內外鏈初步分類
    """
    internal_urls = set()
    external_urls = set()

    parsed_base = urlparse(actual_final_url)
    base_hostname = parsed_base.hostname

    for raw in set(raw_link_pool):
        full_url = robust_link_resolver(actual_final_url, raw)
        if not full_url:
            continue

        # 移除 fragment 並統一結尾 (可選)
        full_url = full_url.split("#")[0]

        try:
            link_hostname = urlparse(full_url).hostname
            if link_hostname == base_hostname:
                internal_urls.add(full_url)
            else:
                external_urls.add(full_url)
        except:
            continue

    return {"internal": list(internal_urls), "external": list(external_urls)}
