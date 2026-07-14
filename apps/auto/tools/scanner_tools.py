import logging
import requests
from urllib.parse import urlparse
from django.conf import settings
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)

# 從設定檔讀取 API Base URL，預留未來多伺服器部署彈性
API_BASE_URL = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")


def _ensure_subdomain(overview_id: int | None, name: str) -> int | None:
    """Ensure a Subdomain record exists for the given name under the Overview's Target.

    Creates one if none is found (auto-registers the root domain as a subdomain
    so GAU/Katana/Nuclei scanners can proceed without requiring Subfinder first).

    Returns:
        Subdomain ID if found/created, None otherwise.
    """
    try:
        from apps.core.models import Overview, Subdomain, Target

        # Normalize: strip http(s):// and trailing /path
        if name.startswith("http"):
            parsed = urlparse(name)
            name = parsed.hostname or name

        # Already exists?
        sub = Subdomain.objects.filter(name=name).first()
        if sub:
            return sub.id

        if not overview_id:
            return None
        overview = Overview.objects.filter(id=overview_id).first()
        if not overview or not overview.target_id:
            return None

        sub = Subdomain.objects.create(
            target_id=overview.target_id,
            name=name,
            is_active=True,
            is_resolvable=True,
        )

        # 綁定到 DOMAIN Seed，確保 DNS 解析鏈 (resolve_dns_for_seed) 可以找到此 subdomain。
        # resolve_dns_for_seed 使用 Subdomain.objects.filter(which_seed=seed) 查詢，
        # 若 which_seed 為空則 DNS chain 永遠掃不到此 subdomain → 無法取得 IP → 無法進行 Nmap/Nuclei。
        try:
            from apps.core.models import Seed
            domain_seed = Seed.objects.filter(
                target_id=overview.target_id, type="DOMAIN", is_active=True
            ).first()
            if domain_seed:
                # 透過 many-to-many 關聯 (SubdomainSeed through table)
                sub.which_seed.add(domain_seed)
                logger.info(
                    f"[_ensure_subdomain] Linked Subdomain #{sub.id} to Seed #{domain_seed.id} ({domain_seed.value})"
                )
        except Exception as link_err:
            logger.warning(f"[_ensure_subdomain] Failed to link to seed: {link_err}")

        logger.info(f"[_ensure_subdomain] Auto-created Subdomain #{sub.id} = {name} for target #{overview.target_id}")
        return sub.id
    except Exception as e:
        logger.warning(f"[_ensure_subdomain] Failed for name={name}: {e}")
        return None


class ScannerToolsMixin:
    """
    Manual wrappers for core scanner endpoints.
    These tools abstract away ExecutionNode lifecycle management from the AI to
    prevent schema or lifecycle hallucinations.
    """

    def _resolve_seed(self, overview_id: int, seed_type: str | None = "DOMAIN") -> int | None:
        """Resolve an active Seed ID from an Overview's Target.

        Prefers seeds of the given type (default DOMAIN for subdomain scanners).
        Falls back to any active seed if no matching type is found.
        If no seed exists at all, auto-creates a DOMAIN seed from the Target name.

        Args:
            overview_id: Overview ID (auto-injected by @method_tool).
            seed_type: Preferred seed type filter (default 'DOMAIN').

        Returns:
            Seed ID if found/created, None otherwise.
        """
        if not overview_id:
            return None
        try:
            from apps.core.models import Overview, Seed, Target
            overview = Overview.objects.filter(id=overview_id).first()
            if not overview or not overview.target_id:
                return None
            # 1. Prefer seed of requested type
            if seed_type:
                seed = Seed.objects.filter(
                    target_id=overview.target_id, type=seed_type, is_active=True
                ).first()
                if seed:
                    return seed.id
            # 2. Fallback: any active seed
            seed = Seed.objects.filter(
                target_id=overview.target_id, is_active=True
            ).first()
            if seed:
                return seed.id
            # 3. Auto-create a DOMAIN seed from the target name
            target = Target.objects.filter(id=overview.target_id).first()
            if target and target.name:
                domain = target.name.lower().strip()
                # Strip http(s):// prefix if present
                for prefix in ('https://', 'http://'):
                    if domain.startswith(prefix):
                        domain = domain[len(prefix):]
                domain = domain.split('/')[0]  # Remove path
                seed = Seed.objects.create(
                    target_id=overview.target_id,
                    value=domain,
                    type='DOMAIN',
                    is_active=True,
                )
                logger.info(f"[_resolve_seed] Auto-created DOMAIN seed #{seed.id} = {domain} for target #{overview.target_id}")
                return seed.id
            return None
        except Exception as e:
            logger.warning(f"[_resolve_seed] Failed for overview_id={overview_id}: {e}")
            return None

    _WALK_FK_MAP = {
        "IP": "ip_asset_id",
        "SUBDOMAIN": "subdomain_asset_id",
        "URL": "url_asset_id",
        "ENDPOINT": "endpoint_asset_id",
        "PORT": "port_asset_id",
    }

    def _validate_walk_constraint(self, overview_id, asset_checks) -> str:
        """Check if assets are in active AttackPlan scope. Returns warning string (empty if OK).

        Args:
            overview_id: Overview ID.
            asset_checks: list of (asset_type, asset_id_or_list).
        """
        if not overview_id:
            return ""
        try:
            from apps.core.models import Overview, AttackPlan, AssetVectorLink
            overview = Overview.objects.filter(id=overview_id).first()
            if not overview or not overview.target_id:
                return ""
            active_plan = AttackPlan.objects.filter(
                target_id=overview.target_id, status="ACTIVE"
            ).first()
            if not active_plan:
                return ""

            warnings = []
            for asset_type, asset_ids in asset_checks:
                if isinstance(asset_ids, int):
                    asset_ids = [asset_ids]
                elif not asset_ids:
                    continue
                fk_field = self._WALK_FK_MAP.get(asset_type.upper())
                if not fk_field:
                    continue
                for aid in asset_ids:
                    in_plan = AssetVectorLink.objects.filter(
                        actions__plan=active_plan,
                        asset_type=asset_type.upper(),
                        **{fk_field: aid},
                    ).exists()
                    if not in_plan:
                        warnings.append(
                            f"⚠️ {asset_type}#{aid} not in active AttackPlan#{active_plan.id} "
                            f"— use add_action to register it before scanning."
                        )

            if warnings:
                return "\n" + "\n".join(warnings) + "\n"
            return ""
        except Exception:
            return ""

    def _dispatch_scanner(self, overview_id: int, tool_name: str, endpoint: str, payload: dict, description: str = "") -> str:
        try:
            from apps.core.models import ExecutionGraph, ExecutionNode
            from apps.core.services import ExecutionService

            # Defensive: overview_id 可能是 Overview 物件（FK 反查）— 強制取 int，
            # 避免後續 emit_thread_event / requests.post(json=) JSON 序列化失敗。
            if overview_id is not None and not isinstance(overview_id, int):
                overview_id = getattr(overview_id, "id", overview_id)

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
        payload = {"url": target_url, "method": "GET"}
        seed_id = self._resolve_seed(overview_id)
        if seed_id:
            payload["seed_id"] = seed_id
        return self._dispatch_scanner(
            overview_id, "flaresolverr", "/flaresolverr/start_scanner", 
            payload, "Flaresolverr Crawl"
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
            method: HTTP 方法（預設 GET；可選 POST/PUT/DELETE 等）。
            body: 請求主體（POST/PUT 時使用，純文字）。
            content_type: 請求的 Content-Type（例如 'application/json'、'application/x-www-form-urlencoded'）。
            host_header: 覆寫 HTTP Host header（用於 vhost 路由/繞過）。
            headers: 額外自訂 headers（dict）。
            cookies: Cookie 字串（例如 'key1=val1; key2=val2'）。
            session_key: 復用既有 FlareSolverr session 的 key（省略則建立新 session）。
            refresh_session: 是否在送出前刷新/重置 session（預設 False）。
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
        seed_id = self._resolve_seed(overview_id)
        if seed_id:
            payload["seed_id"] = seed_id
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
            seed_id: 對應的 Seed ID（若省略則自動從 Overview 解析）
        """
        if not seed_id:
            seed_id = self._resolve_seed(overview_id)
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
        # Auto-register Subdomain if missing (GAU API requires existing Subdomain record)
        _ensure_subdomain(overview_id, subdomain_name)
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
        # Auto-register Subdomain if missing (Katana API requires existing Subdomain record)
        _ensure_subdomain(overview_id, subdomain_name)
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
        return self._validate_walk_constraint(overview_id, [("SUBDOMAIN", subdomain_ids)]) + self._dispatch_scanner(
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
        return self._validate_walk_constraint(overview_id, [("URL", url_ids)]) + self._dispatch_scanner(
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
        return self._validate_walk_constraint(overview_id, [("URL", url_ids)]) + self._dispatch_scanner(
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
        return self._validate_walk_constraint(overview_id, [("SUBDOMAIN", subdomain_ids)]) + self._dispatch_scanner(
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
            seed_id: 該 IP 對應的 Seed ID（若省略則自動從 Overview 解析）
        """
        try:
            from apps.core.models import IP
            ip_obj = IP.objects.filter(id=ip_id).first()
            if not ip_obj:
                return f"CRITICAL_FAILURE: 找不到 IP 資產 (ID: {ip_id})，請先確認資料庫中存在此 IP。"
            ip_str = ip_obj.address
        except Exception as e:
            return f"CRITICAL_FAILURE: 查詢 IP 資產時發生錯誤: {e}"
        
        if not seed_id:
            seed_id = self._resolve_seed(overview_id)
        seed_ids = [seed_id] if seed_id else []
        
        return self._validate_walk_constraint(overview_id, [("IP", ip_id)]) + self._dispatch_scanner(
            overview_id, "nmap", "/scanners/nmap/start_scan",
            {"ip": ip_str, "seed_ids": seed_ids, "scan_rate": 4, "scan_ports": "top-1000"},
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
