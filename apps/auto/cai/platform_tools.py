"""
apps/auto/cai/platform_tools.py

Professional AI Tools for Platform Integration.
Includes GraphQL queries for asset data and REST API wrappers for scanner triggers.
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional

from django.conf import settings
from apps.analyze_ai.tasks.common import (
    get_graphql_client,
    GET_SUBDOMAINS_DETAILS_QUERY,
    GET_IPS_DETAILS_QUERY,
    fetch_subdomain_data_for_batch,
    fetch_ip_data_for_batch
)
from cai.sdk.agents import function_tool

logger = logging.getLogger(__name__)

# Base URL for REST API calls (local Django server)
API_BASE_URL = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")

# =============================================================================
# 1. Asset Discovery Tools (GraphQL)
# =============================================================================

@function_tool
def get_subdomains_info(subdomain_ids: List[int]) -> str:
    """
    Fetch detailed information about specific subdomains using GraphQL.
    Includes tech stack, CDN/WAF info, and DNS records.
    
    Args:
        subdomain_ids: List of subdomain database IDs.
        
    Returns:
        JSON string containing subdomain details.
    """
    try:
        data = fetch_subdomain_data_for_batch(subdomain_ids)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error fetching subdomain info: {e}")
        return f"Error: {str(e)}"

@function_tool
def get_ips_info(ip_ids: List[int]) -> str:
    """
    Fetch detailed information about specific IPs using GraphQL.
    Includes open ports, services, and associated subdomains.
    
    Args:
        ip_ids: List of IP database IDs.
        
    Returns:
        JSON string containing IP details.
    """
    try:
        data = fetch_ip_data_for_batch(ip_ids)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error fetching IP info: {e}")
        return f"Error: {str(e)}"

# =============================================================================
# 2. Scanner Trigger Tools (REST API)
# =============================================================================

@function_tool
def trigger_subfinder(seed_id: int) -> str:
    """
    Trigger a Subfinder reconnaissance scan for a specific seed ID.
    
    Args:
        seed_id: The ID of the DOMAIN seed to scan.
        
    Returns:
        Response from the API.
    """
    url = f"{API_BASE_URL}/subfinder/start_subfinder"
    payload = {"seed_id": seed_id}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        logger.error(f"Error triggering Subfinder: {e}")
        return f"Error triggering Subfinder: {str(e)}"

@function_tool
def trigger_nuclei_scan(asset_type: str, asset_ids: List[int], tags: Optional[List[str]] = None) -> str:
    """
    Trigger a Nuclei vulnerability or tech scan.
    
    Args:
        asset_type: Type of asset ('subdomains', 'ips', 'urls', 'subs_tech', 'urls_tech').
        asset_ids: List of database IDs to scan.
        tags: Optional Nuclei tags to use (e.g., ['cves', 'exposure']).
        
    Returns:
        Response from the API.
    """
    endpoint_map = {
        "subdomains": "/nuclei_scanner/subdomains",
        "ips": "/nuclei_scanner/ips",
        "urls": "/nuclei_scanner/urls",
        "subs_tech": "/nuclei_scanner/subs_tech",
        "urls_tech": "/nuclei_scanner/urls_tech"
    }
    
    if asset_type not in endpoint_map:
        return f"Error: Invalid asset_type '{asset_type}'. Valid types: {list(endpoint_map.keys())}"
    
    url = f"{API_BASE_URL}{endpoint_map[asset_type]}"
    payload = {"ids": asset_ids}
    if tags:
        payload["tags"] = tags
        
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        logger.error(f"Error triggering Nuclei scan: {e}")
        return f"Error triggering Nuclei scan: {str(e)}"
