"""
apps/auto/tools/graphql.py

為 AI 提供通用的 GraphQL 增刪改查 (CRUD) 工具。
封裝了與 Hasura 的交互。
"""

import logging
import json
from typing import Dict, Any, Optional
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from apps.auto.cai.core.tool import function_tool
from c2_core.config.config import Config

logger = logging.getLogger(__name__)

def _get_client() -> Client:
    """獲取 GraphQL 客戶端。"""
    url = f"{Config.HASURA_URL}/v1/graphql"
    headers = {"x-hasura-admin-secret": Config.HASURA_ADMIN_SECRET} if Config.HASURA_ADMIN_SECRET else {}
    transport = RequestsHTTPTransport(url=url, headers=headers, use_json=True)
    return Client(transport=transport, fetch_schema_from_transport=False)

@function_tool
def query_graphql(query: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    執行 GraphQL 查詢 (Query) 來獲取數據。
    
    參數:
        query: GraphQL 查詢字符串。
        variables: 查詢所需的變量。
        
    返回:
        JSON 格式的查詢結果。
    """
    client = _get_client()
    try:
        document = gql(query)
        result = client.execute(document, variable_values=variables)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"GraphQL Query 失敗: {e}")
        return f"錯誤: {str(e)}"

@function_tool
def mutate_graphql(mutation: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    執行 GraphQL 變更 (Mutation) 來新增、修改或刪除數據。
    
    參數:
        mutation: GraphQL 變更字符串。
        variables: 變更所需的變量。
        
    返回:
        JSON 格式的變更結果。
    """
    client = _get_client()
    try:
        document = gql(mutation)
        result = client.execute(document, variable_values=variables)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"GraphQL Mutation 失敗: {e}")
        return f"錯誤: {str(e)}"
