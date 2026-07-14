import logging
from apps.ai_assistant import method_tool
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class ReconnaissanceMixin:
    """
    Reconnaissance & Context Tools Mixin
    Provides tools for querying target context, managing overviews, and checking scan status.
    """

    def _resolve_target_id_from_overview(self, overview_id):
        """從 overview_id 解析 target_id，兼容直接傳 target_id 的舊用法。"""
        if not overview_id:
            overview_id = getattr(self, '_agent_overview_id', None)
        if not overview_id:
            return None, "Error: overview_id 未提供且 session 未綁定。請先呼叫 get_target_context 或 bind_to_target。"
        try:
            from apps.core.models import Overview
            overview = Overview.objects.get(id=overview_id)
            return overview.target_id, None
        except Overview.DoesNotExist:
            from apps.core.models import Target
            if Target.objects.filter(id=overview_id).exists():
                return overview_id, None
            return None, f"Error: Overview ID {overview_id} 不存在。"

    def _build_plan_info(self, target) -> str:
        """從 DB 查詢 AttackPlan + Action + WalkCursor 狀態，組成 context 字串。"""
        try:
            from apps.core.models import AttackPlan, WalkCursor, AssetLock

            plan = AttackPlan.objects.filter(
                target_id=target.id, status="ACTIVE"
            ).first()
            if not plan:
                plan = AttackPlan.objects.filter(
                    target_id=target.id, status="DRAFT"
                ).order_by("-created_at").first()

            if not plan:
                return (
                    "Attack Plan: (無活躍計劃) — 請用 create_attack_plan 建立新計劃。\n"
                    "Attack Actions: (無)"
                )

            lines = [f"Attack Plan#{plan.id} [{plan.status}]: {plan.objective}"]

            actions = plan.actions.prefetch_related("asset_links").order_by("order", "created_at")
            if actions.exists():
                action_lines = []
                for act in actions:
                    assets_str = []
                    for link in act.asset_links.all():
                        for fk in ("ip_asset_id", "subdomain_asset_id", "url_asset_id",
                                   "endpoint_asset_id", "port_asset_id"):
                            val = getattr(link, fk, None)
                            if val:
                                assets_str.append(f"{link.asset_type}#{val}")
                                break
                    action_lines.append(
                        f"  [{act.status:>11}] Action#{act.id} order={act.order}: "
                        f"{(act.purpose_text or '(無目的)')[:80]} | "
                        f"Assets: {', '.join(assets_str) or '(無)'}"
                    )
                lines.append(f"Attack Actions ({actions.count()}):\n" + "\n".join(action_lines))
            else:
                lines.append("Attack Actions: (無 — 請用 add_action 加入行動)")

            try:
                cursor = plan.walk_cursor
                if cursor.current_asset_link_id:
                    lines.append(f"WalkCursor: at AssetVectorLink#{cursor.current_asset_link_id}")
                else:
                    lines.append("WalkCursor: 初始位置（尚未走訪）")
            except WalkCursor.DoesNotExist:
                lines.append("WalkCursor: (未建立 — 計劃尚未激活)")

            active_locks = AssetLock.objects.filter(target_id=target.id, lock_status="HELD")
            if active_locks.exists():
                lock_strs = [f"{l.asset_type} by Thread#{l.thread_id}" for l in active_locks]
                lines.append(f"AssetLocks (HELD): {', '.join(lock_strs)}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"_build_plan_info failed: {e}")
            return f"Attack Plan: (查詢失敗: {e})"

    @method_tool
    def get_target_context(self, target_name: str) -> str:
        """
        【必須第一個呼叫】在進行任何操作前，先用此工具查詢目標的所有有效 ID。
        返回：active overview_id、target_id、subdomain IDs、IP IDs、seed IDs、URL result IDs。
        嚴禁在沒有呼叫此工具的情況下自行猜測或假設任何 ID。

        系統支援語意查詢，可傳入下列任一形式，會自動多層級匹配：
          1. 目標完整名稱（e.g. 'vuln-f9wi.onrender.com'）
          2. 完整網域 / 部分字串（e.g. 'vuln-f9wi' 或 'onrender.com'）
          3. 子域名（會反查所屬 Target）
          4. 種子值（Seed.value，會反查所屬 Target）
          5. URL（會反查其 host 所屬 Target）
        若查無結果，會回傳所有現存目標清單供你挑選正確名稱。

        Args:
            target_name: 目標名稱、域名、子域名、種子值或 URL（系統會自動語意匹配）。
        """
        try:
            from apps.core.models import Target, Overview, Subdomain, IP, Seed
            from apps.core.models.url_assets import URLResult
            from django.utils import timezone
            
            now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')

            # ════════════════════════════════════════════════════════════════
            # 語意查詢：多層級匹配，避免要求 Agent 記憶精確格式
            # 順序：精確名稱 → 完整子串 → 種子值反查 → 子域名反查 → URL host 反查
            # ════════════════════════════════════════════════════════════════
            target = Target.objects.filter(name=target_name).first()

            if not target:
                # 完整子串模糊（使用完整 target_name，而非只取第一段標籤）
                target = Target.objects.filter(name__icontains=target_name).first()

            if not target:
                # 反查種子值（Seed.value）
                from apps.core.models import Seed as _Seed
                seed_match = _Seed.objects.filter(value__icontains=target_name).first()
                if seed_match and seed_match.target_id:
                    target = Target.objects.filter(id=seed_match.target_id).first()

            if not target:
                # 反查子域名
                from apps.core.models import Subdomain as _Subdomain
                sub_match = _Subdomain.objects.filter(name__icontains=target_name).first()
                if sub_match and sub_match.target_id:
                    target = Target.objects.filter(id=sub_match.target_id).first()

            if not target:
                # 反查 URL（host 部分）
                from apps.core.models.url_assets import URLResult as _URLResult
                url_match = _URLResult.objects.filter(url__icontains=target_name).first()
                if url_match and url_match.target_id:
                    target = Target.objects.filter(id=url_match.target_id).first()

            if not target:
                # 最終 fallback：列出所有目標
                all_targets = list(Target.objects.values("id", "name"))
                if all_targets:
                    return (
                        f"找不到目標 '{target_name}'。\n"
                        f"已嘗試：精確名稱、子字串、Seed 反查、子域名反查、URL host 反查。\n"
                        f"現有目標清單：{all_targets}\n"
                        f"請從上述清單挑選正確的 target_name（可使用 id 對應的 name 或其部分字串）重新呼叫。"
                    )
                return (
                    f"找不到目標 '{target_name}'，且系統目前沒有任何目標。"
                    f"請先透過 /api/targets/ 建立目標後再呼叫。"
                )

            active_overview = getattr(target, 'overview', None)

            # 若無 Overview（1:1 關係下 target.overview 為 None），嘗試建立
            if not active_overview:
                active_overview = Overview.objects.create(
                    target=target,
                    status="PLANNING",
                    risk_score=50,
                    plan={"steps": []},
                )
                logger.info(f"[get_target_context] Auto-created Overview for Target {target.name} (1:1 relation)")

            subdomains = list(Subdomain.objects.filter(target=target).values("id", "name")[:15])
            ips = list(IP.objects.filter(target=target).values("id", "address")[:15])
            seeds = list(Seed.objects.filter(target=target).values("id", "type", "value")[:10])
            urls = list(URLResult.objects.filter(target=target).values("id", "url")[:15])

            # active_overview 必不為 None（1:1 關係下，若無則已建立）

            # ════════════════════════════════════════════════════════════════
            # Auto-bind thread_id / parent_thread_id
            # 多層 fallback 鏈（避免 Overview 孤兒——前端 graph / 樹狀結構完全依賴此關聯）：
            #   thread_id：_current_invoke_thread_id → _thread.id → 命名慣例反查
            #   parent_thread_id：_caller_thread_id
            # ════════════════════════════════════════════════════════════════
            if not active_overview.thread_id or not active_overview.parent_thread_id:
                update_fields = []
                # 1. 解析自身 thread_id（優先 instance 屬性，再反查子執行緒）
                if not active_overview.thread_id:
                    resolved_tid = getattr(self, '_current_invoke_thread_id', None)
                    if not resolved_tid:
                        _thread_obj = getattr(self, '_thread', None)
                        if _thread_obj and getattr(_thread_obj, 'id', None):
                            resolved_tid = _thread_obj.id
                    if not resolved_tid:
                        _caller_id = getattr(self, '_caller_thread_id', None)
                        if _caller_id:
                            from apps.core.models.ai_models import Thread
                            sub_thread = Thread.objects.filter(
                                name=f"subagent_automation_agent_for_thread_{_caller_id}"
                            ).first()
                            if sub_thread:
                                resolved_tid = sub_thread.id
                    if resolved_tid:
                        active_overview.thread_id = resolved_tid
                        update_fields.append('thread_id')

                # 2. Bind parent_thread_id (caller)
                if not active_overview.parent_thread_id:
                    _caller_id = getattr(self, '_caller_thread_id', None)
                    if _caller_id:
                        active_overview.parent_thread_id = _caller_id
                        update_fields.append('parent_thread_id')

                if update_fields:
                    active_overview.save(update_fields=update_fields)
                    logger.info(f"[get_target_context] Auto-bound overview {active_overview.id} fields: {update_fields}")
            if not getattr(self, '_agent_overview_id', None):
                self._agent_overview_id = active_overview.id
            # 同步 thread_id, bound_overview_id 到 agent instance（供 wrapper fallback 注入使用）
            # 確保 as_graph() 的 wrapped tools 可以從 _thread.bound_overview_id 取得正確 ID
            if active_overview.thread_id and not getattr(self, '_current_invoke_thread_id', None):
                self._current_invoke_thread_id = active_overview.thread_id
            # 設定 _thread.bound_overview_id（wrapper fallback 路徑依賴此值）
            _th = getattr(self, '_thread', None)
            if _th is not None:
                # bound_overview_id 是 ForeignKey(Overview)，比較 DB 底層 ID
                cur_id = getattr(_th, 'bound_overview_id_id', None) or (
                    getattr(_th, 'bound_overview_id', None) and getattr(_th.bound_overview_id, 'id', None)
                )
                if cur_id != active_overview.id:
                    from apps.core.models.ai_models import Thread
                    Thread.objects.filter(id=_th.id).update(bound_overview_id=active_overview.id)
                    _th.bound_overview_id = active_overview

            is_completed = active_overview.status == "COMPLETED"
            context_prefix = "RECENTLY COMPLETED" if is_completed else "ACTIVE"

            executions_info = ""
            thread_ids = [value for value in [active_overview.thread_id, active_overview.parent_thread_id] if value]
            if thread_ids:
                from apps.core.models import ExecutionGraph

                executions = list(
                    ExecutionGraph.objects.filter(thread_id__in=thread_ids)
                    .prefetch_related("nodes")
                    .order_by("-started_at")[:5]
                )
            else:
                executions = []
            if executions:
                lines = []
                for graph in executions:
                    node_summary = ", ".join(
                        f"{node.name}:{node.status}" for node in graph.nodes.order_by("sequence")[:5]
                    )
                    lines.append(
                        f"- ExecutionGraph[{graph.id}] Status:{graph.status} | "
                        f"Title:{graph.title or graph.assistant_id} | Nodes:{node_summary or 'None'}"
                    )
                executions_info = "\n  " + "\n  ".join(lines)
            else:
                executions_info = "\n  No ExecutionGraphs created yet."

            bound_ips = list(active_overview.ips.values("id", "address")[:20])
            bound_subdomains = list(active_overview.subdomains.values("id", "name")[:20])
            bound_urls = list(active_overview.url_results.values("id", "url")[:20])
            bound_asset_counts = {
                "ips": active_overview.ips.count(),
                "subdomains": active_overview.subdomains.count(),
                "urls": active_overview.url_results.count(),
            }

            # ── AttackPlan 狀態（取代舊 overview.plan JSON）──────────────
            plan_info = self._build_plan_info(target)

            return (
                f"=== TARGET CONTEXT ===\n"
                f"Current System Time: {now_str}\n"
                f"Target Name: {target.name}\n"
                f"Target ID: {target.id}\n"
                f"{context_prefix} Overview: ✓ ACTIVE (ID 已自動綁定到本 session，後續工具呼叫無需提供 overview_id)\n"
                f"Overview Status: {active_overview.status}\n"
                f"Thread Relationship: ✓ AUTO-MANAGED (parent/own thread IDs 已由後端綁定，無需手動傳遞)\n"
                f"Overview Knowledge: {active_overview.knowledge}\n"
                f"{plan_info}\n"
                f"Overview Active Executions:{executions_info}\n"
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
    def create_overview(self, target_id: int) -> str:
        """
        為沒有 Active Overview 的 Target 建立一個全新的 Overview。
        注意：若目標已存在 PLANNING/EXECUTING 的 Overview，此工具會直接回傳現有的，不會重複建立。
        建立後，請務必重新呼叫 get_target_context 來獲取新的 overview_id。

        thread_id 與 parent_thread_id 由後端根據 agent instance 自動綁定，
        無需（也不應）由呼叫端提供，以避免外鍵約束錯誤與關係混亂。

        Args:
            target_id: Target ID
        """
        try:
            from apps.core.models import Target, Overview
            from django.db import transaction
            from apps.core.models.ai_models import Thread
            target = Target.objects.get(id=target_id)

            # ══════════════════════════════════════════════════════════════
            # thread_id / parent_thread_id 完全由 agent instance 推導（問題 ③），
            # 多層 fallback 鏈確保 Overview 不會成為孤兒（前端 graph / 樹狀結構依賴此關聯）：
            #   thread_id：_current_invoke_thread_id → _thread.id → 命名慣例反查
            #   parent_thread_id：_caller_thread_id
            # ══════════════════════════════════════════════════════════════
            thread_id = getattr(self, '_current_invoke_thread_id', None)
            if not thread_id:
                _thread_obj = getattr(self, '_thread', None)
                if _thread_obj and getattr(_thread_obj, 'id', None):
                    thread_id = _thread_obj.id
            parent_thread_id = getattr(self, '_caller_thread_id', None) or None

            # 若自身 thread_id 仍為空但存在 caller，嘗試以命名慣例反查子執行緒
            _caller_id = parent_thread_id
            if _caller_id and not thread_id:
                sub_thread = Thread.objects.filter(
                    name=f"subagent_automation_agent_for_thread_{_caller_id}"
                ).first()
                if sub_thread:
                    thread_id = sub_thread.id

            # ⚠️ Idempotency 保護（1:1 關係下大幅簡化）：target 已有 overview 則直接復用
            with transaction.atomic():
                overview, created = Overview.objects.get_or_create(
                    target=target,
                    defaults={
                        "status": "PLANNING",
                        "risk_score": 50,
                        "plan": {"steps": []},
                        "thread_id": thread_id,
                        "parent_thread_id": parent_thread_id,
                    },
                )
                if not created:
                    # 復用既有 Overview，必要時補上 thread 關聯
                    changed = False
                    if _caller_id and not overview.parent_thread_id and not parent_thread_id:
                        overview.parent_thread_id = _caller_id
                        changed = True
                    if not getattr(self, '_agent_overview_id', None):
                        self._agent_overview_id = overview.id
                    if changed:
                        overview.save(update_fields=['parent_thread_id'])
                    logger.warning(
                        f"create_overview called but overview already exists "
                        f"(Overview#{overview.id}) for Target {target.name}. Returning existing."
                    )
                    return (
                        f"⚠️ Target {target.name} (ID: {target.id}) 已有 Overview (ID: {overview.id}, "
                        f"Status: {overview.status})。無需重複建立，請直接使用此 overview_id={overview.id}。"
                        f"請重新呼叫 get_target_context 確認。"
                    )

            if not getattr(self, '_agent_overview_id', None):
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

        路由優先序：
        1. SubAgentDispatch（直屬派發者，通常是 AutomationAgent）— 最準確
        2. Overview.parent_thread_id（fallback，可能指向 HackerAssistant）

        Args:
            overview_id: (Optional) 當前 Overview 的 ID。自動注入。
            message: 要傳回給上層 Agent 的消息內容。
        """
        try:
            from apps.core.models import Overview, SubAgentDispatch
            from apps.core.models.ai_models import Thread as AIThread
            from apps.core.models import Message as DjangoMessage
            from langchain_core.messages import HumanMessage, message_to_dict
            from django.utils import timezone

            overview = Overview.objects.get(id=overview_id)

            # ════════════════════════════════════════════════════════════════
            # 路由優先序 1: SubAgentDispatch（直屬派發者）
            # 透過當前 agent 的 _thread 反查誰派發了這個子代理任務
            # ════════════════════════════════════════════════════════════════
            current_thread = getattr(self, '_thread', None)
            current_thread_id = getattr(current_thread, 'id', None) if current_thread else None

            dispatch = None
            if current_thread_id:
                dispatch = SubAgentDispatch.objects.filter(
                    sub_thread_id=current_thread_id,
                    status="RUNNING",
                ).order_by("-dispatched_at").first()

            if dispatch:
                # 更新 dispatch 狀態 + 摘要
                dispatch.status = "COMPLETED"
                dispatch.result_summary = message[:2000]
                dispatch.completed_at = timezone.now()
                dispatch.save(update_fields=["status", "result_summary", "completed_at"])

                target_thread_id = dispatch.dispatcher_thread_id
                route_note = "（透過 SubAgentDispatch 路由到直屬派發者）"
            else:
                # ════════════════════════════════════════════════════════════════
                # 路由優先序 2: Overview.parent_thread_id（fallback）
                # ════════════════════════════════════════════════════════════════
                target_thread_id = overview.parent_thread_id
                route_note = "（透過 Overview.parent_thread_id fallback）"

            if not target_thread_id:
                return "此任務沒有關聯的派發者 Thread（無 SubAgentDispatch 且 Overview 無 parent_thread_id），訊息已記錄但未發送。"

            parent_thread = AIThread.objects.get(id=target_thread_id)

            # 直接注入訊息到父層 Thread
            notification = HumanMessage(
                content=f"[SYSTEM: Layer 3 Async Completion Report For Overview {overview_id}]\n{message}"
            )
            DjangoMessage.objects.create(
                thread=parent_thread,
                role="human",
                message=message_to_dict(notification),
            )

            # 統一喚醒機制：寫完 message 後觸發 wake_agent_on_scan_completion
            # 讓 parent agent 被喚醒繼續消化子代理回報
            try:
                from apps.auto.tasks import wake_agent_on_scan_completion
                wake_agent_on_scan_completion.delay(thread_id=target_thread_id)
            except Exception as wake_err:
                logger.warning(
                    f"notify_caller_agent: wake trigger failed for thread={target_thread_id}: {wake_err}"
                )

            return f"成功回調通知 Parent Thread {target_thread_id} {route_note}。"
        except Exception as e:
            logger.error(f"Failed to notify caller agent for overview {overview_id}: {e}")
            return f"通知 Caller Agent 失敗: {e}"

    @method_tool
    def check_scanned_urls(
        self,
        target_id: int,
        fetch_status_filter: str = None,
        tech_analyzed_filter: bool = None,
        vuln_scanned_filter: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        檢查某個 Target 底下所有 URL 的抓取紀錄與狀態（支持分页和过滤）。

        在執行任何 Flaresolverr 爬蟲、Katana 掃描或其他 URL 掃描與抽取前，請務必先使用此工具，
        以確認該 URL 是否已經被抓取過 (例如 content_fetch_status='SUCCESS_FETCHED')，
        或是否已用過 Flaresolverr (used_flaresolverr=True)。
        防止重複執行無意義的掃描造成系統負載。

        漏洞掃描狀態由 vulnerabilities 關聯記錄的數量推導（vuln_count>0 代表已掃出漏洞），
        URLResult 本身沒有 is_vuln_scanned 布林欄位。

        Args:
            target_id: Target ID
            fetch_status_filter: 按 content_fetch_status 过滤 ('SUCCESS_FETCHED', 'FAILED_BLOCKED', 'PENDING' 等)
            tech_analyzed_filter: 按 is_tech_analyzed 过滤 (True/False/None)
            vuln_scanned_filter: 按漏洞記錄過濾；True=只看已有漏洞記錄的 URL，False=只看尚無漏洞記錄的 URL，None=不過濾
            limit: 返回数量上限（默认 50，最大 200）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的 URL 扫描状态摘要
        """
        try:
            from apps.core.models.url_assets import URLResult
            from django.db.models import Count

            query = URLResult.objects.filter(target_id=target_id).annotate(
                vuln_count=Count("vulnerabilities", distinct=True)
            )

            # 应用过滤条件
            if fetch_status_filter:
                query = query.filter(content_fetch_status=fetch_status_filter)

            if tech_analyzed_filter is not None:
                query = query.filter(is_tech_analyzed=tech_analyzed_filter)

            if vuln_scanned_filter is True:
                query = query.filter(vuln_count__gt=0)
            elif vuln_scanned_filter is False:
                query = query.filter(vuln_count=0)

            # 限制最大值
            limit = min(limit, 200)

            # 获取总数
            total = query.count()

            if total == 0:
                return f"No URLs found for Target ID {target_id} with the given filters."

            # 获取分页数据
            urls = query.values(
                "id", "url", "used_flaresolverr", "content_fetch_status",
                "status_code", "is_tech_analyzed", "vuln_count"
            ).order_by('-created_at')[offset:offset+limit]

            summary = f"URL Scan Status (showing {len(urls)}/{total}):\n"
            summary += f"Filters: fetch_status={fetch_status_filter}, tech_analyzed={tech_analyzed_filter}, vuln_scanned={vuln_scanned_filter}\n\n"

            for u in urls:
                used_fs_str = "Yes" if u["used_flaresolverr"] else "No"
                summary += f"[{u['id']}] {u['url']}\n"
                summary += f"  Status: {u['content_fetch_status']} (HTTP {u['status_code']})\n"
                summary += f"  FlareSolverr: {used_fs_str}\n"
                summary += f"  Tech Analyzed: {u['is_tech_analyzed']}, Vuln Records: {u['vuln_count']}\n\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} URLs\n"

            return summary
        except Exception as e:
            return f"Error checking scanned URLs: {str(e)}"

    @method_tool
    def check_scanned_subdomains(
        self,
        overview_id: int = None,
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
            overview_id: (自動注入) 當前 Overview ID。系統會自動解析對應的 target_id。
            resolvable_filter: 按 is_resolvable 过滤 (True/False/None)
            tech_analyzed_filter: 按 is_tech_analyzed 过滤 (True/False/None)
            limit: 返回数量上限（默认 50，最大 200）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的子域名扫描状态摘要
        """
        try:
            from apps.core.models.domain import Subdomain

            target_id, err = self._resolve_target_id_from_overview(overview_id)
            if err:
                return err

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
        overview_id: int = None,
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
        【批量篩選工具】根據多個條件組合查詢 URLResult 記錄，適合「先找到候選 URL 清單」。
        找到目標後，再用 get_url_intelligence(url_id=X) 對單個 URL 做深度情報讀取。

        ═══ 使用場景 ═══
        - 想找「有 Form 的 URL」: has_forms=True
        - 想找「URL 路徑含 /admin」: url_contains='/admin'
        - 想找「hostname 含 api.example.com」: hostname_contains='api.example'
        - 想知道哪些 URL 有漏洞: has_vulnerabilities=True
        - 想過濾尚未抓取的: content_fetch_status='PENDING'

        ═══ 分頁 (Pagination) ═══
        當目標有大量 URL 時，limit 預設 20。
        若結果顯示尚有更多，請遞增 offset 翻頁：
          第 1 頁: limit=20, offset=0
          第 2 頁: limit=20, offset=20
          第 3 頁: limit=20, offset=40
        不要一次 limit=1000 拉所有資料，浪費 context token。

        ═══ 子字串匹配 (Substring Match) ═══
        url_contains 和 hostname_contains 都是「包含」匹配（icontains），不是完整 URL 匹配：
          url_contains='/login'  → 匹配所有含 /login 的 URL（/login, /login/, /api/login 等）
          hostname_contains='api' → 匹配 api.example.com、myapi.net 等
        當你想找「某個路徑下的 URL」時，用 url_contains 即可，不必猜完整 URL。

        ═══ 查無結果時的處理 ═══
        若 url_contains 或 hostname_contains 查無結果，代表該 URL 尚未被系統爬取。
        系統會自動暗示應使用哪個爬蟲工具觸發掃描，無需 AI 手動發起兩次請求。

        Args:
            overview_id: (自動注入) 當前 Overview ID。系統會自動解析對應的 target_id。
            hostname_contains: (可選) 篩選 hostname 包含特定字串（子字串匹配，非完整匹配）
            url_contains: (可選) 篩選 URL 路徑包含特定字串（子字串匹配）
            content_fetch_status: (可選) 按抓取狀態篩選 ('SUCCESS_FETCHED', 'FAILED_BLOCKED', 'PENDING')
            used_flaresolverr: (可選) 是否已用過 Flaresolverr
            status_code: (可選) HTTP 狀態碼
            has_forms: True=只有 Form 的 URL；False=沒有 Form 的
            has_links: 是否有 Link 資產
            has_meta_tags: 是否有 MetaTag
            has_iframes: 是否有 Iframe
            has_comments: 是否有 HTML Comment
            has_findings: 是否有 AnalysisFinding 敏感發現
            has_endpoints: 是否有關聯 Endpoint
            has_javascript_files: 是否有外部 JavaScriptFile
            has_inline_js: 是否有 ExtractedJS inline block
            has_technologies: 是否有 TechStack
            has_vulnerabilities: 是否有關聯漏洞
            form_method: 篩選 form method ('GET','POST')，自動啟用 has_forms=True
            form_action_contains: 篩選 form action 包含字串，自動啟用 has_forms=True
            finding_name_contains: 篩選 finding pattern_name，自動啟用 has_findings=True
            endpoint_path_contains: 篩選 endpoint path，自動啟用 has_endpoints=True
            endpoint_param_contains: 篩選 endpoint 參數名，自動啟用 has_endpoints=True
            link_href_contains: 篩選 link href，自動啟用 has_links=True
            iframe_src_contains: 篩選 iframe src，自動啟用 has_iframes=True
            comment_contains: 篩選 HTML comment 內容，自動啟用 has_comments=True
            meta_tag_contains: 篩選 meta tag JSON 屬性，自動啟用 has_meta_tags=True
            technology_name_contains: 篩選技術名稱，自動啟用 has_technologies=True
            vulnerability_severity: 篩選漏洞嚴重度 (info/low/medium/high/critical)，自動啟用 has_vulnerabilities=True
            limit: 每頁返回數量（預設 20，建議不超過 50）
        """
        try:
            from apps.core.models.url_assets import URLResult
            from django.db.models import Count, Q

            target_id, err = self._resolve_target_id_from_overview(overview_id)
            if err:
                return err

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

                # ═══ Intent-to-Scan Hint ═══
                # 當 url_contains / hostname_contains 查無結果，代表該 URL 尚未被系統爬取。
                # 明確告知 AI 應觸發爬蟲，省去 AI 判斷步驟。
                scan_hint = ""
                if url_contains or hostname_contains:
                    target_hint = url_contains or hostname_contains
                    scan_hint = (
                        f"\n💡 INTENT-TO-SCAN: No crawl history found for '{target_hint}'. "
                        f"This URL has not been fetched yet. "
                        f"Use run_flaresolverr_crawler(target_url='https://{target_hint}') to crawl it, "
                        f"or run_katana_crawl(subdomain_name='{target_hint}') for full site discovery. "
                        f"Do NOT call query_urls again with the same filter — trigger the scan instead."
                    )

                return f"No URLs found with filters: {filter_str}{scan_hint}"
            
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
            from apps.core.models.ai_models import Thread as AIThread
            from apps.core.models import Message as DjangoMessage
            from langchain_core.messages import HumanMessage, message_to_dict
            from django.contrib.auth import get_user_model
            from django.utils import timezone

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            overview = Overview.objects.get(id=overview_id)
            if not overview.parent_thread_id:
                return "⚠️ 沒有設定 parent_thread_id，無法向 Orchestrator 求助。請繼續自行嘗試。"

            # 直接將求助訊息注入到父層 Thread，不觸發 LLM 避免無限迴圈
            try:
                parent_thread = AIThread.objects.get(id=overview.parent_thread_id)
                notification = HumanMessage(
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
                DjangoMessage.objects.create(
                    thread=parent_thread,
                    role="human",
                    message=message_to_dict(notification),
                )
            except Exception as notify_err:
                logger.error(f"escalate_to_orchestrator: failed to inject notification into parent thread: {notify_err}")

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
    def read_orchestrator_guidance(self, overview_id: int = None) -> str:
        """
        [Escalation] 在呼叫 escalate_to_orchestrator 求助之後，用此工具查看 HackerAssistant 是否已回覆指導建議。
        如果有新的指導訊息，此工具會回傳其內容。如果還沒有回覆，會提示你等待。

        Args:
            overview_id: (Optional) 當前 Overview 的 ID。自動注入。
        """
        try:
            from django.utils import timezone

            if not overview_id:
                return "Error: overview_id 未提供且 session 未綁定。請先呼叫 get_target_context 或 bind_to_target。"
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
                    # Message 模型以 JSONField `message` 儲存 LangChain 訊息，需從中萃取文字內容
                    msg_data = msg.message if isinstance(msg.message, dict) else {}
                    content = (
                        msg_data.get('data', {}).get('content')
                        or msg_data.get('content')
                        or ""
                    )
                    if "Orchestrator Strategic Guidance" in content:
                        guidance = content
                        break

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
        overview_id: int = None,
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
            overview_id: (自動注入) 當前 Overview ID。系統會自動解析對應的 target_id。
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

            target_id, err = self._resolve_target_id_from_overview(overview_id)
            if err:
                return err

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

            # 获取分页数据（IP 模型無 created_at 欄位，改以 last_scan_type 排序）
            ips = query.values(
                'id', 'address', 'last_scan_type', 'port_count'
            ).order_by('-port_count', '-last_scan_type')[offset:offset+limit]

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

    # ════════════════════════════════════════════════════════════════
    # Overview 分頁情報工具（1:1 後 Overview 是 Target 唯一情報中樞）
    # ════════════════════════════════════════════════════════════════

    @method_tool
    def write_overview_page(
        self,
        section_type: str,
        title: str,
        content: str,
        summary: str = "",
        overview_id: int = None,
    ) -> str:
        """
        [Overview Intel] 將情報寫入 Overview 的分區頁面（OverviewPage）。

        每個 Target 只有一個 Overview（1:1），但情報依語義分區儲存：
        - RECON_SUMMARY / SUBDOMAIN_INTEL / PORT_SERVICE / URL_ENDPOINT
        - VULNERABILITY / ATTACK_VECTOR / TECH_STACK / STRATEGIC_PLAN / FREEFORM

        當內容超過 12000 字元時，系統自動用 LLM 生成 page_breakdown 結構化分頁。

        Args:
            section_type: 分區類型（見上述 choices）
            title: 此頁標題
            content: 完整內容（大篇幅情報）
            summary: 簡短摘要（agent 快速瀏覽用）
            overview_id: Overview ID（自動注入）
        """
        try:
            from apps.core.models import OverviewPage
            from apps.core.services.pagination import maybe_generate_page_breakdown
            from django.utils import timezone

            resolved_ov = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov:
                return "無 overview_id 可寫入（session 尚未綁定到 Overview）。"

            valid_sections = {
                "RECON_SUMMARY", "SUBDOMAIN_INTEL", "PORT_SERVICE", "URL_ENDPOINT",
                "VULNERABILITY", "ATTACK_VECTOR", "TECH_STACK", "STRATEGIC_PLAN", "FREEFORM",
            }
            if section_type not in valid_sections:
                return f"無效 section_type。有效值: {sorted(valid_sections)}"

            # 大篇幅內容自動生成分頁
            page_breakdown = None
            if len(content) > 12000:
                try:
                    page_breakdown = maybe_generate_page_breakdown(content)
                except Exception as e:
                    logger.warning(f"[write_overview_page] page_breakdown failed: {e}")

            source_agent = getattr(self, 'id', 'unknown')

            page, created = OverviewPage.objects.update_or_create(
                overview_id=resolved_ov,
                section_type=section_type,
                defaults={
                    "title": title,
                    "content": content,
                    "summary": summary,
                    "page_breakdown": page_breakdown,
                    "source_agent": source_agent,
                },
            )
            action = "Created" if created else "Updated"
            extra = f" (auto-generated {len(page_breakdown)} pages)" if page_breakdown else ""
            return (
                f"✅ {action} OverviewPage #{page.id} [{section_type}] for Overview#{resolved_ov}{extra}.\n"
                f"Title: {title}\nContent length: {len(content)} chars\n"
                f"Use read_overview_page(section_type='{section_type}') to read."
            )
        except Exception as e:
            logger.error(f"[write_overview_page] failed: {e}")
            return f"寫入 OverviewPage 失敗: {e}"

    @method_tool
    def read_overview_page(
        self,
        section_type: str = None,
        page: int = None,
        overview_id: int = None,
    ) -> str:
        """
        [Overview Intel] 讀取 Overview 的分區頁面（OverviewPage）。

        三種讀取模式：
        1. 不指定 section_type → 列出所有分區摘要
        2. 指定 section_type 但不指定 page → 顯示該分區 summary + （若有分頁）頁面列表
        3. 指定 section_type + page → 顯示該分區的第 N 頁內容

        Args:
            section_type: 分區類型（不指定則列出所有）
            page: 頁碼（僅當該分區有 page_breakdown 時有效）
            overview_id: Overview ID（自動注入）
        """
        try:
            from apps.core.models import OverviewPage
            from apps.core.services.pagination import read_page, list_pages_overview

            resolved_ov = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov:
                return "無 overview_id 可讀取（session 尚未綁定到 Overview）。"

            # 模式 1:列出所有分區
            if not section_type:
                pages_qs = OverviewPage.objects.filter(overview_id=resolved_ov).order_by("section_type")
                if not pages_qs.exists():
                    return f"Overview#{resolved_ov} 目前沒有任何分區頁面。"
                lines = [f"=== Overview#{resolved_ov} Intel Sections ({pages_qs.count()}) ==="]
                for p in pages_qs:
                    page_count = len(p.page_breakdown) if p.page_breakdown else 0
                    page_hint = f", {page_count} pages" if page_count else ""
                    lines.append(
                        f"- [{p.section_type}] {p.title} ({len(p.content)} chars{page_hint})\n"
                        f"  Summary: {(p.summary or '(無)')[:150]}\n"
                        f"  Updated: {p.updated_at.strftime('%Y-%m-%d %H:%M')} by {p.source_agent}"
                    )
                return "\n".join(lines)

            # 模式 2/3:讀取特定分區
            try:
                p = OverviewPage.objects.get(overview_id=resolved_ov, section_type=section_type)
            except OverviewPage.DoesNotExist:
                return f"Overview#{resolved_ov} 沒有 [{section_type}] 分區頁面。"

            # 模式 3:讀取特定頁
            if page is not None and p.page_breakdown:
                return read_page(p.page_breakdown, page, blob_id=p.id)

            # 模式 2:顯示分區摘要 + 內容
            result = (
                f"=== OverviewPage #{p.id} [{p.section_type}] ===\n"
                f"Title: {p.title}\n"
                f"Summary: {p.summary or '(無)'}\n"
            )
            if p.page_breakdown:
                result += f"\n{list_pages_overview(p.page_breakdown)}\n"
                result += f"\n💡 Use read_overview_page(section_type='{section_type}', page=N) to read specific page."
            else:
                result += f"\n=== Content ({len(p.content)} chars) ===\n{p.content}"
            return result
        except Exception as e:
            logger.error(f"[read_overview_page] failed: {e}")
            return f"讀取 OverviewPage 失敗: {e}"
