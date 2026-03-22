import json
import logging
import os
import random
from typing import List, Dict, Any, Tuple
from urllib.parse import urljoin

import requests
from django.conf import settings
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from c2_core.config.config import Config
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 配置與常量 (Configuration & Constants)
# =============================================================================

HASURA_GRAPHQL_URL = f"{Config.HASURA_URL}/v1/graphql" if Config.HASURA_URL else None
HASURA_ADMIN_SECRET = Config.HASURA_ADMIN_SECRET
FALLBACK_AI_PROXY_URL = Config.NYAPROXY_SPIDER_URL

# Prompt 文件路徑
PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "ips_prompts.txt"
)
SUBDOMAIN_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "subdomains_prompts.txt"
)
URL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "urls_prompts.txt"
)
INITIAL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "initial_prompts.txt"
)

# =============================================================================
# 2. GraphQL 查詢語句 (GraphQL Queries)
# =============================================================================

GET_IPS_DETAILS_QUERY = gql(
    """
query GetIPsScanDetails($ip_ids: [bigint!]) {
  core_ip(where: {id: {_in: $ip_ids}}) {
    id
    address
    version
    core_ports(where: {state: {_eq: "open"}}) {
      port_number
      protocol
      service_name
      service_version
    }
    core_subdomain_ips {
      core_subdomain {
        name
      }
    }
  }
}

"""
)

GET_SUBDOMAINS_DETAILS_QUERY = gql(
    """
query GetSubdomainsDetails($ids: [bigint!]) {
  core_subdomain(where: {id: {_in: $ids}}) {
    cdn_name
    created_at
    first_seen
    is_cdn
    is_active
    is_resolvable
    is_waf
    sources_text
    name
    waf_name
    id
    core_dnsrecords {
        record_type
        value
    }
    core_techstacks {
      name
      version
      categories
    }
    core_vulnerabilities {
      fingerprint
      name
      severity
      status
      subdomain_asset_id
      template_id
      tool_source
      matched_at
      description
    }
  }
}

"""
)

GET_URLS_DETAILS_QUERY = gql(
    """
query GetUrlDetailsForAI($ids: [bigint!]) {
  core_urlresult(where: {id: {_in: $ids}}) {
    id
    url
    method
    status_code
    title
    content_length
    content_fetch_status
    text
    core_techstacks {
      name
      version
      categories
    }
    core_forms {
      action
      method
      parameters
    }
    core_comments {
      content
    }
    core_vulnerabilities {
      template_id
      name
      severity
      matched_at
    }
    core_analysisfindings {
      pattern_name
      match_content
    }
    core_endpoint_discovered_by_urls {
      core_endpoint {
        id
        path
        method
        core_urlparameters {
          key
          value
          param_location
          data_type
        }
      }
    }
    core_extractedj {
      id
      content
      core_jsonobjects(where: {score: {_gt: 0.8}}) {
        key
        path
        score
        struct
        val
        core_javascriptfile {
          id
          src
          core_jsonobjects(where: {score: {_gt: 0.9}}) {
            depth
            key
            path
            score
          }
        }
      }
    }
    core_iframes {
      src
    }
    core_links {
      href
      text
    }
    core_metatags {
      attributes
    }
    core_urlscans {
      tool
    }
    used_flaresolverr
    cleaned_html
    content_length
    status_code
    headers
    is_tech_analyzed
    final_url
    discovery_source
  }
}

"""
)


# =============================================================================
# 3. 基礎輔助函數 (Infrastructure Helpers)
# =============================================================================


@log_function_call()
def get_graphql_client() -> Client:
    headers = (
        {"x-hasura-admin-secret": HASURA_ADMIN_SECRET} if HASURA_ADMIN_SECRET else {}
    )
    transport = RequestsHTTPTransport(
        url=HASURA_GRAPHQL_URL, headers=headers, use_json=True
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


@log_function_call()
def load_prompt_template() -> str:
    try:
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"操！找不到 Prompt 模板文件: {PROMPT_TEMPLATE_PATH}")
        raise


@log_function_call()
def load_subdomain_prompt_template() -> str:
    try:
        with open(SUBDOMAIN_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(
            f"操！找不到 Subdomain Prompt 模板文件: {SUBDOMAIN_PROMPT_TEMPLATE_PATH}"
        )
        raise


@log_function_call()
def load_url_prompt_template() -> str:
    try:
        with open(URL_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"操！找不到 URL Prompt 模板文件: {URL_PROMPT_TEMPLATE_PATH}")
        raise


@log_function_call()
def load_initial_prompt_template() -> str:
    try:
        with open(INITIAL_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"操！找不到 Initial Prompt 模板文件: {INITIAL_PROMPT_TEMPLATE_PATH}")
        raise


# =============================================================================
# 4. 數據提取與清洗 (Data Fetching & Cleaning)
# =============================================================================


def fetch_ip_data_for_batch(ip_ids: List[int]) -> Dict[str, Any]:
    logger.info(f"正在通過 GraphQL 為 {len(ip_ids)} 個 IP 提取情報...")
    client = get_graphql_client()
    variables = {"ip_ids": ip_ids}
    try:
        result = client.execute(GET_IPS_DETAILS_QUERY, variable_values=variables)
        ip_data_from_gql = result.get("core_ip", [])
        asset_list = [
            {
                "correlation_id": ip_gql["id"],
                "asset_data": {
                    "ip_address": ip_gql["address"],
                    "ip_version": ip_gql["version"],
                    "ports": ip_gql.get("core_ports", []),
                    "associated_subdomains": [
                        # GraphQL 查詢返回 core_subdomain_ips { core_subdomain { name } }
                        # 注意：不是 core_subdomains，是中間表 core_subdomain_ips
                        rel.get("core_subdomain", {}).get("name")
                        for rel in ip_gql.get("core_subdomain_ips", [])
                        if rel.get("core_subdomain")
                    ],
                    "target_context": {
                        "root_domain": ip_gql.get("targets_target", {}).get("domain")
                    },
                },
            }
            for ip_gql in ip_data_from_gql
        ]
        return {"list_of_assets": asset_list}
    except Exception as e:
        logger.exception(f"執行 GraphQL 查詢失敗: {e}")
        return {"list_of_assets": []}


def fetch_subdomain_data_for_batch(subdomain_ids: List[int]) -> Dict[str, Any]:
    logger.info(f"正在通過 GraphQL 為 {len(subdomain_ids)} 個子域名提取情報...")
    client = get_graphql_client()
    variables = {"ids": subdomain_ids}
    try:
        result = client.execute(GET_SUBDOMAINS_DETAILS_QUERY, variable_values=variables)
        sub_data_from_gql = result.get("core_subdomain", [])

        asset_list = []
        for sub in sub_data_from_gql:
            # 提取技術棧 summary
            techs = [
                f"{t['name']} {t['version'] or ''}".strip()
                for t in sub.get("core_techstacks", [])
            ]
            # 提取已發現漏洞摘要
            vulns = [
                f"{v['name']} ({v['severity']})"
                for v in sub.get("core_vulnerabilities", [])
            ]

            asset_entry = {
                "correlation_id": sub["id"],
                "asset_data": {
                    "name": sub["name"],
                    "cdn_waf": {"cdn": sub.get("cdn_name"), "waf": sub.get("waf_name")},
                    "is_resolvable": sub.get("is_resolvable"),
                    "dns_records": sub.get("core_dnsrecords", []),
                    "tech_stack": techs,
                    "existing_vulnerabilities": vulns,
                    "source": sub.get("sources_text"),
                },
            }
            asset_list.append(asset_entry)

        return {"list_of_assets": asset_list}
    except Exception as e:
        logger.exception(f"執行 GraphQL (Subdomains) 查詢失敗: {e}")
        return {"list_of_assets": []}


def clean_url_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    針對 URL 數據進行深度截斷與去噪。
    """
    cleaned_list = []

    # 安全相關的 Header 白名單
    header_whitelist = [
        "server",
        "x-powered-by",
        "via",
        "x-cache",
        "content-security-policy",
        "strict-transport-security",
    ]

    for item in raw_data:
        # 1. 截斷正文 (只取前 1500 字，通常包含核心邏輯與標題)
        body_text = (item.get("text") or item.get("cleaned_html") or "")[:1500]

        # 2. 清理 Headers
        raw_headers = item.get("headers") or {}
        cleaned_headers = {
            k: v for k, v in raw_headers.items() if k.lower() in header_whitelist
        }

        # 3. 技術棧與漏洞整合
        techs = [
            f"{t['name']} {t['version'] or ''}".strip()
            for t in item.get("core_techstacks", [])
        ]
        vulns = [
            f"{v['name']} ({v['severity']})"
            for v in item.get("core_vulnerabilities", [])
        ]

        # 4. JS 文件截斷 (只保留路徑，不保留內容以免爆掉 Token)
        js_files = [
            js.get("src") for js in item.get("core_extractedjs", []) if js.get("src")
        ]

        # 5. 提取 Endpoint 摘要
        endpoints = []
        for ep_rel in item.get("core_endpoint_discovered_by_urls", []):
            ep = ep_rel.get("core_endpoint", {})
            endpoints.append(f"{ep.get('method')} {ep.get('path')}")

        cleaned_entry = {
            "correlation_id": item["id"],
            "asset_data": {
                "url": item["url"],
                "final_url": item.get("final_url"),
                "title": item["title"],
                "status": item["status_code"],
                "tech_stack": techs,
                "known_vulnerabilities": vulns,
                "headers": cleaned_headers,
                "endpoints_found": endpoints[:10],  # 限制 10 個
                "js_files": js_files[:10],
                "forms": item.get("core_forms", [])[:5],
                "analysis_findings": item.get("core_analysisfindings", [])[:10],
                "content_preview": body_text,
                "anti_bot": item.get("used_flaresolverr"),
            },
        }
        cleaned_list.append(cleaned_entry)

    return cleaned_list


def fetch_url_data_for_batch(url_ids: List[int]) -> Dict[str, Any]:
    logger.info(f"正在通過 GraphQL 為 {len(url_ids)} 個 URL 提取情報...")
    client = get_graphql_client()
    variables = {"ids": url_ids}
    try:
        result = client.execute(GET_URLS_DETAILS_QUERY, variable_values=variables)
        raw_data = result.get("core_urlresult", [])
        cleaned_data = clean_url_data(raw_data)
        return {"list_of_assets": cleaned_data}
    except Exception as e:
        logger.exception(f"執行 GraphQL (URLs) 查詢失敗: {e}")
        return {"list_of_assets": []}


def fetch_initial_data_for_batch(analysis_ids: List[int]) -> Dict[str, Any]:
    """
    為 InitialAIAnalysis 批次提取情報。
    因為 InitialAIAnalysis 記錄本身就關聯了 IP/Subdomain/URL，
    我們先獲取這些記錄，再按型別調用對應的 GraphQL fetcher。
    """
    from apps.core.models import InitialAIAnalysis
    records = InitialAIAnalysis.objects.filter(id__in=analysis_ids).select_related('ip', 'subdomain', 'url_result')
    
    ip_ids = [r.ip_id for r in records if r.ip_id]
    sub_ids = [r.subdomain_id for r in records if r.subdomain_id]
    url_ids = [r.url_result_id for r in records if r.url_result_id]
    
    all_assets = []
    
    # 建立 correlation_id -> analysis_id 的對應
    # 因為 GraphQL fetcher 返回的是 asset_id，我們需要對接回 InitialAIAnalysis.id
    record_map = {} # (type, asset_id) -> analysis_id
    for r in records:
        if r.ip_id: record_map[('ip', r.ip_id)] = r.id
        if r.subdomain_id: record_map[('subdomain', r.subdomain_id)] = r.id
        if r.url_result_id: record_map[('url', r.url_result_id)] = r.id

    if ip_ids:
        raw_ips = fetch_ip_data_for_batch(ip_ids).get('list_of_assets', [])
        for asset in raw_ips:
            asset['correlation_id'] = record_map.get(('ip', asset['correlation_id']))
            all_assets.append(asset)
            
    if sub_ids:
        raw_subs = fetch_subdomain_data_for_batch(sub_ids).get('list_of_assets', [])
        for asset in raw_subs:
            asset['correlation_id'] = record_map.get(('subdomain', asset['correlation_id']))
            all_assets.append(asset)
            
    if url_ids:
        raw_urls = fetch_url_data_for_batch(url_ids).get('list_of_assets', [])
        for asset in raw_urls:
            asset['correlation_id'] = record_map.get(('url', asset['correlation_id']))
            all_assets.append(asset)
            
    return {"list_of_assets": [a for a in all_assets if a['correlation_id']]}


# =============================================================================
# 5. 戰略上下文提取 (Strategic Context Builder)
# =============================================================================

def _build_strategic_context(record) -> Dict[str, Any]:
    """
    獲取分析記錄關聯的 Overview 戰略背景，包含知識、技術棧與最近執行的 Step 歷史。
    安全處理：若 record 沒有 overview 欄位（如 InitialAIAnalysis），返回空 dict。
    """
    if not hasattr(record, 'overview') or not record.overview:
        return {}

    context = {
        "overview_summary": record.overview.summary,
        "overview_knowledge": record.overview.knowledge,
        "overview_techs": record.overview.techs,
        "overview_plan": record.overview.plan,
        "recent_steps_execution": []
    }

    # 獲取最近3個已完成的 Step，以提供給 AI 執行結果的歷史上下文
    from apps.core.models import Step
    recent_steps = Step.objects.filter(overview=record.overview, status__in=["COMPLETED", "FAILED"]).order_by('-id')[:3]
    
    # 反轉以按時間順序排列 (舊 -> 新)
    for st in reversed(list(recent_steps)):
        step_data = {
            "step_id": st.id,
            "command_template": st.command_template,
            "note": st.note,
        }
        verifications = []
        for v in st.verifications.all():
            out = v.execution_output or ""
            verifications.append({
                "verdict": v.verdict,
                "strategy": v.verify_strategy,
                "output_preview": out[:1000]  # 截斷保留前1000字元避免Token爆炸
            })
        step_data["verifications"] = verifications
        context["recent_steps_execution"].append(step_data)

    # 標記觸發此 AI 分析的 Step（如果有的話）
    if record.triggered_by_step:
        context["triggered_by_step_id"] = record.triggered_by_step.id

    return context

# =============================================================================
# 6. AI 火力輸出核心 (AI Fire Control Core)
# =============================================================================


@log_function_call()
def _build_payload(target_api_name: str, final_prompt: str) -> dict:
    """
    【彈藥工廠】根據目標 API 名稱構建正確的 payload。
    """
    if "gemini" in target_api_name.lower():
        logger.info(
            f"檢測到 Gemini 目標 '{target_api_name}'，正在構建 Gemini 專用彈藥..."
        )
        return {
            "contents": [{"parts": [{"text": final_prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }

    logger.info(f"使用默認彈藥 (Mistral/OpenAI 格式) 攻擊目標 '{target_api_name}'...")
    return {
        "messages": [{"role": "user", "content": final_prompt}],
        "model": "mistral-large-latest",
        "response_format": {"type": "json_object"},
    }


@log_function_call()
def _fire_at_target(
    api_name: str, api_url: str, final_prompt: str
) -> Tuple[Dict[str, Any] | None, Exception | None]:
    """
    【砲手】使用正確的彈藥對單個目標開火。
    返回 (響應JSON, 異常) 元組。
    """
    try:
        # 1. 製造彈藥
        payload = _build_payload(api_name, final_prompt)
        logger.info(
            f"準備向 {api_url} 開火，Payload 結構:\n{json.dumps(payload, indent=2)}"
        )

        target_url = api_url
        logger.info(f"目標 URL: {target_url}")

        if "mistral_ai" in api_name:
            target_url = urljoin(api_url, "mistral_ai/chat/completions")
            logger.info(f"mistral_ai URL: {target_url}")

        # 2. 開火
        response = requests.post(
            target_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        response.raise_for_status()

        # 3. 處理戰果
        raw_json = response.json()
        if "gemini" in api_name.lower():
            try:
                content_text = raw_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(content_text), None
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                err_msg = f"解析 Gemini 響應時結構出錯: {e}. 原始響應: {raw_json}"
                logger.error(err_msg)
                return None, ValueError(err_msg)
        else:
            try:
                content_text = raw_json["choices"][0]["message"]["content"]
                return json.loads(content_text), None
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                err_msg = (
                    f"解析 Mistral/OpenAI 格式響應時結構出錯: {e}. 原始響應: {raw_json}"
                )
                logger.error(err_msg)
                return None, ValueError(err_msg)

    except requests.RequestException as e:
        logger.warning(f"火力點 {api_url} 連接失敗: {e}。")
        return None, e
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"解析 AI 響應失敗: {e}. 原始文本: {response.text}")
        return None, e


# =============================================================================
# 6. 通用 AI 批次執行器（Factory Core / Template Method）
# =============================================================================


def _execute_ai_batch(asset_type: str, asset_ids: List[int], task_self) -> None:
    """
    【通用 AI 批次分析執行器】

    這是整個 analyze_ai 的核心工廠函式。
    使用 ASSET_REGISTRY 查找特定資產型別的設定，
    然後執行以下統一流程：

    1. 將相關 analysis 記錄狀態更新為 RUNNING
    2. 通過 GraphQL 提取資產情報
    3. 載入對應的 Prompt 模板並注入資料
    4. 輪詢可用的 AI 服務火力點
    5. 解析 AI 回應並 bulk_update 回資料庫

    Args:
        asset_type:  資產型別字串，必須是 ASSET_REGISTRY 的有效 key
                     ('ip' | 'subdomain' | 'url')
        asset_ids:   要分析的資產 ID 列表
        task_self:   Celery task 的 self，用於 retry 機制

    Raises:
        KeyError: 若 asset_type 不在 ASSET_REGISTRY 中
    """
    from django.utils import timezone
    from django.db import transaction
    from .asset_configs import get_asset_registry

    registry = get_asset_registry()
    if asset_type not in registry:
        raise KeyError(
            f"未知的資產型別 '{asset_type}'，"
            f"可用型別: {list(registry.keys())}"
        )

    config = registry[asset_type]
    Model = config.analysis_model

    logger.info(
        f"Task {task_self.request.id}: 開始處理 [{asset_type}] 批次，"
        f"數量: {len(asset_ids)}。"
    )

    # ── 1. 標記為 RUNNING ──────────────────────────────────────────────────
    with transaction.atomic():
        analysis_qs = Model.objects.filter(
            **{f"{config.asset_id_field}__in": asset_ids}, status="PENDING"
        )
        # 獲取這些記錄的 ID，以便後續重新查詢（避免 QuerySet 中的 status='PENDING' 導致 update 後查不到）
        analysis_ids = list(analysis_qs.values_list("id", flat=True))
        
        if not analysis_ids:
            logger.warning(f"[{asset_type}] 沒有找到 PENDING 分析記錄，任務結束。")
            return

        analysis_qs.update(status="RUNNING")
        # 重新獲取 RUNNING 狀態的對象列表
        analysis_records = list(Model.objects.filter(id__in=analysis_ids))

    analysis_ids = [r.id for r in analysis_records]

    try:
        # ── 2. 動態火力選擇 ───────────────────────────────────────────────
        available_targets = list(Config.AI_SERVICE_URLS.items())
        if not available_targets:
            logger.error("沒有配置任何動態 AI 服務 URL，任務無法執行。")
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message="No AI services configured."
            )
            return

        random.shuffle(available_targets)
        logger.info(
            f"[{asset_type}] 火力陣地就緒，可用目標: "
            f"{[name for name, _ in available_targets]}"
        )

        # ── 3. 提取情報 ──────────────────────────────────────────────────
        data_payload = config.data_fetcher(asset_ids)
        if not data_payload.get("list_of_assets"):
            logger.warning(f"[{asset_type}] 未能提取到任何情報，任務終止。")
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message="Failed to fetch asset data."
            )
            return

        # ── 3.5 注入戰略上下文 (Continuous Strategy Context) ────────────────
        for asset in data_payload["list_of_assets"]:
            correlation_id = asset["correlation_id"]
            # 找到對應的 AIAnalysis 記錄
            record = next((r for r in analysis_records if config.get_asset_id(r) == correlation_id), None)
            if record:
                asset["strategic_context"] = _build_strategic_context(record)

        # ── 4. 準備彈藥（注入 Prompt 模板）──────────────────────────────
        template = config.prompt_loader()
        final_prompt = template.replace(
            "{$data}", json.dumps(data_payload, indent=2)
        )

        # ── 5. 輪番開火 ──────────────────────────────────────────────────
        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"[{asset_type}] 嘗試火力點: {api_name} ({api_url})")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"[{asset_type}] 火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception
                logger.warning(f"[{asset_type}] 火力點 {api_name} 未命中，切換中...")

        if ai_response is None:
            error_msg = (
                f"[{asset_type}] 所有 AI 服務節點均無響應。"
                f"最後錯誤: {last_exception}"
            )
            logger.error(error_msg)
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message=str(last_exception)
            )
            task_self.retry(exc=last_exception)
            return

        # ── 6. 戰果驗收與存檔 ────────────────────────────────────────────
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"[{asset_type}] 收到 {len(analysis_results)} 條 AI 分析結果。")

        if not analysis_results:
            logger.warning(f"[{asset_type}] 未收到任何 AI 分析結果，任務終止。")
            Model.objects.filter(id__in=analysis_ids).update(
                status="FAILED", error_message="No AI analysis results received."
            )
            logger.warning(f"原始 AI 回應: {ai_response}")
            return

        # 建立 { asset_id -> record } 的 map，方便快速查找
        analysis_map = config.build_analysis_map(analysis_records)
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)
            if not record:
                logger.warning(
                    f"[{asset_type}] AI 返回未知 correlation_id: "
                    f"{correlation_id}，已忽略。"
                )
                continue

            # 動態將 AI 回應欄位填回 record
            for result_field in config.result_fields:
                if result_field == "status":
                    record.status = "COMPLETED"
                elif result_field == "completed_at":
                    record.completed_at = timezone.now()
                else:
                    setattr(record, result_field, result.get(result_field))

            # 永遠儲存完整原始回應
            record.raw_response = result
            records_to_update.append(record)

        if records_to_update:
            Model.objects.bulk_update(records_to_update, config.result_fields)
            logger.info(
                f"[{asset_type}] 成功更新 {len(records_to_update)} 條分析記錄。"
            )

        # ── 7. 同步到 Overview (Overview Synchronization) ────────────────────
        for record in records_to_update:
            if record.overview:
                knowledge = record.overview.knowledge or {}
                # 記錄此次分析的主要發現
                entry_key = f"{asset_type}_{record.id}"
                knowledge[entry_key] = {
                    "summary": getattr(record, "summary", ""),
                    "inferred_purpose": getattr(record, "inferred_purpose", ""),
                    "timestamp": timezone.now().isoformat()
                }
                record.overview.knowledge = knowledge

                # 合併 techs：從 tech_stack_summary 或分析的 raw_response 中提取
                existing_techs = record.overview.techs or []
                new_techs = []
                if hasattr(record, "tech_stack_summary") and record.tech_stack_summary:
                    # Subdomain 有 tech_stack_summary
                    new_techs.append(record.tech_stack_summary)
                if record.raw_response and isinstance(record.raw_response, dict):
                    # 嘗試從 raw 回應中提取 tech_stack 欄位
                    raw_techs = record.raw_response.get("tech_stack") or record.raw_response.get("techs") or []
                    if isinstance(raw_techs, list):
                        new_techs.extend(raw_techs)
                # 合併去重 (保持順序)
                seen = set(existing_techs)
                for t in new_techs:
                    if t and t not in seen:
                        existing_techs.append(t)
                        seen.add(t)
                if new_techs:
                    record.overview.techs = existing_techs

                # 若分析出更高的 risk_score，則更新 Overview 的 risk_score
                if hasattr(record, "risk_score") and record.risk_score:
                    if record.overview.risk_score < record.risk_score:
                        record.overview.risk_score = record.risk_score
                
                record.overview.save(update_fields=["knowledge", "techs", "risk_score", "updated_at"])
                logger.debug(f"[{asset_type}] 已將分析結果同步至 Overview#{record.overview.id}")

        # ── 8. 後續鏈條觸發 (Post-Analysis Chain) ────────────────────────────────
        _handle_post_analysis_chain(asset_type, records_to_update)

    except Exception as e:
        error_msg = f"[{asset_type}] 批次處理發生未知錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        task_self.retry(exc=e)


def _handle_post_analysis_chain(asset_type: str, records: list):
    """
    處理分析完成後的邏輯跳轉：
    1. deep (ip/sub/url) -> 觸發 Planning (propose_next_steps)
    """
    if asset_type in ["ip", "subdomain", "url"]:
        # 深度分析完成，觸發 Planning
        processed_overviews = set()
        for r in records:
            if r.overview_id and r.overview_id not in processed_overviews:
                from .planning import propose_next_steps
                propose_next_steps.delay(r.overview_id)
                processed_overviews.add(r.overview_id)
                logger.info(f"[Analysis] 深度分析已完成，觸發 Overview#{r.overview_id} 的策略規劃。")

