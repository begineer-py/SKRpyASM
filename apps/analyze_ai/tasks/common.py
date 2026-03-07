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

# =============================================================================
# 2. GraphQL 查詢語句 (GraphQL Queries)
# =============================================================================

GET_IPS_DETAILS_QUERY = gql(
    """
query GetIPsScanDetails($ip_ids: [bigint!]) {
  core_ip(where: {id: {_in: $ip_ids}}) {
    id
    ipv4
    ipv6
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
    cname
    dns_records
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
                    "ip_address": ip_gql["ipv4"] or ip_gql["ipv6"],
                    "ports": ip_gql.get("core_ports", []),
                    "associated_subdomains": [
                        sub.get("name") for sub in ip_gql.get("core_subdomains", [])
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
                    "cname": sub.get("cname"),
                    "cdn_waf": {"cdn": sub.get("cdn_name"), "waf": sub.get("waf_name")},
                    "is_resolvable": sub.get("is_resolvable"),
                    "dns_records": (sub.get("dns_records") or {}).get("a", []),
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


# =============================================================================
# 5. AI 火力輸出核心 (AI Fire Control Core)
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
