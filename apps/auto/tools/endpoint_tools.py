import logging
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class EndpointMixin:
    """
    Endpoint Intelligence Tools Mixin
    Provides tools for querying and managing API endpoints, parameters, and URL intelligence.
    """

    @method_tool
    def query_endpoints(self, target_id: int, method_filter: str = None, path_contains: str = None, limit: int = 30) -> str:
        """
        查詢目標的所有 API Endpoint 列表，包含每個端點已知的參數 (URLParameter)。
        可依 HTTP 方法或路徑關鍵字過濾。適合在發動攻擊前了解目標 API 表面積。

        Args:
            target_id: Target 的 ID。
            method_filter: (選填) 依 HTTP 方法過濾，如 'POST', 'GET'。
            path_contains: (選填) 路徑包含的關鍵字，如 '/api/' 或 '/admin'。
            limit: (選填) 最多回傳幾筆，預設 30。
        """
        try:
            from apps.core.models.url_assets import Endpoint

            qs = Endpoint.objects.filter(target_id=target_id).prefetch_related(
                'query_parameters', 'related_subdomains'
            ).order_by('-last_seen')

            if method_filter:
                qs = qs.filter(method=method_filter.upper())
            if path_contains:
                qs = qs.filter(path__icontains=path_contains)

            endpoints = qs[:limit]
            if not endpoints:
                return f"Target#{target_id} 沒有找到符合條件的 Endpoint。"

            lines = [f"=== Endpoints for Target#{target_id} (顯示 {len(endpoints)} 筆) ==="]
            for ep in endpoints:
                params = ep.query_parameters.all()
                param_list = ""
                if params:
                    param_parts = []
                    for p in params:
                        val_hint = f"={p.value[:30]}" if p.value else ""
                        param_parts.append(f"{p.key}{val_hint}[{p.param_location}/{p.source_type or '?'}]")
                    param_list = " | Params: " + ", ".join(param_parts)
                lines.append(f"  EP#{ep.id} [{ep.method}] {ep.path}{param_list}")

            lines.append("=== END ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"query_endpoints failed for target {target_id}: {e}")
            return f"查詢 Endpoints 失敗: {e}"

    @method_tool
    def create_endpoint(self, target_id: int, path: str, method: str = "GET", subdomain_id: int = None) -> str:
        """
        當你從 JS 分析、API 回應或其他偵察手段發現了資料庫中尚未記錄的新 API Endpoint 時，
        使用此工具登記它。去重保護：若已存在則直接回傳現有 ID。

        Args:
            target_id: Target 的 ID。
            path: Endpoint 路徑（如 '/api/v1/users/export' 或 '/admin/secret'）。
            method: HTTP 方法（'GET', 'POST', 'PUT', 'DELETE', 'PATCH'），預設 'GET'。
            subdomain_id: (選填) 關聯的 Subdomain ID。
        """
        try:
            from apps.core.models.url_assets import Endpoint

            ep, created = Endpoint.objects.get_or_create(
                target_id=target_id,
                path=path,
                method=method.upper(),
            )
            if subdomain_id:
                ep.related_subdomains.add(subdomain_id)

            if created:
                return (
                    f"✅ 新 Endpoint 已登記: EP#{ep.id} [{ep.method}] {ep.path}\n"
                    f"可使用 add_endpoint_parameter 為此端點添加已知參數。"
                )
            else:
                params_count = ep.query_parameters.count()
                return f"Endpoint 已存在: EP#{ep.id} [{ep.method}] {ep.path} (現有 {params_count} 個參數)。"
        except Exception as e:
            logger.error(f"create_endpoint failed: {e}")
            return f"建立 Endpoint 失敗: {e}"

    @method_tool
    def add_endpoint_parameter(
        self,
        endpoint_id: int,
        key: str,
        value: str = None,
        param_location: str = "body",
        source_type: str = "javascript",
        data_type: str = None,
    ) -> str:
        """
        為指定的 Endpoint 添加一個新的參數（隱藏參數、注入點、未文檔化欄位等）。
        若此 key 在此 endpoint 的相同位置已存在，會更新 value 而不是重複建立。

        Args:
            endpoint_id: Endpoint 的 ID（來自 query_endpoints 或 create_endpoint 回傳）。
            key: 參數名稱，如 'csrfmiddlewaretoken', 'debug', '_method', 'user_id'。
            value: (選填) 觀察到的範例值，如 'true', '1', 'abc123'。
            param_location: 參數位置 ('query' 或 'body')，預設 'body'。
            source_type: 來源類型 ('form', 'javascript', 'querystring')，預設 'javascript'。
            data_type: (選填) 推斷的資料型別，如 'string', 'int', 'bool', 'json'。
        """
        try:
            from apps.core.models.url_assets import Endpoint, URLParameter

            try:
                ep = Endpoint.objects.get(id=endpoint_id)
            except Endpoint.DoesNotExist:
                return f"CRITICAL_FAILURE: Endpoint ID {endpoint_id} 不存在。請先用 query_endpoints 查詢。"

            param, created = URLParameter.objects.update_or_create(
                which_endpoint=ep,
                param_location=param_location,
                key=key,
                defaults={
                    "value": value,
                    "source_type": source_type,
                    "data_type": data_type,
                }
            )

            action = "✅ 新參數已添加" if created else "🔄 參數已更新"
            val_hint = f" = '{value[:50]}'" if value else ""
            return (
                f"{action}: EP#{ep.id} [{ep.method}] {ep.path}\n"
                f"  {key}{val_hint} [{param_location}/{source_type}]"
            )
        except Exception as e:
            logger.error(f"add_endpoint_parameter failed for endpoint {endpoint_id}: {e}")
            return f"添加 Endpoint 參數失敗: {e}"

    @method_tool
    def get_url_intelligence(self, url_id: int) -> str:
        """
        【核心情報工具】輸入 URL ID，取得資料庫中已儲存的所有情報：
        - HTTP 狀態、標題、Headers
        - HTML Forms（含 action、method、所有 input 欄位名稱）
        - 發現的 Links 與 Endpoints
        - MetaTags（可推斷技術棧）
        - 分析發現 (AnalysisFinding)：API Key、敏感 pattern 等
        - TechStack：已偵測的技術
        - Vulnerabilities：已記錄的漏洞

        【歷史快取直接派發】若 content_fetch_status=SUCCESS_FETCHED，
        表示已有完整爬取記錄，系統直接返回快取情報，無需重新爬取。
        請勿對已有情報的 URL 再次呼叫 run_flaresolverr_crawler。

        【意圖觸發掃描】若 content_fetch_status=PENDING，代表尚未爬取。
        系統會自動靜默觸發爬蟲任務，同時在回傳中提示。你無需再手動下達掃描指令。

        當你想了解一個 URL 的完整情況時，優先呼叫此工具，不要猜測。

        Args:
            url_id: URLResult 的資料庫 ID（從 get_target_context 取得）。
        """
        try:
            from apps.core.models.url_assets import URLResult

            try:
                url_obj = URLResult.objects.prefetch_related(
                    'forms', 'links', 'meta_tags', 'findings',
                    'found_endpoints__query_parameters',
                    'technologies',
                    'vulnerabilities',
                ).get(id=url_id)
            except URLResult.DoesNotExist:
                return f"URL ID {url_id} 不存在於資料庫中。請用 get_target_context 確認正確的 URL IDs。"

            sections = []
            sections.append(f"=== URL INTELLIGENCE (ID: {url_id}) ===")
            sections.append(f"URL: {url_obj.url}")
            sections.append(f"Status: {url_obj.status_code} | Title: {url_obj.title}")
            sections.append(f"Fetch Status: {url_obj.content_fetch_status}")

            # Headers
            if url_obj.headers:
                interesting_headers = {
                    k: v for k, v in (url_obj.headers if isinstance(url_obj.headers, dict) else {}).items()
                    if k.lower() in ('server', 'x-powered-by', 'content-type', 'set-cookie',
                                     'x-frame-options', 'content-security-policy', 'strict-transport-security',
                                     'x-content-type-options', 'access-control-allow-origin')
                }
                if interesting_headers:
                    sections.append(f"\n[Security-Relevant Headers]\n{interesting_headers}")

            # Forms
            forms = list(url_obj.forms.all())
            if forms:
                sections.append(f"\n[Forms Found: {len(forms)}]")
                for f in forms:
                    params = f.parameters  # JSONField
                    field_names = [p.get('name', '?') for p in params] if isinstance(params, list) else list(params.keys()) if isinstance(params, dict) else [str(params)]
                    sections.append(f"  FORM: {f.method} {f.action} | Fields: {field_names}")
            else:
                sections.append("\n[Forms] None found.")

            # Endpoints
            endpoints = list(url_obj.found_endpoints.all().prefetch_related('query_parameters'))
            if endpoints:
                sections.append(f"\n[Endpoints Discovered: {len(endpoints)}]")
                for ep in endpoints[:10]:
                    params = [p.key for p in ep.query_parameters.all()]
                    sections.append(f"  [{ep.method}] {ep.path} | Params: {params}")

            # Links
            links = list(url_obj.links.values_list('href', flat=True)[:15])
            if links:
                sections.append(f"\n[Links ({len(links)} shown)]: {links}")

            # MetaTags
            meta_tags = list(url_obj.meta_tags.values_list('attributes', flat=True)[:8])
            if meta_tags:
                sections.append(f"\n[MetaTags]: {meta_tags}")

            # AnalysisFindings (sensitive patterns, API keys, etc.)
            findings = list(url_obj.findings.values('pattern_name', 'match_content')[:10])
            if findings:
                sections.append(f"\n[Analysis Findings – Sensitive Patterns!]")
                for fi in findings:
                    sections.append(f"  [{fi['pattern_name']}]: {fi['match_content'][:100]}")

            # TechStack
            try:
                techs = list(url_obj.technologies.values_list('name', 'version')[:10])
                if techs:
                    tech_str = [f"{n} {v or ''}".strip() for n, v in techs]
                    sections.append(f"\n[Tech Stack]: {tech_str}")
            except Exception:
                pass

            # Vulnerabilities
            try:
                vulns = list(url_obj.vulnerabilities.values('name', 'severity', 'template_id')[:5])
                if vulns:
                    sections.append(f"\n[Known Vulnerabilities!]: {vulns}")
            except Exception:
                pass

            # Content preview (cleaned HTML, truncated)
            content = url_obj.cleaned_html or url_obj.text or ""
            if content:
                sections.append(f"\n[Content Preview (2000 chars)]\n{content[:2000]}")
                sections.append("\n✅ CACHED: This URL has existing crawl data — no need to re-crawl with run_flaresolverr_crawler.")
            else:
                if url_obj.content_fetch_status == "PENDING":
                    # ═══ Intent-to-Scan Auto-Trigger ═══
                    # AI 查詢 PENDING URL 等於表達「想掃描它」的意圖，後端靜默觸發爬蟲
                    triggered = False
                    try:
                        from django.conf import settings
                        import requests as _req
                        api_base = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")
                        # Find overview for this URL's target to create step
                        from apps.core.models.analyze.overview import Overview
                        overview_qs = Overview.objects.filter(
                            target=url_obj.target,
                            status__in=["PLANNING", "EXECUTING"]
                        ).order_by("-id")
                        active_ov = overview_qs.first()
                        if active_ov:
                            from apps.core.models.analyze.Step import Step, StepNote
                            from django.utils import timezone
                            step = Step.create_next(
                                overview_id=active_ov.id,
                                status="WAITING_FOR_ASYNC"
                            )
                            StepNote.objects.create(
                                step=step,
                                content=f"[Auto-Intent Crawl] AI queried PENDING URL {url_obj.url} — auto-triggering Flaresolverr crawl"
                            )
                            payload = {"url": url_obj.url, "method": "GET", "callback_step_id": step.id}
                            _req.post(f"{api_base.rstrip('/')}/flaresolverr/start_scanner", json=payload, timeout=5)
                            triggered = True
                    except Exception as trig_err:
                        logger.warning(f"[Intent-to-scan] Auto-trigger failed for url_id={url_id}: {trig_err}")

                    if triggered:
                        sections.append(
                            "\n[Content] ⏳ PENDING — no content yet. "
                            "🔫 INTENT-TO-SCAN: System has auto-triggered a Flaresolverr crawl for this URL. "
                            "Continue with other work and check back after the crawl callback."
                        )
                    else:
                        sections.append(
                            "\n[Content] ⏳ PENDING — no content yet. "
                            "Use run_flaresolverr_crawler(target_url=...) to fetch it."
                        )
                else:
                    sections.append(f"\n[Content] No parseable HTML content (status={url_obj.content_fetch_status}). Already attempted crawl — skip this URL and move on.")

            sections.append("=== END URL INTELLIGENCE ===")
            return "\n".join(sections)

        except Exception as e:
            logger.error(f"get_url_intelligence failed for url_id={url_id}: {e}")
            return f"Error fetching URL intelligence for ID {url_id}: {e}"
