import json
import logging
import os
import random
from typing import List, Dict, Any, Tuple
from urllib.parse import urljoin

import requests
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from c2_core.config.config import Config
from c2_core.config.logging import log_function_call
from core.models import IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 配置與常量 (Configuration & Constants)
# =============================================================================

HASURA_GRAPHQL_URL = f"{Config.HASURA_URL}/v1/graphql" if Config.HASURA_URL else None
HASURA_ADMIN_SECRET = Config.HASURA_ADMIN_SECRET
FALLBACK_AI_PROXY_URL = Config.NYAPROXY_SPIDER_URL

# Prompt 文件路徑
PROMPT_TEMPLATE_PATH = settings.BASE_DIR / "analyze_ai" / "prompts" / "ips_prompts.txt"
SUBDOMAIN_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "analyze_ai" / "prompts" / "subdomains_prompts.txt"
)
URL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "analyze_ai" / "prompts" / "urls_prompts.txt"
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
    id
    name
    cname
    cdn_name
    waf_name
    core_urlscans(limit: 1, order_by: {created_at: desc}) {
      created_at
      status
      core_urlresult_discovered_by_scans {
        core_urlresult {
          content_fetch_status
          headers
          final_url
          core_techstacks {
            categories
            name
            version
          }
          used_flaresolverr
        }
      }
    }
    dns_records
      }
    }



"""
)

GET_URLS_DETAILS_QUERY = gql(
    """
query GetURLsDetails($ids: [bigint!]) {
  core_urlresult(where: {id: {_in: $ids}}) {
    id
    url
    title
    status_code
    content_length
    used_flaresolverr
    core_analysisfindings {
      pattern_name
      match_content
      line_number
    }
    core_forms {
      action
      method
      parameters
    }
    headers
    core_endpoints(limit: 30) {
      path
      source
    }
    core_javascriptfiles(limit: 40) {
      src
    }
    core_comments(limit: 20) {
      content
    }
    core_metatags(limit: 20) {
      attributes
    }
    core_techstacks {
      name
      version
      categories
    }
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
        # 使用你新的 GraphQL 查询语句
        result = client.execute(GET_SUBDOMAINS_DETAILS_QUERY, variable_values=variables)
        sub_data_from_gql = result.get("core_subdomain", [])

        asset_list = []
        for sub in sub_data_from_gql:
            # === 1. 提取 IP 和端口信息 ===
            ip_address = None
            open_ports = []
            ips_relation = sub.get("core_subdomain_ips", [])
            if ips_relation:
                # 通常只有一个 IP，我们取第一个
                ip_data = ips_relation[0].get("core_ip")
                if ip_data:
                    ip_address = ip_data.get("ipv4") or ip_data.get("ipv6")
                    # 提取开放端口
                    open_ports = ip_data.get("core_ports", [])

            # === 2. 提取 HTTP 扫描结果 ===
            http_info = None
            url_scans = sub.get("core_urlscans", [])
            if url_scans:
                # 通常只有一个 URLScan 记录
                scan_data = url_scans[0]
                # URLScan 下可能有一个或多个 URLResult
                url_results_relation = scan_data.get(
                    "core_urlresult_discovered_by_scans", []
                )
                if url_results_relation:
                    # 取第一个 URLResult 作为代表
                    url_result = url_results_relation[0].get("core_urlresult")
                    if url_result:
                        http_info = {
                            "status": scan_data.get("status"),
                            "scan_date": scan_data.get("created_at"),
                            "fetch_status": url_result.get("content_fetch_status"),
                            "final_url": url_result.get("final_url"),
                            "tech_stack": url_result.get("tech_stack"),
                        }

            # === 3. 组装最终的数据结构 ===
            asset_entry = {
                "correlation_id": sub["id"],
                "asset_data": {
                    "name": sub["name"],
                    "cname": sub.get("cname"),
                    "cdn_name": sub.get("cdn_name"),
                    "waf_name": sub.get("waf_name"),
                    "ip_address": ip_address,
                    "open_ports": open_ports,  # 新增
                    "http_info": http_info,  # 新增
                    "dns_records_summary": sub.get("dns_records", {}).get(
                        "a", []
                    ),  # 只取 A 记录作为摘要
                },
            }
            asset_list.append(asset_entry)

        return {"list_of_assets": asset_list}
    except Exception as e:
        logger.exception(f"執行 GraphQL (Subdomains) 查詢失敗: {e}")
        return {"list_of_assets": []}


def clean_url_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    對 URL 原始數據進行強力清洗，去除噪音，節省 Token。
    """
    cleaned_list = []

    # 定義過濾黑名單/白名單關鍵字
    js_ignore_keywords = [
        "jquery",
        "bootstrap",
        "google",
        "facebook",
        "twitter",
        "gtm",
        "analytics",
        "wp-includes",
        "node_modules",
        "cdn.",
        "assets.squarespace",
    ]
    meta_keep_keywords = ["generator", "csrf", "api", "token", "version"]
    comment_ignore_keywords = [
        "squarespace",
        "wordpress",
        "end of",
        "start of",
        "wrapper",
        "nav",
        "footer",
    ]

    for item in raw_data:
        # 1. JS 過濾
        cleaned_js = []
        for js in item.get("core_javascriptfiles", []):
            src = js.get("src")
            if not src:
                continue
            src_lower = src.lower()
            if any(k in src_lower for k in js_ignore_keywords):
                continue
            cleaned_js.append(js)

        # 2. Meta 過濾
        cleaned_meta = []
        for meta in item.get("core_metatags", []):
            attrs = meta.get("attributes", {})
            attrs_str = str(attrs).lower()
            if any(k in attrs_str for k in meta_keep_keywords):
                cleaned_meta.append(meta)

        # 3. Comment 過濾
        cleaned_comments = []
        for comm in item.get("core_comments", []):
            content = comm.get("content", "").strip()
            if len(content) < 10:
                continue
            if any(k in content.lower() for k in comment_ignore_keywords):
                continue
            cleaned_comments.append({"content": content[:200]})

        # 構建清洗後的對象
        cleaned_entry = {
            "correlation_id": item["id"],
            "asset_data": {
                "url": item["url"],
                "title": item["title"],
                "status_code": item["status_code"],
                "tech_stack": item.get("tech_stack"),
                "headers": item.get("headers"),
                "used_flaresolverr": item.get("used_flaresolverr"),
                "core_analysisfindings": item.get("core_analysisfindings", []),
                "core_forms": item.get("core_forms", []),
                "core_endpoints": item.get("core_endpoints", []),
                "core_javascriptfiles": cleaned_js,
                "core_metatags": cleaned_meta,
                "core_comments": cleaned_comments,
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


# =============================================================================
# 6. Celery Tasks: IP Analysis
# =============================================================================


@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_ips(self, ip_ids: List[int]):
    """【總司令部】"""
    logger.info(f"Task {self.request.id}: 收到 {len(ip_ids)} 個 IP 的 AI 分析請求。")
    with transaction.atomic():
        IPAIAnalysis.objects.bulk_create(
            [IPAIAnalysis(ip_id=ip_id) for ip_id in ip_ids], ignore_conflicts=True
        )
    perform_ai_analysis_for_ip_batch.delay(ip_ids)
    return f"已成功為 {len(ip_ids)} 個 IP 派發單個分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_ip_batch(self, ip_ids: List[int]):
    """
    【作戰單元】使用重構後的火力系統處理批次。
    """
    logger.info(f"Task {self.request.id}: 開始處理批次，包含 {len(ip_ids)} 個 IP。")
    analysis_qs = IPAIAnalysis.objects.filter(ip_id__in=ip_ids)
    analysis_qs.update(status="RUNNING")

    try:
        # 1. 動態火力選擇
        available_targets = list(Config.AI_SERVICE_URLS.items())
        if not available_targets:
            logger.error("沒有配置任何動態 AI 服務 URL，任務無法執行。")
            analysis_qs.update(
                status="FAILED", error_message="No AI services configured."
            )
            return

        random.shuffle(available_targets)
        logger.info(
            f"火力陣地已準備就緒，可用目標: {[name for name, url in available_targets]}"
        )

        # 2. 提取情報 & 準備作戰指令
        data_payload = fetch_ip_data_for_batch(ip_ids)
        if not data_payload["list_of_assets"]:
            logger.warning("未能為此批次提取到任何情報，任務終止。")
            analysis_qs.update(
                status="FAILED", error_message="Failed to fetch asset data."
            )
            return

        template = load_prompt_template()
        final_prompt = template.replace("{$data}", json.dumps(data_payload, indent=2))

        # 3. 輪番開火
        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"正在嘗試使用火力點: {api_name} ({api_url})")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception
                logger.warning(f"火力點 {api_name} 未命中，正在切換到下一個...")

        if ai_response is None:
            error_msg = f"所有 AI 服務節點均無響應。最後錯誤: {last_exception}"
            logger.error(error_msg)
            analysis_qs.update(status="FAILED", error_message=str(last_exception))
            self.retry(exc=last_exception)
            return

        # 4. 戰果驗收與存檔
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"收到 {len(analysis_results)} 條 AI 分析結果。")

        if len(analysis_results) == 0:
            logger.warning("未能收到任何 AI 分析結果，任務終止。")
            analysis_qs.update(
                status="FAILED", error_message="No AI analysis results received."
            )
            logger.warning(f"{ai_response}")

        analysis_map = {record.ip_id: record for record in analysis_qs}
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)
            if record:
                record.summary = result.get("summary")
                record.inferred_purpose = result.get("inferred_purpose")
                record.risk_score = result.get("risk_score")
                record.port_analysis_summary = result.get("port_analysis_summary")
                record.potential_vulnerabilities = result.get(
                    "potential_vulnerabilities"
                )
                record.recommended_actions = result.get("recommended_actions")
                record.command_actions = result.get("command_actions")
                record.raw_response = result
                record.status = "COMPLETED"
                record.completed_at = timezone.now()
                records_to_update.append(record)
            else:
                logger.warning(
                    f"AI 返回了未知的 correlation_id: {correlation_id}，已忽略。"
                )

        if records_to_update:
            IPAIAnalysis.objects.bulk_update(
                records_to_update,
                [
                    "summary",
                    "inferred_purpose",
                    "risk_score",
                    "port_analysis_summary",
                    "potential_vulnerabilities",
                    "recommended_actions",
                    "command_actions",
                    "raw_response",
                    "status",
                    "completed_at",
                ],
            )
            logger.info(f"成功更新 {len(records_to_update)} 條分析記錄。")

    except Exception as e:
        error_msg = f"批次處理中發生未知錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        self.retry(exc=e)


# =============================================================================
# 7. Celery Tasks: Subdomain Analysis
# =============================================================================


@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_subdomains(self, subdomain_ids: List[int]):
    """【總司令部 - 子域名分部】"""
    logger.info(
        f"Task {self.request.id}: 收到 {len(subdomain_ids)} 個子域名的 AI 分析請求。"
    )

    with transaction.atomic():
        SubdomainAIAnalysis.objects.bulk_create(
            [SubdomainAIAnalysis(subdomain_id=sid) for sid in subdomain_ids],
            ignore_conflicts=True,
        )

    perform_ai_analysis_for_subdomain_batch.delay(subdomain_ids)
    return f"已成功為 {len(subdomain_ids)} 個子域名派發分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_subdomain_batch(self, subdomain_ids: List[int]):
    """
    【作戰單元 - 子域名分析】
    """
    logger.info(
        f"Task {self.request.id}: 開始處理子域名批次，數量: {len(subdomain_ids)}。"
    )

    analysis_qs = SubdomainAIAnalysis.objects.filter(subdomain_id__in=subdomain_ids)
    analysis_qs.update(status="RUNNING")

    try:
        # 1. 獲取數據
        data_payload = fetch_subdomain_data_for_batch(subdomain_ids)
        if not data_payload["list_of_assets"]:
            logger.warning("未能提取到任何子域名數據，任務終止。")
            analysis_qs.update(
                status="FAILED", error_message="Failed to fetch asset data via GraphQL."
            )
            return

        # 2. 準備彈藥
        template = load_subdomain_prompt_template()
        final_prompt = template.replace("{$data}", json.dumps(data_payload, indent=2))

        # 3. 火力覆蓋
        available_targets = list(Config.AI_SERVICE_URLS.items())
        random.shuffle(available_targets)

        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"正在嘗試使用火力點: {api_name} 分析子域名...")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception

        if ai_response is None:
            error_msg = f"所有 AI 節點均失敗。最後錯誤: {last_exception}"
            logger.error(error_msg)
            analysis_qs.update(status="FAILED", error_message=str(last_exception))
            self.retry(exc=last_exception)
            return

        # 4. 戰果存檔
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"收到 {len(analysis_results)} 條 AI 分析結果。")

        analysis_map = {record.subdomain_id: record for record in analysis_qs}
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)

            if record:
                record.summary = result.get("summary")
                record.inferred_purpose = result.get("inferred_purpose")
                record.business_impact = result.get("business_impact")
                record.tech_stack_summary = result.get("tech_stack_summary")
                record.risk_score = result.get("risk_score")
                record.potential_vulnerabilities = result.get(
                    "potential_vulnerabilities"
                )
                record.recommended_actions = result.get("recommended_actions")
                record.command_actions = result.get("command_actions")
                record.raw_response = result
                record.status = "COMPLETED"
                record.completed_at = timezone.now()
                records_to_update.append(record)
            else:
                logger.warning(
                    f"AI 返回了未知的 Subdomain ID: {correlation_id}，忽略。"
                )

        if records_to_update:
            SubdomainAIAnalysis.objects.bulk_update(
                records_to_update,
                [
                    "summary",
                    "inferred_purpose",
                    "business_impact",
                    "tech_stack_summary",
                    "risk_score",
                    "potential_vulnerabilities",
                    "recommended_actions",
                    "command_actions",
                    "raw_response",
                    "status",
                    "completed_at",
                ],
            )
            logger.info(f"成功更新 {len(records_to_update)} 條子域名分析記錄。")

    except Exception as e:
        error_msg = f"子域名批次處理中發生致命錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        self.retry(exc=e)


# =============================================================================
# 8. Celery Tasks: URL Analysis
# =============================================================================


@shared_task(bind=True)
@log_function_call()
def trigger_ai_analysis_for_urls(self, url_ids: List[int]):
    """【總司令部 - URL分部】"""
    logger.info(f"Task {self.request.id}: 收到 {len(url_ids)} 個 URL 的 AI 分析請求。")

    with transaction.atomic():
        URLAIAnalysis.objects.bulk_create(
            [URLAIAnalysis(url_result_id=uid) for uid in url_ids], ignore_conflicts=True
        )

    perform_ai_analysis_for_url_batch.delay(url_ids)
    return f"已成功為 {len(url_ids)} 個 URL 派發分析任務。"


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_ai_analysis_for_url_batch(self, url_ids: List[int]):
    """
    【作戰單元 - URL分析】
    """
    logger.info(f"Task {self.request.id}: 開始處理 URL 批次，數量: {len(url_ids)}。")

    analysis_qs = URLAIAnalysis.objects.filter(url_result_id__in=url_ids)
    analysis_qs.update(status="RUNNING")

    try:
        # 1. 獲取並清洗數據
        data_payload = fetch_url_data_for_batch(url_ids)
        if not data_payload["list_of_assets"]:
            logger.warning("未能提取到任何 URL 數據，任務終止。")
            analysis_qs.update(
                status="FAILED", error_message="Failed to fetch/clean asset data."
            )
            return

        # 2. 準備彈藥
        template = load_url_prompt_template()
        final_prompt = template.replace("{$data}", json.dumps(data_payload, indent=2))

        # 3. 火力覆蓋
        available_targets = list(Config.AI_SERVICE_URLS.items())
        random.shuffle(available_targets)

        ai_response = None
        last_exception = None

        for api_name, api_url in available_targets:
            logger.info(f"正在嘗試使用火力點: {api_name} 分析 URL...")
            response_json, exception = _fire_at_target(api_name, api_url, final_prompt)

            if response_json:
                ai_response = response_json
                logger.info(f"火力點 {api_name} 命中目標！")
                break
            else:
                last_exception = exception

        if ai_response is None:
            error_msg = f"所有 AI 節點均失敗。最後錯誤: {last_exception}"
            logger.error(error_msg)
            analysis_qs.update(status="FAILED", error_message=str(last_exception))
            self.retry(exc=last_exception)
            return

        # 4. 戰果存檔
        analysis_results = ai_response.get("analysis_results", [])
        logger.info(f"收到 {len(analysis_results)} 條 URL 分析結果。")

        analysis_map = {record.url_result_id: record for record in analysis_qs}
        records_to_update = []

        for result in analysis_results:
            correlation_id = result.get("correlation_id")
            record = analysis_map.get(correlation_id)

            if record:
                record.summary = result.get("summary")
                record.inferred_purpose = result.get("inferred_purpose")
                record.risk_score = result.get("risk_score")
                record.potential_vulnerabilities = result.get(
                    "potential_vulnerabilities"
                )
                record.recommended_actions = result.get("recommended_actions")
                record.command_actions = result.get("command_actions")
                record.extracted_entities = result.get("extracted_entities")
                record.raw_response = result
                record.score = result.get("score")
                record.status = "COMPLETED"
                record.completed_at = timezone.now()
                records_to_update.append(record)
            else:
                logger.warning(
                    f"AI 返回了未知的 URLResult ID: {correlation_id}，忽略。"
                )

        if records_to_update:
            URLAIAnalysis.objects.bulk_update(
                records_to_update,
                [
                    "summary",
                    "inferred_purpose",
                    "risk_score",
                    "potential_vulnerabilities",
                    "recommended_actions",
                    "command_actions",
                    "extracted_entities",
                    "raw_response",
                    "status",
                    "completed_at",
                ],
            )
            logger.info(f"成功更新 {len(records_to_update)} 條 URL 分析記錄。")

    except Exception as e:
        error_msg = f"URL 批次處理中發生致命錯誤: {e}"
        logger.exception(error_msg)
        analysis_qs.update(status="FAILED", error_message=str(e))
        self.retry(exc=e)
