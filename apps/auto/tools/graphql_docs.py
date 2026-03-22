"""
apps/auto/tools/graphql_docs.py

提供豐富的 GraphQL 模式 (Schema) 說明，讓 AI 知道有哪些表格和欄位可用。
"""

from apps.auto.cai.core.tool import function_tool

GRAPHQL_SCHEMA_HELP = """
Hasura GraphQL 模式說明 (部分核心表格):

1. core_target (目標專案)
   - id: bigint (主鍵)
   - name: String (專案名稱)
   - description: String (描述)

2. core_seed (掃描種子)
   - id: bigint (主鍵)
   - target_id: bigint (關聯目標)
   - value: String (Domain/IP/URL)
   - type: String (DOMAIN, IP, URL)
   - is_active: Boolean

3. core_ip (IP 資產)
   - id: bigint (主鍵)
   - target_id: bigint
   - address: String (IP 位址，支援 IPv4 與 IPv6)
   - version: Int (IP 版本：4 或 6)
   - core_ports: [core_port] (關聯端口)
   - core_subdomain_ips: [core_subdomain_ip] (關聯子域名，透過中間表)

4. core_port (端口/服務)
   - id: bigint
   - ip_id: bigint
   - port_number: Int
   - protocol: String (tcp, udp)
   - state: String (open, closed)
   - service_name: String
   - service_version: String

5. core_subdomain (子域名資產)
   - id: bigint
   - name: String
   - is_active: Boolean
   - is_resolvable: Boolean
6. core_urlresult (URL 資產)
   - id: bigint
   - url: String
   - method: String
   - status_code: Int
   - title: String
   - content_length: Int
   - text: String (響應內容文本)
   - discovery_source: String (SCAN, CRAWL_html, JS_EXT, BRUTE, API)

7. core_vulnerability (漏洞)
   - id: bigint
   - name: String
   - severity: String (critical, high, medium, low, info)
   - template_id: String
   - tool_source: String
   - matched_at: String
   - status: String

8. core_step (自動化步驟)
   - id: bigint
   - command_template: String
   - status: String (PENDING, RUNNING, COMPLETED, FAILED)

提示:
- 使用 GraphQL 查詢時，表格名稱通常為 core_xxx。
- 查詢多個時使用 core_xxx(where: {...})。
- 變更數據使用 insert_core_xxx, update_core_xxx, delete_core_xxx。
"""

@function_tool
def get_graphql_schema_info() -> str:
    """
    獲取 GraphQL 資料庫的模式說明，包含主要表格和欄位定義。
    AI Agent 在編寫 GraphQL 語句前應先調用此工具。
    """
    return GRAPHQL_SCHEMA_HELP
