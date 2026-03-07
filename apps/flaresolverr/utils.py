# apps/flaresolverr/utils.py

import logging
import hashlib
import torch
import requests
from urllib.parse import urlparse, parse_qsl

from fake_useragent import UserAgent
from c2_core.config.config import Config

# 導入 Django Models (根據你的代碼合併)
from apps.core.models import (
    URLResult,
    JavaScriptFile,
    Endpoint,
    URLParameter,
    Subdomain,
    Target,
    TechStack,
    ExtractedJS,
)

# 初始化設定
logger = logging.getLogger(__name__)
ua = UserAgent()


def get_random_headers():
    """生成隨機 Header 字典"""
    return {"User-Agent": ua.random}


def get_score_batch(node_list, AI_MODEL, AI_TOKENIZER, DEVICE):
    """
    一次算一整批，效率最高
    """
    if not node_list:
        return []

    texts = [
        f"Path: {n['path']} | Key: {n['key']} | Struct: {n['struct']} | Val: {n['val']} | Depth: {n['depth']}"
        for n in node_list
    ]

    inputs = AI_TOKENIZER(
        texts, return_tensors="pt", truncation=True, max_length=128, padding=True
    ).to(DEVICE)

    with torch.no_grad():
        outputs = AI_MODEL(**inputs)
        scores = outputs.logits.squeeze(-1).tolist()

    # 轉成 List 並限制範圍
    if not isinstance(scores, list):
        scores = [scores]
    return [round(max(0.0, min(1.0, s)), 4) for s in scores]


def save_tech_stack_to_db(url_result_obj, tech_stack_result: dict):
    """
    全量更新模式：
    1. 刪除該 URL 關聯的所有舊 TechStack。
    2. 寫入本次掃描發現的所有新 TechStack。
    """
    fingerprints = tech_stack_result.get("fingerprints_matched", [])

    # 1. 清理舊數據 (這一步確保資料庫裡不會有殘留的過時版本)
    TechStack.objects.filter(which_url_result=url_result_obj).delete()

    if not fingerprints:
        return

    to_create = []
    seen_in_batch = set()

    for item in fingerprints:
        name = item.get("name")
        if not name:
            continue

        version = item.get("version")
        clean_version = version if version and version.lower() != "n/a" else None

        # 本次批次內去重
        if (name, clean_version) in seen_in_batch:
            continue
        seen_in_batch.add((name, clean_version))

        categories = item.get("categories", [])
        if not isinstance(categories, list):
            categories = []

        to_create.append(
            TechStack(
                which_url_result=url_result_obj,
                name=name,
                version=clean_version,
                categories=categories,
            )
        )

    # 2. 寫入新數據
    if to_create:
        TechStack.objects.bulk_create(to_create)
        logger.info(
            f"已更新 {url_result_obj.url} 的技術棧: 寫入 {len(to_create)} 條記錄。"
        )


def walk(obj, path, depth, nodes_list):
    """
    遞迴遍歷 JSON/Dict 結構，將節點平鋪到 nodes_list
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f"{path}.{k}", depth + 1, nodes_list)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", depth + 1, nodes_list)
    else:
        nodes_list.append(
            {
                "path": path,
                "key": str(path.split(".")[-1]),
                "struct": "Leaf",
                "val": str(obj),
                "depth": depth,
            }
        )


def downloader(js_url) -> str | None:
    """
    下載器邏輯：
    1. 嘗試使用 requests 直接下載。
    2. 如果失敗，調用 FlareSolverr 進行繞過下載。
    """
    headers = get_random_headers()

    # --- 階段 1：直接抓取 ---
    logger.info(f"嘗試直接抓取: {js_url}")
    try:
        resp = requests.get(js_url, timeout=5, headers=headers, verify=False)
        if resp.status_code == 200:
            # logger.info("直接抓取成功！") # 視需要開啟
            return resp.text
        logger.warning(f"直接抓取失敗，Status Code: {resp.status_code}")
    except Exception as e:
        logger.info(f"Requests 發生異常，準備切換策略: {e}")

    # --- 階段 2：FlareSolverr ---
    logger.info(f"準備派出 FlareSolverr 戰鬥: {js_url}")
    payload = {"cmd": "request.get", "url": js_url, "maxTimeout": 60000}

    try:
        # 這裡使用真實的 Config
        r = requests.post(Config.FLARESOLVERR_URL, json=payload, timeout=70)

        if r.status_code != 200:
            logger.error(f"FlareSolverr 服務器響應錯誤代碼: {r.status_code}")
            return None

        solver_resp = r.json()
        if solver_resp.get("status") == "ok":
            content = solver_resp["solution"]["response"]
            logger.info(f"FlareSolverr 抓取成功，內容長度: {len(content)}")
            return content
        else:
            logger.error(f"FlareSolverr 回報錯誤: {solver_resp.get('message')}")
            return None

    except requests.exceptions.ConnectionError:
        logger.error(
            f"❌ 無法連線到 FlareSolverr (位址: {Config.FLARESOLVERR_URL})。請檢查 Docker 是否啟動。"
        )
        return None
    except Exception as e:
        logger.error(f"❌ FlareSolverr 調用發生未預期錯誤: {type(e).__name__} - {e}")
        return None


def save_params_to_db(endpoints_list: list, target_obj, source_obj) -> int:
    """
    將分析結果存入 Endpoint 與 URLParameter
    :param endpoints_list: 分析工具產生的列表
    :param target_obj: 專案 Target 物件
    :param source_obj: 發現來源 (URLResult 或 JavaScriptFile)
    """
    total_saved = 0

    for ep in endpoints_list:
        full_url = ep.get("url")
        method = ep.get("method", "GET").upper()

        if not full_url:
            continue

        # A. 提取 Path 進行歸一化
        parsed = urlparse(full_url)
        path = parsed.path if parsed.path else "/"

        # B. 建立/獲取 Endpoint (唯一標識: target + method + path)
        endpoint_obj, created = Endpoint.objects.get_or_create(
            target=target_obj, method=method, path=path
        )

        # C. 關聯發現來源 (M2M)
        if isinstance(source_obj, URLResult):
            endpoint_obj.discovered_by_urls.add(source_obj)
        elif isinstance(source_obj, JavaScriptFile):
            endpoint_obj.discovered_by_js.add(source_obj)

        # D. 處理參數
        params_to_save = []

        # 1. 來自分析器的參數 (JS/Form)
        all_found_params = ep.get("queryParams", []) + ep.get("bodyParams", [])
        for p in all_found_params:
            params_to_save.append(
                {
                    "key": p.get("name"),
                    "value": p.get("value", ""),
                    "location": "query" if p in ep.get("queryParams", []) else "body",
                    "source": p.get("source", "javascript"),
                    "data_type": p.get("data_type", "string") or p.get("input_type"),
                }
            )

        # 2. 來自 URL 原始 Query String 的參數
        if parsed.query:
            qs_params = parse_qsl(parsed.query)
            existing_keys = {
                p["key"] for p in params_to_save if p["location"] == "query"
            }
            for key, val in qs_params:
                if key not in existing_keys:
                    params_to_save.append(
                        {
                            "key": key,
                            "value": val,
                            "location": "query",
                            "source": "querystring",
                            "data_type": "string",
                        }
                    )

        # E. 寫入 URLParameter 表
        for item in params_to_save:
            key = item["key"]
            if not key:
                continue

            # 使用 update_or_create 避免重複，並保持範例值最新
            URLParameter.objects.update_or_create(
                which_endpoint=endpoint_obj,
                key=key,
                param_location=item["location"],
                defaults={
                    "value": item["value"],
                    "source_type": (
                        item["source"]
                        if item["source"] in ["form", "javascript", "querystring"]
                        else "javascript"
                    ),
                    "data_type": item["data_type"],
                },
            )
            total_saved += 1

    return total_saved


def get_target_from_js_file(js_obj):
    """
    既然 JavaScriptFile 沒有 target 欄位，我們必須透過關聯頁面來查
    """
    # 1. 透過關聯的頁面 (URLResult) 溯源
    # 使用 select_related 避免 N+1
    first_page = js_obj.related_pages.select_related("target").first()
    if first_page and first_page.target:
        return first_page.target

    # 2. 如果頁面也沒標記 Target (像你剛才遇到的問題)，嘗試域名反查
    if js_obj.src:
        from urllib.parse import urlparse
        from apps.core.models import Subdomain

        try:
            domain_name = urlparse(js_obj.src).netloc.split(":")[0]
            sub = Subdomain.objects.filter(name__icontains=domain_name).first()
            if sub and sub.target:
                return sub.target
        except Exception:
            pass

    return None


def sync_previous_results(new_obj, old_obj):
    """
    當內容重複時，將舊物件發現的 Endpoint 關聯到新物件所屬的 Target。
    """
    # 找到所有舊物件關聯的 Endpoint
    old_endpoints = old_obj.found_endpoints.all()

    target = getattr(new_obj, "target", None)
    if not target and hasattr(new_obj, "which_url"):
        target = new_obj.which_url.target

    if not target:
        return  # 沒 Target 就不需要關聯 Endpoint 了，標記 analyzed 就好

    for ep in old_endpoints:
        # 在新 Target 下建立或獲取相同的 Endpoint
        new_ep, _ = Endpoint.objects.get_or_create(
            target=target, method=ep.method, path=ep.path
        )

        # 將新物件(JSFile/URLResult)加到發現來源中
        if isinstance(new_obj, JavaScriptFile):
            new_ep.discovered_by_js.add(new_obj)
        # 注意: ExtractedJS 需要確認是否已導入
        elif type(new_obj).__name__ == "ExtractedJS":
            new_ep.discovered_by_urls.add(new_obj.which_url)
