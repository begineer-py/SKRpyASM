import logging
from apps.ai_assistant import method_tool
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class ReconnaissanceMixin:
    """
    Reconnaissance & Context Tools Mixin
    Provides tools for querying target context, managing overviews, and checking scan status.
    """

    @method_tool
    def get_target_context(self, target_name: str) -> str:
        """
        【必須第一個呼叫】在進行任何操作前，先用此工具查詢目標的所有有效 ID。
        返回：active overview_id、target_id、subdomain IDs、IP IDs、seed IDs、URL result IDs。
        嚴禁在沒有呼叫此工具的情況下自行猜測或假設任何 ID。

        Args:
            target_name: 目標名稱或域名 (e.g., 'vuln-f9wi.onrender.com')。
        """
        try:
            from apps.core.models import Target, Overview, Subdomain, IP, Seed
            from apps.core.models.url_assets import URLResult
            from django.utils import timezone
            
            now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')

            target = Target.objects.filter(name=target_name).first()
            if not target:
                # 嘗試模糊搜尋
                target = Target.objects.filter(name__icontains=target_name.split(".")[0]).first()
            if not target:
                all_targets = list(Target.objects.values("id", "name"))
                return f"找不到目標 '{target_name}'。現有目標：{all_targets}。請用正確的 target_name 重新呼叫。"

            active_overview = Overview.objects.filter(
                target=target, status__in=["PLANNING", "EXECUTING"]
            ).order_by("-id").first()

            # If no active overview, fall back to most recent COMPLETED overview
            if not active_overview:
                active_overview = Overview.objects.filter(
                    target=target, status="COMPLETED"
                ).order_by("-id").first()

            subdomains = list(Subdomain.objects.filter(target=target).values("id", "name")[:15])
            ips = list(IP.objects.filter(target=target).values("id", "address")[:15])
            seeds = list(Seed.objects.filter(target=target).values("id", "type", "value")[:10])
            urls = list(URLResult.objects.filter(target=target).values("id", "url")[:15])

            if not active_overview:
                return (
                    f"=== TARGET CONTEXT ===\n"
                    f"Current System Time: {now_str}\n"
                    f"Target Name: {target.name}\n"
                    f"Target ID: {target.id}\n"
                    f"Active Overview: NONE - No PLANNING/EXECUTING/COMPLETED overview found.\n"
                    f"  ⚠ DO NOT call create_step or update_overview_status.\n"
                    f"  👉 You MUST call `create_overview` with target_id={target.id} to initialize a new overview, then call `get_target_context` again.\n"
                    f"Real Seeds: {seeds}\n"
                    f"Real Subdomains: {subdomains}\n"
                    f"Real IPs: {ips}\n"
                    f"Real URLs: {urls}\n"
                    f"=== END OF CONTEXT ==="
                )

            # ════════════════════════════════════════════════════════════════
            # Auto-bind thread_id when this agent was invoked by a parent
            # (Orchestrator delegation flow). The sub-thread was already
            # created by _run_as_tool — we just need to store its ID on the
            # overview so the frontend can display it and async scanners
            # can callback to the correct thread.
            # ════════════════════════════════════════════════════════════════
            if not active_overview.thread_id or not active_overview.parent_thread_id:
                _caller_id = getattr(self, '_caller_thread_id', None)
                if _caller_id:
                    update_fields = []
                    # 1. Bind thread_id (current sub-thread)
                    if not active_overview.thread_id:
                        from apps.core.models.ai_models import Thread
                        sub_thread = Thread.objects.filter(
                            name=f"subagent_automation_agent_for_thread_{_caller_id}"
                        ).first()
                        if sub_thread:
                            active_overview.thread_id = sub_thread.id
                            update_fields.append('thread_id')
                    
                    # 2. Bind parent_thread_id (caller)
                    if not active_overview.parent_thread_id:
                        active_overview.parent_thread_id = _caller_id
                        update_fields.append('parent_thread_id')
                    
                    if update_fields:
                        active_overview.save(update_fields=update_fields)
                        logger.info(f"[get_target_context] Auto-bound overview {active_overview.id} fields: {update_fields}")
            if hasattr(self, '_agent_overview_id') is not None and not self._agent_overview_id:
                self._agent_overview_id = active_overview.id

            is_completed = active_overview.status == "COMPLETED"
            context_prefix = "RECENTLY COMPLETED" if is_completed else "ACTIVE"

            steps_info = ""
            steps = active_overview.steps.all().prefetch_related('discovered_vectors', 'note_detail').order_by('id')
            if steps.exists():
                lines = []
                for s in steps:
                    av = s.discovered_vectors.first()
                    tool = av.name if av else "Unknown Vector"
                    desc = av.description if av else "No description"
                    note = s.note_detail.content if hasattr(s, 'note_detail') and s.note_detail else ""
                    lines.append(f"- Step[{s.id}] Status:{s.status} | Tool/Vector:{tool} | Desc:{desc} | Note:{note}")
                steps_info = "\n  " + "\n  ".join(lines)
            else:
                steps_info = "\n  No Steps created yet."

            bound_ips = list(active_overview.ips.values("id", "address")[:20])
            bound_subdomains = list(active_overview.subdomains.values("id", "name")[:20])
            bound_urls = list(active_overview.url_results.values("id", "url")[:20])
            bound_asset_counts = {
                "ips": active_overview.ips.count(),
                "subdomains": active_overview.subdomains.count(),
                "urls": active_overview.url_results.count(),
            }

            return (
                f"=== TARGET CONTEXT (USE ONLY THESE IDs) ===\n"
                f"Current System Time: {now_str}\n"
                f"Target Name: {target.name}\n"
                f"Target ID: {target.id}\n"
                f"{context_prefix} Overview ID: {active_overview.id}  ← USE THIS as overview_id in ALL tools\n"
                f"Overview Status: {active_overview.status}\n"
                f"Overview Thread ID: {active_overview.thread_id or '—'}  ← Your conversation thread\n"
                f"Overview Parent Thread ID: {active_overview.parent_thread_id or '—'}  ← Parent/caller thread\n"
                f"Overview Knowledge: {active_overview.knowledge}\n"
                f"Overview Plan: {active_overview.plan}\n"
                f"Overview Active Steps:{steps_info}\n"
                f"Overview Bound Asset Counts: {bound_asset_counts}\n"
                f"Overview Bound IPs (high-value/current scope): {bound_ips}\n"
                f"Overview Bound Subdomains (high-value/current scope): {bound_subdomains}\n"
                f"Overview Bound URLs (high-value/current scope): {bound_urls}\n"
                f"Real Seeds (use for Subfinder/crawler): {seeds}\n"
                f"Real Subdomains (use for Nuclei): {subdomains}\n"
                f"Real IPs (use for Nmap/Nuclei): {ips}\n"
                f"Real URLs (use for URL Nuclei/tech): {urls}\n"
                f"=== END OF CONTEXT ===\n"
                + (
                    f"NOTE: This overview is COMPLETED. If you need to continue investigation, "
                    f"call update_overview_status to set it back to EXECUTING."
                    if is_completed else
                    f"IMPORTANT: Call `bind_to_target(target_id={target.id})` to lock this session to this target and its overview. "
                    f"Once bound, you NO LONGER need to provide overview_id in tool calls."
                )
            )
        except Exception as e:
            logger.error(f"get_target_context failed: {e}")
            return f"查詢目標上下文失敗: {e}"

    @method_tool
    def create_overview(self, target_id: int, thread_id: int = None, parent_thread_id: int = None) -> str:
        """
        為沒有 Active Overview 的 Target 建立一個全新的 Overview。
        注意：若目標已存在 PLANNING/EXECUTING 的 Overview，此工具會直接回傳現有的，不會重複建立。
        建立後，請務必重新呼叫 get_target_context 來獲取新的 overview_id。

        Args:
            target_id: Target 的 ID。
            thread_id: 當前 AI 對話 Thread ID，用於接收非同步掃描器的 Callback。若不能取得，請保持為 None。
            parent_thread_id: 上層 Calling Agent 的 Thread ID。若上層要求非同步回調，請帶入此 ID。
        """
        try:
            from apps.core.models import Target, Overview
            from django.db import transaction
            from apps.core.models.ai_models import Thread
            target = Target.objects.get(id=target_id)

            # Fix: Ensure thread_id is None if it's 0 or empty string to avoid FK constraint violation
            if not thread_id:
                thread_id = None
            if not parent_thread_id:
                parent_thread_id = None

            # ══════════════════════════════════════════════════════════════
            # Auto-bind parent_thread_id & thread_id from caller context
            # This ensures parent notification works even if the LLM forgets
            # to pass these parameters explicitly.
            # ══════════════════════════════════════════════════════════════
            _caller_id = getattr(self, '_caller_thread_id', None)
            if _caller_id:
                if not parent_thread_id:
                    parent_thread_id = _caller_id
                if not thread_id:
                    sub_thread = Thread.objects.filter(
                        name=f"subagent_automation_agent_for_thread_{_caller_id}"
                    ).first()
                    if sub_thread:
                        thread_id = sub_thread.id

            # ⚠️ Idempotency 保護：防止重複建立
            with transaction.atomic():
                existing = Overview.objects.select_for_update().filter(
                    target=target,
                    status__in=["PLANNING", "EXECUTING", "NEEDS_GUIDANCE"]
                ).order_by("-id").first()
                if existing:
                    # Auto-bind parent_thread_id on existing overview too
                    if _caller_id and not existing.parent_thread_id and not parent_thread_id:
                        existing.parent_thread_id = _caller_id
                        existing.save(update_fields=['parent_thread_id'])
                    if hasattr(self, '_agent_overview_id') is not None:
                        self._agent_overview_id = existing.id
                    logger.warning(
                        f"create_overview called but active overview already exists "
                        f"(Overview#{existing.id}) for Target {target.name}. Returning existing."
                    )
                    return (
                        f"⚠️ Target {target.name} (ID: {target.id}) 已有 Active Overview (ID: {existing.id}, "
                        f"Status: {existing.status})。無需重複建立，請直接使用此 overview_id={existing.id}。"
                        f"請重新呼叫 get_target_context 確認。"
                    )

                overview = Overview.objects.create(
                    target=target,
                    status="PLANNING",
                    risk_score=50,
                    plan={"steps": []},
                    thread_id=thread_id,
                    parent_thread_id=parent_thread_id,
                )
            if hasattr(self, '_agent_overview_id') is not None:
                self._agent_overview_id = overview.id
            return f"成功為 Target {target.name} (ID: {target.id}) 建立新的 Overview (ID: {overview.id})。請重新呼叫 get_target_context。"
        except Exception as e:
            logger.error(f"Failed to create overview for target {target_id}: {e}")
            return f"建立 Overview 時發生錯誤: {e}"

    @method_tool
    def notify_caller_agent(self, overview_id: int = None, message: str = "") -> str:
        """
        如果在長期的非同步自動化任務結束拉！如果 Overview 中存有 parent_thread_id (調用你的上層 Agent)，
        利用此工具將最後的分析結果或是達成目標的消息傳回給上層 Agent 吧。
        
        Args:
            overview_id: (Optional) 當前 Overview 的 ID。自動注入。
            message: 要傳回給上層 Agent 的消息內容。
        """
        try:
            from apps.core.models import Overview
            from apps.core.models.ai_models import Thread
            from apps.ai_assistant.helpers.use_cases import create_message
            from django.contrib.auth import get_user_model
            
            overview = Overview.objects.get(id=overview_id)
            if not overview.parent_thread_id:
                return "此 Overview 沒有紀錄 parent_thread_id，無法進行回調通知。"
            
            thread_obj = Thread.objects.get(id=overview.parent_thread_id)
            User = get_user_model()
            system_user = thread_obj.created_by or User.objects.filter(is_superuser=True).first()
            
            create_message(
                assistant_id=thread_obj.assistant_id or "hacker_assistant_agent",
                thread=thread_obj,
                user=system_user,
                content=f"[SYSTEM: Layer 3 Async Completion Report For Overview {overview_id}]\n{message}",
            )
            return f"成功回調通知 Parent Thread {overview.parent_thread_id}。"
        except Exception as e:
            logger.error(f"Failed to notify caller agent for overview {overview_id}: {e}")
            return f"通知 Caller Agent 失敗: {e}"

    @method_tool
    def check_scanned_urls(
        self,
        target_id: int,
        fetch_status_filter: str = None,
        tech_analyzed_filter: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        檢查某個 Target 底下所有 URL 的抓取紀錄與狀態（支持分页和过滤）。

        在執行任何 Flaresolverr 爬蟲、Katana 掃描或其他 URL 掃描與抽取前，請務必先使用此工具，
        以確認該 URL 是否已經被抓取過 (例如 content_fetch_status='SUCCESS_FETCHED')，
        或是否已用過 Flaresolverr (used_flaresolverr=True)。
        防止重複執行無意義的掃描造成系統負載。

        Args:
            target_id: Target ID
            fetch_status_filter: 按 content_fetch_status 过滤 ('SUCCESS_FETCHED', 'FAILED_BLOCKED', 'PENDING' 等)
            tech_analyzed_filter: 按 is_tech_analyzed 过滤 (True/False/None)
            limit: 返回数量上限（默认 50，最大 200）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的 URL 扫描状态摘要
        """
        try:
            from apps.core.models.url_assets import URLResult

            query = URLResult.objects.filter(target_id=target_id)

            # 应用过滤条件
            if fetch_status_filter:
                query = query.filter(content_fetch_status=fetch_status_filter)

            if tech_analyzed_filter is not None:
                query = query.filter(is_tech_analyzed=tech_analyzed_filter)

            # 限制最大值
            limit = min(limit, 200)

            # 获取总数
            total = query.count()

            if total == 0:
                return f"No URLs found for Target ID {target_id} with the given filters."

            # 获取分页数据
            urls = query.values(
                "id", "url", "used_flaresolverr", "content_fetch_status",
                "status_code", "is_tech_analyzed", "is_vuln_scanned"
            ).order_by('-created_at')[offset:offset+limit]

            summary = f"URL Scan Status (showing {len(urls)}/{total}):\n"
            summary += f"Filters: fetch_status={fetch_status_filter}, tech_analyzed={tech_analyzed_filter}\n\n"

            for u in urls:
                used_fs_str = "Yes" if u["used_flaresolverr"] else "No"
                summary += f"[{u['id']}] {u['url']}\n"
                summary += f"  Status: {u['content_fetch_status']} (HTTP {u['status_code']})\n"
                summary += f"  FlareSolverr: {used_fs_str}\n"
                summary += f"  Tech Analyzed: {u['is_tech_analyzed']}, Vuln Scanned: {u['is_vuln_scanned']}\n\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} URLs\n"

            return summary
        except Exception as e:
            return f"Error checking scanned URLs: {str(e)}"

    @method_tool
    def check_scanned_subdomains(
        self,
        target_id: int,
        resolvable_filter: bool = None,
        tech_analyzed_filter: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        檢查某個 Target 底下所有子域名 (Subdomain) 的掃描狀態與概況（支持分页和过滤）。

        在重複使用 Amass, Subfinder 等工具挖掘子域名，或是使用 dnsx/Nuclei 前，
        請務必先使用此工具來「感知」當前資料庫中已經找出的子域名，
        並察看是否已經有 is_tech_analyzed=True 或是否已經成功解析 IP。
        避免永無止盡的執行相同的掃描。

        Args:
            target_id: Target ID
            resolvable_filter: 按 is_resolvable 过滤 (True/False/None)
            tech_analyzed_filter: 按 is_tech_analyzed 过滤 (True/False/None)
            limit: 返回数量上限（默认 50，最大 200）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的子域名扫描状态摘要
        """
        try:
            from apps.core.models.domain import Subdomain

            query = Subdomain.objects.filter(target_id=target_id)

            # 应用过滤条件
            if resolvable_filter is not None:
                query = query.filter(is_resolvable=resolvable_filter)

            if tech_analyzed_filter is not None:
                query = query.filter(is_tech_analyzed=tech_analyzed_filter)

            # 限制最大值
            limit = min(limit, 200)

            # 获取总数
            total = query.count()

            if total == 0:
                return f"No Subdomains found for Target ID {target_id} with the given filters."

            # 获取分页数据
            subdomains = query.values(
                "id", "name", "is_resolvable", "is_tech_analyzed", "last_scan_type"
            ).order_by('-created_at')[offset:offset+limit]

            summary = f"Subdomain Scan Status (showing {len(subdomains)}/{total}):\n"
            summary += f"Filters: resolvable={resolvable_filter}, tech_analyzed={tech_analyzed_filter}\n\n"

            for s in subdomains:
                res_str = "Yes" if s["is_resolvable"] else "No"
                tech_str = "Yes" if s["is_tech_analyzed"] else "No"
                summary += f"[{s['id']}] {s['name']}\n"
                summary += f"  Resolvable: {res_str}, Tech Analyzed: {tech_str}\n"
                summary += f"  Last Scan: {s['last_scan_type']}\n\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} subdomains\n"

            return summary
        except Exception as e:
            return f"Error checking scanned subdomains: {str(e)}"

    @method_tool
    def query_urls(
        self,
        target_id: int = None,
        hostname_contains: str = None,
        url_contains: str = None,
        content_fetch_status: str = None,
        used_flaresolverr: bool = None,
        status_code: int = None,
        has_forms: bool = None,
        has_links: bool = None,
        has_meta_tags: bool = None,
        has_iframes: bool = None,
        has_comments: bool = None,
        has_findings: bool = None,
        has_endpoints: bool = None,
        has_javascript_files: bool = None,
        has_inline_js: bool = None,
        has_technologies: bool = None,
        has_vulnerabilities: bool = None,
        form_method: str = None,
        form_action_contains: str = None,
        finding_name_contains: str = None,
        endpoint_path_contains: str = None,
        endpoint_param_contains: str = None,
        link_href_contains: str = None,
        iframe_src_contains: str = None,
        comment_contains: str = None,
        meta_tag_contains: str = None,
        technology_name_contains: str = None,
        vulnerability_severity: str = None,
        limit: int = 20
    ) -> str:
        """
        【灵活查询】根据多个条件组合查询 URLResult 记录。
        支持按 Target、Hostname、URL 关键词、状态、以及 URL 底下已发现资产进行筛选。
        例如：用 target_id + has_forms=True 找出目标下所有含 HTML Form 的 URL，
        或用 has_findings=True / has_vulnerabilities=True 找出高价值 URL。
        AutomationAgent 不需要先记住单一 url_id 再逐笔查询。
        避免一次性获取大量不相关的 URL，提高查询效率。
        
        Args:
            target_id: (可选) 筛选指定 Target 下的 URL
            hostname_contains: (可选) 筛选 Hostname 包含特定字符串的 URL
            url_contains: (可选) 筛选 URL 包含特定字符串的记录
            content_fetch_status: (可选) 按抓取状态筛选 (e.g., 'SUCCESS_FETCHED', 'FAILED_BLOCKED')
            used_flaresolverr: (可选) 按是否使用过 Flaresolverr 筛选
            status_code: (可选) 按 HTTP 状态码筛选
            has_forms: (可选) True 只返回有 HTML Form 的 URL；False 只返回没有 Form 的 URL
            has_links: (可选) 筛选是否有 Link 资产
            has_meta_tags: (可选) 筛选是否有 MetaTag 资产
            has_iframes: (可选) 筛选是否有 Iframe 资产
            has_comments: (可选) 筛选是否有 HTML Comment 资产
            has_findings: (可选) 筛选是否有 AnalysisFinding 敏感发现
            has_endpoints: (可选) 筛选是否有关联 Endpoint
            has_javascript_files: (可选) 筛选是否有关联外部 JavaScriptFile
            has_inline_js: (可选) 筛选是否有 ExtractedJS inline block
            has_technologies: (可选) 筛选是否有 TechStack
            has_vulnerabilities: (可选) 筛选是否有关联漏洞
            form_method: (可选) 筛选表单 method (e.g., 'GET', 'POST')，会自动启用 has_forms=True
            form_action_contains: (可选) 筛选 form action 包含特定字符串，会自动启用 has_forms=True
            finding_name_contains: (可选) 筛选 finding pattern_name 包含特定字符串，会自动启用 has_findings=True
            endpoint_path_contains: (可选) 筛选 endpoint path 包含特定字符串，会自动启用 has_endpoints=True
            endpoint_param_contains: (可选) 筛选 endpoint 参数名包含特定字符串，会自动启用 has_endpoints=True
            link_href_contains: (可选) 筛选 link href 包含特定字符串，会自动启用 has_links=True
            iframe_src_contains: (可选) 筛选 iframe src 包含特定字符串，会自动启用 has_iframes=True
            comment_contains: (可选) 筛选 HTML comment 内容包含特定字符串，会自动启用 has_comments=True
            meta_tag_contains: (可选) 筛选 meta tag JSON 属性包含特定字符串，会自动启用 has_meta_tags=True
            technology_name_contains: (可选) 筛选技术名称包含特定字符串，会自动启用 has_technologies=True
            vulnerability_severity: (可选) 筛选漏洞严重度 (info/low/medium/high/critical)，会自动启用 has_vulnerabilities=True
            limit: (可选) 返回结果数量上限，默认 20
        """
        try:
            from apps.core.models.url_assets import URLResult
            from django.db.models import Count, Q
            
            asset_relations = {
                "forms": "forms",
                "links": "links",
                "meta_tags": "meta_tags",
                "iframes": "iframes",
                "comments": "comments",
                "findings": "findings",
                "endpoints": "found_endpoints",
                "javascript_files": "javascript_files",
                "inline_js": "extracted_js_blocks",
                "technologies": "technologies",
                "vulnerabilities": "vulnerabilities",
            }
            asset_flags = {
                "forms": has_forms,
                "links": has_links,
                "meta_tags": has_meta_tags,
                "iframes": has_iframes,
                "comments": has_comments,
                "findings": has_findings,
                "endpoints": has_endpoints,
                "javascript_files": has_javascript_files,
                "inline_js": has_inline_js,
                "technologies": has_technologies,
                "vulnerabilities": has_vulnerabilities,
            }
            annotations = {
                f"{asset_name}_count": Count(relation_name, distinct=True)
                for asset_name, relation_name in asset_relations.items()
            }
            query = URLResult.objects.annotate(**annotations)
            
            # Build filters
            filters = Q()
            if target_id is not None:
                filters &= Q(target_id=target_id)
            if content_fetch_status is not None:
                filters &= Q(content_fetch_status=content_fetch_status)
            if used_flaresolverr is not None:
                filters &= Q(used_flaresolverr=used_flaresolverr)
            if status_code is not None:
                filters &= Q(status_code=status_code)
            
            if hostname_contains is not None:
                filters &= Q(url__icontains=hostname_contains)
            if url_contains is not None:
                filters &= Q(url__icontains=url_contains)

            if form_method is not None or form_action_contains is not None:
                has_forms = True
                asset_flags["forms"] = True
            if finding_name_contains is not None:
                has_findings = True
                asset_flags["findings"] = True
            if endpoint_path_contains is not None:
                has_endpoints = True
                asset_flags["endpoints"] = True
            if endpoint_param_contains is not None:
                has_endpoints = True
                asset_flags["endpoints"] = True
            if link_href_contains is not None:
                has_links = True
                asset_flags["links"] = True
            if iframe_src_contains is not None:
                has_iframes = True
                asset_flags["iframes"] = True
            if comment_contains is not None:
                has_comments = True
                asset_flags["comments"] = True
            if meta_tag_contains is not None:
                has_meta_tags = True
                asset_flags["meta_tags"] = True
            if technology_name_contains is not None:
                has_technologies = True
                asset_flags["technologies"] = True
            if vulnerability_severity is not None:
                has_vulnerabilities = True
                asset_flags["vulnerabilities"] = True

            for asset_name, enabled in asset_flags.items():
                relation_name = asset_relations[asset_name]
                if enabled is True:
                    filters &= Q(**{f"{relation_name}__isnull": False})
                elif enabled is False:
                    filters &= Q(**{f"{relation_name}__isnull": True})

            if form_method is not None:
                filters &= Q(forms__method__iexact=form_method)
            if form_action_contains is not None:
                filters &= Q(forms__action__icontains=form_action_contains)
            if finding_name_contains is not None:
                filters &= Q(findings__pattern_name__icontains=finding_name_contains)
            if endpoint_path_contains is not None:
                filters &= Q(found_endpoints__path__icontains=endpoint_path_contains)
            if endpoint_param_contains is not None:
                filters &= Q(found_endpoints__query_parameters__key__icontains=endpoint_param_contains)
            if link_href_contains is not None:
                filters &= Q(links__href__icontains=link_href_contains)
            if iframe_src_contains is not None:
                filters &= Q(iframes__src__icontains=iframe_src_contains)
            if comment_contains is not None:
                filters &= Q(comments__content__icontains=comment_contains)
            if meta_tag_contains is not None:
                filters &= Q(meta_tags__attributes__icontains=meta_tag_contains)
            if technology_name_contains is not None:
                filters &= Q(technologies__name__icontains=technology_name_contains)
            if vulnerability_severity is not None:
                filters &= Q(vulnerabilities__severity__iexact=vulnerability_severity)
            
            urls = query.filter(filters).distinct().values(
                "id", "url", "used_flaresolverr", "content_fetch_status", 
                "status_code", "target_id", *annotations.keys()
            )[:limit]
            
            if not urls:
                filter_desc = []
                if target_id: filter_desc.append(f"target_id={target_id}")
                if hostname_contains: filter_desc.append(f"hostname_contains='{hostname_contains}'")
                if url_contains: filter_desc.append(f"url_contains='{url_contains}'")
                if content_fetch_status: filter_desc.append(f"status='{content_fetch_status}'")
                if used_flaresolverr is not None: filter_desc.append(f"used_flaresolverr={used_flaresolverr}")
                if status_code: filter_desc.append(f"status_code={status_code}")
                for asset_name, enabled in asset_flags.items():
                    if enabled is not None:
                        filter_desc.append(f"has_{asset_name}={enabled}")
                if form_method: filter_desc.append(f"form_method='{form_method}'")
                if form_action_contains: filter_desc.append(f"form_action_contains='{form_action_contains}'")
                if finding_name_contains: filter_desc.append(f"finding_name_contains='{finding_name_contains}'")
                if endpoint_path_contains: filter_desc.append(f"endpoint_path_contains='{endpoint_path_contains}'")
                if endpoint_param_contains: filter_desc.append(f"endpoint_param_contains='{endpoint_param_contains}'")
                if link_href_contains: filter_desc.append(f"link_href_contains='{link_href_contains}'")
                if iframe_src_contains: filter_desc.append(f"iframe_src_contains='{iframe_src_contains}'")
                if comment_contains: filter_desc.append(f"comment_contains='{comment_contains}'")
                if meta_tag_contains: filter_desc.append(f"meta_tag_contains='{meta_tag_contains}'")
                if technology_name_contains: filter_desc.append(f"technology_name_contains='{technology_name_contains}'")
                if vulnerability_severity: filter_desc.append(f"vulnerability_severity='{vulnerability_severity}'")
                
                filter_str = ", ".join(filter_desc) if filter_desc else "no filters (all URLs)"
                return f"No URLs found with filters: {filter_str}"
            
            summary = f"=== URL Query Results (showing {len(urls)} results) ===\n"
            for u in urls:
                used_fs_str = "Yes" if u["used_flaresolverr"] else "No"
                asset_counts = []
                for asset_name in asset_relations.keys():
                    count = u.get(f"{asset_name}_count", 0)
                    if count:
                        asset_counts.append(f"{asset_name}={count}")
                asset_str = f" | Assets: {', '.join(asset_counts)}" if asset_counts else " | Assets: none"
                summary += f"- URL ID [{u['id']}]: {u['url']} | Fetch: {u['content_fetch_status']} | FS: {used_fs_str} | Status: {u['status_code']}{asset_str}\n"

            if any(enabled is True for enabled in asset_flags.values()):
                summary += "\nTip: Use get_url_intelligence(url_id=<URL ID>) only for the specific URL you want to inspect deeply.\n"
            
            return summary
        except Exception as e:
            logger.error(f"query_urls failed: {e}")
            return f"Error querying URLs: {str(e)}"

    @method_tool
    def escalate_to_orchestrator(self, overview_id: int = None, question: str = "") -> str:
        """
        [Escalation] 當你完全卡住時呼叫此工具向 HackerAssistant (Orchestrator/Layer 2) 請求戰略指導。
        例如：所有已知的繞過手法都失敗、找不到新的攻擊面、或不確定下一步該做什麼。
        系統會自動標記 Overview 為 NEEDS_GUIDANCE，並啟動自動化戰略分析。

        Args:
            overview_id: (Optional) 當前 Overview 的 ID。自動注入。
            question: 你的問題。描述你嘗試了什麼、失敗了什麼、需要什麼方向指引。
                      要詳細 (例如 'SSTI sandbox escape 所有標準繞過都被擋: __class__, __globals__, __builtins__ 全被攔截，還有其他思路嗎？')
        """
        try:
            from apps.core.models import Overview
            from apps.ai_assistant.helpers.use_cases import create_message
            from django.contrib.auth import get_user_model
            from django.utils import timezone

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            overview = Overview.objects.get(id=overview_id)
            if not overview.parent_thread_id:
                return "⚠️ 沒有設定 parent_thread_id，無法向 Orchestrator 求助。請繼續自行嘗試。"

            User = get_user_model()
            system_user = User.objects.filter(is_superuser=True).first()

            create_message(
                assistant_id="hacker_assistant_agent",
                thread_id=overview.parent_thread_id,
                user=system_user,
                content=(
                    f"🤖 **AutomationAgent needs guidance (Overview #{overview_id})**\n\n"
                    f"**Target**: {overview.target.name if overview.target else 'N/A'}\n"
                    f"**Risk Score**: {overview.risk_score}\n"
                    f"**Question**: {question}\n\n"
                    f"---\n"
                    f"System: Review the AutomationAgent's recent steps in Overview #{overview_id} "
                    f"and provide focused strategic guidance. Be specific about what to try next."
                )
            )

            knowledge = overview.knowledge or {}
            knowledge['_escalation'] = {
                'question': question,
                'escalated_at': str(timezone.now()),
            }
            overview.knowledge = knowledge
            overview.status = "NEEDS_GUIDANCE"
            overview.save(update_fields=['status', 'knowledge'])

            return (
                f"✅ 已向 HackerAssistant (parent_thread={overview.parent_thread_id}) 求助！\n"
                f"問題: {question}\n"
                f"Overview #{overview_id} 已標記為 NEEDS_GUIDANCE。\n"
                f"系統正在分析你的情況並提供戰略建議。請稍後呼叫 read_orchestrator_guidance({overview_id}) 查看回覆。"
            )
        except Exception as e:
            logger.error(f"escalate_to_orchestrator failed: {e}")
            return f"求助失敗: {e}"

    @method_tool
    def read_orchestrator_guidance(self, overview_id: int) -> str:
        """
        [Escalation] 在呼叫 escalate_to_orchestrator 求助之後，用此工具查看 HackerAssistant 是否已回覆指導建議。
        如果有新的指導訊息，此工具會回傳其內容。如果還沒有回覆，會提示你等待。

        Args:
            overview_id: 當前 Overview 的 ID。
        """
        try:
            from django.utils import timezone

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            overview = Overview.objects.get(id=overview_id)

            if overview.status == "NEEDS_GUIDANCE":
                # Guidance is delivered to the agent's OWN thread by _handle_guidance_request
                if not overview.thread_id:
                    return "⏳ 尚未建立 Thread，分析可能還在進行中。請稍後再查。"

                from apps.core.models.ai_models import Message as AiMessage
                agent_msgs = AiMessage.objects.filter(
                    thread_id=overview.thread_id
                ).order_by('-created_at')[:10]

                guidance = None
                for msg in agent_msgs:
                    content = (msg.content or "")
                    if "Orchestrator Strategic Guidance" in content:
                        guidance = content
                        break
                    if msg._meta.label == 'ai_assistant.AIMessage' and hasattr(msg, 'response'):
                        continue

                if guidance:
                    overview.status = "EXECUTING"
                    overview.save(update_fields=['status'])
                    return f"📨 **Orchestrator 指導建議**:\n\n{guidance}\n\n---\nOverview 已恢復 EXECUTING 狀態。請根據上述建議繼續行動。"
                else:
                    return (
                        f"⏳ 等待 Orchestrator 回覆中... (Overview #{overview_id} 狀態: NEEDS_GUIDANCE)\n"
                        f"系統自動分析正在進行。請稍後再次呼叫此工具檢查。\n"
                        f"與此同時，你可以嘗試自行尋找替代攻擊路徑。"
                    )

            return f"Overview #{overview_id} 狀態為 {overview.status}，無需等待指導。繼續執行當前任務。"
        except Exception as e:
            logger.error(f"read_orchestrator_guidance failed: {e}")
            return f"讀取指導失敗: {e}"

    @method_tool
    def check_scanned_ips(
        self,
        target_id: int,
        port_count_min: int = None,
        port_count_max: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        檢查某個 Target 底下所有 IP 的掃描狀態與概況（支持分页和过滤，已优化 N+1 查询）。

        在對 IP 使用 Nmap, Naabu 等掃描前，請務必先使用此工具，
        確認該 IP 是否已經被掃描過 (例如 last_scan_type 不為空，或是已有掃出的 ports)。
        避免對同一個 IP 重複執行慢速的端口掃描。

        Args:
            target_id: Target ID
            port_count_min: 最少端口数过滤
            port_count_max: 最多端口数过滤
            limit: 返回数量上限（默认 50，最大 200）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的 IP 扫描状态摘要
        """
        try:
            from apps.core.models.network import IP
            from django.db.models import Count

            # 使用 annotate 避免 N+1 查询
            query = IP.objects.filter(target_id=target_id).annotate(
                port_count=Count('ports')
            )

            # 应用过滤条件
            if port_count_min is not None:
                query = query.filter(port_count__gte=port_count_min)

            if port_count_max is not None:
                query = query.filter(port_count__lte=port_count_max)

            # 限制最大值
            limit = min(limit, 200)

            # 获取总数
            total = query.count()

            if total == 0:
                return f"No IPs found for Target ID {target_id} with the given filters."

            # 获取分页数据
            ips = query.values(
                'id', 'address', 'last_scan_type', 'port_count'
            ).order_by('-port_count', '-created_at')[offset:offset+limit]

            summary = f"IP Scan Status (showing {len(ips)}/{total}):\n"
            summary += f"Filters: port_count_min={port_count_min}, port_count_max={port_count_max}\n\n"

            for ip in ips:
                summary += f"[{ip['id']}] {ip['address']}\n"
                summary += f"  Ports: {ip['port_count']}, Last Scan: {ip['last_scan_type']}\n\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} IPs\n"

            return summary
        except Exception as e:
            return f"Error checking scanned IPs: {str(e)}"
