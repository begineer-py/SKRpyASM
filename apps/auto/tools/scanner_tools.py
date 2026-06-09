import logging
import requests
from django.conf import settings
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)

# 從設定檔讀取 API Base URL，預留未來多伺服器部署彈性
API_BASE_URL = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")

class ScannerToolsMixin:
    """
    Manual wrappers for core scanner endpoints.
    These tools abstract away ExecutionNode lifecycle management from the AI to
    prevent schema or lifecycle hallucinations.
    """

    def _dispatch_scanner(self, overview_id: int, tool_name: str, endpoint: str, payload: dict, description: str = "") -> str:
        try:
            from apps.core.models import ExecutionGraph, ExecutionNode
            from apps.core.services import ExecutionService

            graph = getattr(self, "_execution_graph", None)
            node = getattr(self, "_current_execution_node", None)
            if graph is None:
                graph_id = getattr(self, "_current_execution_graph_id", None)
                graph = ExecutionGraph.objects.filter(id=graph_id).first() if graph_id else None
            if node is None:
                node_id = getattr(self, "_current_execution_node_id", None)
                node = ExecutionNode.objects.filter(id=node_id).first() if node_id else None

            if graph is not None:
                payload["execution_graph_id"] = graph.id
            if node is not None:
                payload["execution_node_id"] = node.id
            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "scanner_dispatch_started",
                    status="started",
                    content=description or tool_name,
                    payload={
                        "overview_id": overview_id,
                        "endpoint": endpoint,
                        "payload": payload,
                        "execution_graph_id": getattr(graph, "id", None),
                        "execution_node_id": getattr(node, "id", None),
                    },
                    tool_name=tool_name,
                )

            # 發送本地 API 請求
            # Defensive normalization: avoid accidental double '/api/api' prefixes.
            if endpoint.startswith("/api/"):
                endpoint = endpoint[len("/api") :]
            url = f"{API_BASE_URL.rstrip('/')}{endpoint}"
            resp = requests.post(url, json=payload)
            
            if resp.status_code >= 400:
                summary = (description or "Scanner dispatch failed").strip()
                details = f"[FAILED] API responded with {resp.status_code}: {resp.text}"
                if node is not None:
                    ExecutionService.fail_node(
                        node,
                        error={"status_code": resp.status_code, "response": resp.text[:4000]},
                        content=details,
                        payload={"overview_id": overview_id, "endpoint": endpoint},
                    )
                if hasattr(self, "emit_thread_event"):
                    self.emit_thread_event(
                        "scanner_dispatch_error",
                        status="failed",
                        content=details,
                        payload={
                            "overview_id": overview_id,
                            "endpoint": endpoint,
                            "status_code": resp.status_code,
                            "execution_graph_id": getattr(graph, "id", None),
                            "execution_node_id": getattr(node, "id", None),
                        },
                        tool_name=tool_name,
                    )
                return f"CRITICAL_FAILURE: API ({endpoint}) 失敗 (HTTP {resp.status_code}): {resp.text}"

            if node is not None:
                ExecutionService.wait_node(
                    node,
                    wait_reason="ASYNC_CALLBACK",
                    content=f"{tool_name} dispatched and waiting for async callback",
                    payload={"overview_id": overview_id, "endpoint": endpoint, "response": resp.text[:2000]},
                )
            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "scanner_dispatched",
                    status="waiting_for_async",
                    content=f"{tool_name} dispatched with execution node #{getattr(node, 'id', None)}",
                    payload={
                        "overview_id": overview_id,
                        "endpoint": endpoint,
                        "response": resp.text[:2000],
                        "execution_graph_id": getattr(graph, "id", None),
                        "execution_node_id": getattr(node, "id", None),
                    },
                    tool_name=tool_name,
                )
            return f"工具 {tool_name} 已成功發送，ExecutionNode #{getattr(node, 'id', 'N/A')} 已進入 WAITING。請等待任務回調或進行其他動作。"
        except Exception as e:
            logger.error(f"Scanner dispatch failed: {e}")
            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "scanner_dispatch_error",
                    status="failed",
                    content=str(e),
                    payload={"overview_id": overview_id, "endpoint": endpoint},
                    tool_name=tool_name,
                )
            return f"CRITICAL_FAILURE: 內部執行例外錯誤: {e}"

    @method_tool
    def run_flaresolverr_crawler(self, overview_id: int = None, target_url: str = "") -> str:
        """
        [Phase A - Surface Mapping] 使用 Flaresolverr 爬取指定網頁 (GET)。
        會自動找出 URL、Form、Parameters。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            target_url: 完整的網址 (例如 'https://example.com/')
        """
        return self._dispatch_scanner(
            # API_BASE_URL already ends with /api, so endpoints should NOT start with /api
            overview_id, "flaresolverr", "/flaresolverr/start_scanner", 
            {"url": target_url, "method": "GET"}, "Flaresolverr Crawl"
        )

    @method_tool
    def run_flaresolverr_request(
        self,
        overview_id: int = None,
        target_url: str = "",
        method: str = "GET",
        body: str | None = None,
        content_type: str | None = None,
        host_header: str | None = None,
        headers: dict | None = None,
        cookies: str | None = None,
        session_key: str | None = None,
        refresh_session: bool = False,
    ) -> str:
        """Send a single HTTP request via FlareSolverr with session reuse.

        This is designed for AI-driven form submission / API probing under CF/WAF.
        The platform will log request/response under the active ExecutionNode.

        Use host_header to override the HTTP Host header (e.g. for vhost routing).

        Args:
            overview_id: (Optional) 當前 Overview ID。自動注入。
            target_url: 目標 URL。
        """

        payload = {
            "url": target_url,
            "method": method,
            "body": body,
            "content_type": content_type,
            "host_header": host_header,
            "headers": headers or {},
            "cookies": cookies,
            "session_key": session_key,
            "refresh_session": refresh_session,
        }
        return self._dispatch_scanner(
            overview_id,
            "flaresolverr-request",
            "/flaresolverr/send_request",
            payload,
            f"FlareSolverr Request {method} {target_url}",
        )
        
    @method_tool
    def run_subfinder_discovery(self, overview_id: int = None, seed_id: int = None) -> str:
        """
        [Phase C - Deep Discovery] 呼叫 Subfinder 從 Seed 發掘子域名。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            seed_id: 對應的 Seed ID
        """
        return self._dispatch_scanner(
            overview_id, "subfinder", "/scanners/subdomain/start_subfinder", 
            {"seed_id": seed_id}, "Subfinder Subdomain Enum"
        )
        
    @method_tool
    def run_gau_url_discovery(self, overview_id: int = None, subdomain_name: str = "") -> str:
        """
        [Phase C - Deep Discovery] 呼叫 GAU 被動收集網域的歷史 URL。

        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            subdomain_name: 目標子域名「字串」(e.g., 'vuln-f9wi.onrender.com')，這『不是』ID！
        """
        return self._dispatch_scanner(
            overview_id, "gau", "/scanners/crawler/get_all_url",
            {"name": subdomain_name, "scan_type": "passive"}, "GAU Historical URL Scan"
        )

    @method_tool
    def run_katana_crawl(self, overview_id: int = None, subdomain_name: str = "", depth: int = 3) -> str:
        """
        [Phase C - Active URL Discovery] 使用 Katana 主動爬取子域名，發現當前存活的 URL。
        補充 GAU 被動歷史資料的不足（GAU 可能已過時）。
        建議在 GAU 之後、Flaresolverr 深度分析之前執行。

        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            subdomain_name: 目標子域名「字串」(e.g., 'example.com')，這『不是』ID！
            depth: 爬取深度 (預設 3)
        """
        return self._dispatch_scanner(
            overview_id, "katana", "/scanners/crawler/katana",
            {"name": subdomain_name, "depth": depth}, f"Katana Active Crawl: {subdomain_name}"
        )

    @method_tool
    def run_nuclei_tech_scan_subdomains(self, overview_id: int = None, subdomain_ids: list[int] = None) -> str:
        """
        [Phase D - Tech Fingerprint] 在子域上執行 Nuclei 技術堆疊掃描 (Tech-stack)。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            subdomain_ids: 要掃描的子域名 ID 列表。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-tech", "/scanners/vuln/subs_tech", 
            {"ids": subdomain_ids}, "Nuclei Subdomain Tech Scan"
        )

    @method_tool
    def run_nuclei_tech_scan_urls(self, overview_id: int = None, url_ids: list[int] = None) -> str:
        """
        [Phase D - Tech Fingerprint] 在 URL 上執行 Nuclei 技術堆疊掃描 (Tech-stack)。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            url_ids: 要掃描的 URL ID 列表。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-tech", "/scanners/vuln/urls_tech", 
            {"ids": url_ids}, "Nuclei URL Tech Scan"
        )

    @method_tool
    def run_nuclei_vuln_scan_urls(self, overview_id: int = None, url_ids: list[int] = None) -> str:
        """
        [Phase E - Vulnerability Scan] 在 URL 上執行 Nuclei 的「漏洞」模板掃描 (Vuln)。
        注意：請先完成 A~D 階段再調用此工具。

        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            url_ids: 要掃描的 URL ID 列表。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-vuln", "/scanners/vuln/urls", 
            {"ids": url_ids, "tags": []}, "Nuclei URL Vulnerability Scan"
        )

    @method_tool
    def run_nuclei_vuln_scan_subdomains(self, overview_id: int = None, subdomain_ids: list[int] = None) -> str:
        """
        [Phase E - Vulnerability Scan] 在子域名上執行 Nuclei 的「漏洞」模板掃描 (Vuln)。

        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            subdomain_ids: 要掃描的子域名 ID 列表。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-vuln", "/scanners/vuln/subdomains", 
            {"ids": subdomain_ids, "tags": []}, "Nuclei Subdomain Vulnerability Scan"
        )

    @method_tool
    def run_nmap_port_scan(self, overview_id: int = None, ip_id: int = None, seed_id: int = None) -> str:
        """
        [Phase C - Deep Discovery] 針對發現的 IP 執行 Nmap Full Port Scan 掃描。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            ip_id: 要掃描的 IP 資產的 ID (整數)
            seed_id: 該 IP 對應的 Seed ID (整數)
        """
        try:
            from apps.core.models import IP
            ip_obj = IP.objects.filter(id=ip_id).first()
            if not ip_obj:
                return f"CRITICAL_FAILURE: 找不到 IP 資產 (ID: {ip_id})，請先確認資料庫中存在此 IP。"
            ip_str = ip_obj.address
        except Exception as e:
            return f"CRITICAL_FAILURE: 查詢 IP 資產時發生錯誤: {e}"
        
        return self._dispatch_scanner(
            overview_id, "nmap", "/scanners/nmap/start_scan", 
            {"ip": ip_str, "seed_ids": [seed_id], "scan_rate": 4, "scan_ports": "top-1000"}, 
            f"Nmap Port Scan for {ip_str}"
        )

    @method_tool
    def analyze_javascript_file(self, overview_id: int = None, js_id: int = None, js_type: str = "") -> str:
        """
        對抓取到的 JavaScript 檔案進行 Nuclei JS 分析。
        
        Args:
            overview_id: (Optional) 目標目前的 Overview ID。自動注入。
            js_id: 提取到的 JS ID
            js_type: 必須是 "inline" 或 "external"
        """
        if js_type not in ["inline", "external"]:
            return "CRITICAL_FAILURE: js_type 必須為 'inline' 或 'external'"
            
        return self._dispatch_scanner(
            overview_id, "js-analyze", "/flaresolverr/json_analyze", 
            {"id": js_id, "type": js_type}, "JavaScript Nuclei Analysis"
        )
