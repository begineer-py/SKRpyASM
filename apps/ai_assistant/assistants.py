from apps.ai_assistant import AIAssistant, method_tool
from apps.ai_assistant.prompts import AgentSpec, TaskDefinition
from apps.core.llms import get_llm_instance
from apps.auto.tools.memory_tools import MemoryMixin
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.cve_intelligence_tools import CVEIntelligenceMixin
from apps.auto.tools.step_management_tools import StepManagementMixin
from apps.auto.tools.skill_tools import SkillMixin
from langchain_community.tools import (
    DuckDuckGoSearchResults,
)
import logging

logger = logging.getLogger(__name__)


# === HackerAssistantAgent 五欄位 + sections（由原 _generate_dynamic_instructions 拆解） ===

_GUIDELINES = """<guidelines>
    <rule id="1">Delegate low-level scanning, complex script execution, and large data analysis tasks to the AutomationAgent (Layer 3) or specific analyzer agents.</rule>
    <rule id="2">When calling the `automation_agent` tool, you must provide a clear `instruction` (e.g., 'Analyze the HTML in blob_id=45 for hidden forms'). You may optionally provide `target_name` ONLY if the instruction is related to a specific penetration testing target.</rule>
    <rule id="3">Synthesize findings from sub-agents and report progress concisely to the user.</rule>
    <rule id="4">Create seeds only for targets explicitly provided by the user; avoid using placeholders.</rule>
    <rule id="5">If a target already has discovered assets (domains, IPs, URLs), prioritize attacking/analyzing them over indefinite enumeration.</rule>
    <rule id="6">Always verify the Target ID using `list_active_targets` before performing target-specific actions.</rule>
    <rule id="7">Be concise in your communication. Acknowledge commands briefly and let the user monitor detailed progress via the UI.</rule>
    <rule id="8">[Data Management] Large tool outputs are automatically compressed and saved to the database. If you see a `blob_id`, DO NOT try to read it yourself unless it's very short. Instead, delegate the analysis to a sub-agent or use `read_content_blob` with a specific `focus_query` or `page=N`.</rule>
    <rule id="9">[Context Binding] Once you call `bind_to_target`, the session will be automatically bound to the active Overview. You DO NOT need to provide `overview_id` in subsequent tool calls; the system will inject it for you.</rule>
    <rule id="10">[Direct DB Queries] You now have direct read access to the asset database. For quick lookups — listing subdomains, IPs, URLs, endpoints, CVEs, execution history, or URL intelligence — use the structured query tools (get_target_context, query_urls, check_scanned_*, query_endpoints, get_url_intelligence, query_cve_by_id, query_steps, etc.) DIRECTLY instead of delegating to AutomationAgent. This is faster and cheaper.</rule>
    <rule id="11">[When to Delegate] STILL delegate to AutomationAgent (Layer 3) when the task requires: running scans (nmap/nuclei/subfinder), executing scripts in the Kali sandbox, performing multi-step attack chains, or analyzing very large data outputs. Rule of thumb: if it involves a tool named run_* or execute_*, delegate it.</rule>
    <rule id="12">[Pagination] When a blob has multiple pages (shown as `**Pages**: N pages available`), use `read_content_blob(blob_id=X, page=N)` to read one page at a time. Each page is a self-contained topic section. Do NOT use `read_content_blob` without `page` for paginated blobs — that will only return the summary.</rule>
    <rule id="13">[Agent Orchestration Awareness] When you delegate to AutomationAgent, it may further spawn sub-agents (ReconAgent, PostExploitAgent, ReportingAgent). These run asynchronously and report back via SubAgentDispatch. You can monitor their progress by calling `get_target_context(target_name)` to check the Overview status, or `query_steps(overview_id)` to see the execution graph. Do NOT re-delegate the same task while a sub-agent is RUNNING.</rule>
    <rule id="14">[Skill Awareness] When you receive a new task, first check if the domain involves any loadable Skill. Use `search_skills(query='<topic>')` to search the skill library. If a matching skill is found, load its rules into context to guide your methodology.</rule>
  </guidelines>"""

_OVERVIEW_STANDARDS = """<overview_standards tool="create_or_update_target_overview">
    <field name="plan_json_string">
      Always provide a valid JSON string with this structure:
      {"objectives": [{"id": 1, "description": "...", "priority": "HIGH|MEDIUM|LOW", "status": "PENDING|IN_PROGRESS|DONE|FAILED"}], "reasoning": "...", "generated_at": "ISO8601"}
    </field>
    <field name="risk_score">
      <level range="0-30">Recon only, no exploitable issues.</level>
      <level range="31-60">Low risk / info disclosure.</level>
      <level range="61-85">Mid-high severity (SQLi/SSRF/IDOR).</level>
      <level range="86-100">Critical (RCE/full auth bypass).</level>
    </field>
    <note>Stay calm and don't overdescribe the issue, only provide the facts.</note>
  </overview_standards>"""


def _reflect_tool_catalog(_agent) -> str:
    """動態注入 AutomationAgent 工具詳情（原 _generate_dynamic_instructions 的動態部分）。

    作為 AgentSpec extra_sections 的 callable，於 render 時呼叫。
    失敗時回傳空字串（退回 base sections）。
    """
    try:
        from apps.auto.cai.tool_reflector import get_tool_reflector
        reflector = get_tool_reflector()
        return (reflector.generate_tool_markdown() + reflector.generate_tool_decision_tree()).strip()
    except Exception as e:
        logger.warning("Failed to generate dynamic tool catalog: %s. Using base sections only.", e)
        return ""


_HACKER_ASSISTANT_SPEC = AgentSpec(
    name="Hacker Assistant",
    role=(
        "Orchestrator Hacker Assistant (Layer 2), responsible for managing "
        "penetration testing workflows and coordinating specialized agents."
    ),
    task=TaskDefinition(
        goal=(
            "Manage the overall penetration testing workflow: triage user requests, "
            "make direct read-only DB queries for quick lookups, and delegate heavy "
            "tasks (scans, script execution, multi-step attack chains, large data "
            "analysis) to AutomationAgent (Layer 3). Synthesize findings and report "
            "concisely to the user."
        ),
        background=(
            "You are the top-level orchestrator the user talks to directly. "
            "AutomationAgent (Layer 3) may further spawn ReconAgent / PostExploitAgent / "
            "ReportingAgent asynchronously. Each target has a 1:1 Overview tracking "
            "status/plan/knowledge/risk_score."
        ),
        materials=(
            "User's natural-language requests in the conversation thread. "
            "Asset DB is queryable directly via structured tools (get_target_context, "
            "query_urls, query_endpoints, get_url_intelligence, query_cve_by_id, "
            "query_steps, list_active_targets, etc.). Sub-agent findings arrive as "
            "notify_caller_agent messages."
        ),
        boundary=(
            "1. 嚴禁發明或猜測任何 Target/Overview ID；必須先以 list_active_targets 或 "
            "get_target_context 驗證。\n"
            "2. 嚴禁自行執行 run_*/execute_* 類工具（掃描、沙箱腳本）；必須委派 AutomationAgent。\n"
            "3. 大型 blob 輸出不可自行讀取（除非極短）；改委派子代理或使用 read_content_blob(page=N)。\n"
            "4. 子代理 RUNNING 時不可重複委派相同任務。\n"
            "5. 溝通要簡潔；只回報事實與結論，不贅述。"
        ),
        dod=(
            "Each turn must either: (a) answer the user concisely with DB-backed facts, "
            "(b) delegate a heavy task to automation_agent and acknowledge, or "
            "(c) update Overview via create_or_update_target_overview with valid "
            "plan_json_string + risk_score (0-100 per overview_standards)."
        ),
    ),
    extra_sections={
        "guidelines": _GUIDELINES,
        "overview_standards": _OVERVIEW_STANDARDS,
        "tool_catalog": _reflect_tool_catalog,
    },
    section_order=("guidelines", "overview_standards", "tool_catalog"),
)


class HackerAssistantAgent(
    ReconnaissanceMixin,
    EndpointMixin,
    CVEIntelligenceMixin,
    StepManagementMixin,
    SkillMixin,
    MemoryMixin,
    AIAssistant,
):
    id = "hacker_assistant_agent"
    name = "Hacker Assistant"
    SPEC = _HACKER_ASSISTANT_SPEC
    _REQUIRES_SPEC = True

    # 防護機制：與其他 Layer 3 agent 一致，防止 LLM 誤判 async 任務回傳為「失敗」
    # 而重複派發 AutomationAgent。
    # - stop_on_waiting_async=True：2+ 個 WAITING_FOR_ASYNC 工具回傳後強制結束迴圈
    # - max_consecutive_same_tool=3：同一工具連續呼叫 3 次後強制結束（防無限重派）
    stop_on_waiting_async = True
    max_consecutive_same_tool = 3

    # 工具黑名單：對 HackerAssistant (Layer 2 Orchestrator) 角色不適用的工具。
    # 這些工具是 Layer 3 sub-agent 向上溝通或執行腳本用的，HackerAssistant 不需要。
    _EXCLUDE_TOOLS = {
        'escalate_to_orchestrator',       # 向上請求指導 — HackerAssistant 就是頂層
        'read_orchestrator_guidance',     # 讀取上層指導 — 同上
        'create_overview',                # 與既有 create_or_update_target_overview 重疊
        'notify_caller_agent',            # sub-agent 向 parent 報告 — 無 parent
        'execute_skill_script',           # 腳本執行應委派 Layer 3
        'install_sandbox_dependency',     # 同上
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 讓 get_url_intelligence 遇到 PENDING URL 時不自動觸發 FlareSolverr 爬蟲。
        # HackerAssistant 是唯讀查詢模式，掃描應委派 Layer 3。
        self._skip_auto_crawl = True
        # 自動注入所需 ID 欄位（初始為 None，由 bind_to_target 或 get_target_context 設定）
        self._agent_overview_id = None
        self._caller_thread_id = None
        self._current_invoke_thread_id = None


    def get_llm(self):
        return get_llm_instance(agent_id=self.id)

    @method_tool
    def bind_to_target(self, target_id: int) -> str:
        """Bind this conversation session to a specific Target ID.
        After binding, all subsequent operations will default to this target.
        Use list_active_targets first to find the correct Target ID."""
        try:
            from apps.core.models.ai_models import Thread
            from apps.core.models import Target
            thread = self._init_kwargs.get('thread')
            if not thread:
                return "Error: Cannot bind — no active thread found."
            target = Target.objects.filter(id=target_id).first()
            if not target:
                return f"Error: Target ID {target_id} does not exist in the database."
            
            # 1:1 關係：每個 target 只有唯一 overview
            overview = getattr(target, 'overview', None)
            if overview and overview.status not in ("PLANNING", "EXECUTING", "NEEDS_GUIDANCE"):
                # 既有 overview 已 COMPLETED/STALLED — 仍可復用，只是 status 不活躍
                pass
            ov_id = overview.id if overview else None
            
            Thread.objects.filter(id=thread.id).update(
                bound_target_id=target_id,
                bound_overview_id=ov_id
            )
            # 同步到 instance，後續工具呼叫（透過 as_graph wrap 注入）才能正確讀取
            self._agent_overview_id = ov_id
            
            msg = f"[BOUND] This session is now focused on Target '{target.name}' (ID: {target_id})."
            if ov_id:
                msg += f" Automatically bound to active Overview #{ov_id}."
            return msg
        except Exception as e:
            return f"Error binding target: {str(e)}"

    @method_tool
    def unbind_target(self) -> str:
        """Remove the current target binding from this conversation session."""
        try:
            from apps.core.models.ai_models import Thread
            thread = self._init_kwargs.get('thread')
            if not thread:
                return "Error: Cannot unbind — no active thread found."
            current_id = Thread.objects.filter(id=thread.id).values_list('bound_target_id', flat=True).first()
            Thread.objects.filter(id=thread.id).update(
                bound_target_id=None,
                bound_overview_id=None
            )
            if current_id:
                return f"[UNBOUND] Session is no longer focused on Target ID {current_id}."
            return "[UNBOUND] Session had no target binding."
        except Exception as e:
            return f"Error unbinding target: {str(e)}"

    def get_tools(self):
        from apps.auto.assistants.planning_agent import AutomationAgent

        # Capture caller thread_id so the async Celery task can create a
        # properly linked sub-thread + ExecutionGraph.
        ha_caller_thread_id = getattr(self, '_current_invoke_thread_id', None)

        my_custom_tools = [
            DuckDuckGoSearchResults(),
            AutomationAgent().as_tool(
                description=(
                    "Delegates tasks to the Automation Agent (Layer 3). "
                    "Use this for pentest loops, complex script execution, "
                    "running scans (nmap/nuclei/subfinder/flaresolverr), "
                    "or analyzing large data/blobs discovered during recon. "
                    "For simple read-only DB queries (listing assets, CVEs, execution history), "
                    "use the structured query tools directly instead."
                ),
                ha_caller_thread_id=ha_caller_thread_id,
            ),
        ]
        # 取得 mixin 產生的工具（_method_tools），過濾黑名單
        tools = [t for t in super().get_tools() if t.name not in self._EXCLUDE_TOOLS]
        for tool in my_custom_tools:
            tools.append(tool)
        return tools

    @method_tool
    def get_server_temperature(self) -> str:
        """Retrieve the current hardware/CPU temperature of the server."""
        import subprocess

        try:
            # First try using sensors command directly
            result = subprocess.run(
                "sensors", shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "temp" in result.stdout.lower():
                return result.stdout

            # Alternative fallback: reading thermal zone directly
            result = subprocess.run(
                "cat /sys/class/thermal/thermal_zone*/temp",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                temps = [f"{int(t)/1000}°C" for t in result.stdout.strip().split("\n")]
                return "Thermal Zones: " + ", ".join(temps)

            return "Command executed successfully but no temperature data found. Check if lm-sensors is installed."
        except Exception as e:
            return f"Unable to fetch temperature: {str(e)}"

    @method_tool
    def list_active_targets(self) -> str:
        """Fetch a list of all targets currently in the database to get their IDs and basic information before performing actions on them. Always use this to find the correct Target ID."""
        try:
            from apps.core.models import Target
            targets = Target.objects.all().values("id", "name", "created_at")
            if not targets:
                return "No targets found in the database. Instruct the user to create a target or provide seed data."
            
            result = "Currently known targets in the database:\n"
            for t in targets:
                result += f"- Target ID: {t['id']}, Name: {t['name']}, Created: {t['created_at'].strftime('%Y-%m-%d %H:%M:%S') if t['created_at'] else 'Unknown'}\n"
            return result
        except Exception as e:
            return f"Error listing targets: {str(e)}"

    @method_tool
    def check_asset_liveness(self, target_id: int) -> str:
        """
        快速探測指定 Target 底下所有資產 (Subdomains 和 IPs) 的存活狀態。
        使用 HTTP Request 檢測子域名、使用 ping 命令檢測 IP。
        在開始滲透測試之前，可使用此工具快速了解哪些資產是「活的」。

        Args:
            target_id: 要探測的 Target ID。
        """
        import subprocess
        import requests
        from apps.core.models import Subdomain, IP
        from apps.core.header_injection import get_tagged_headers

        results = []

        # --- 探測子域名 (HTTP) ---
        subdomains = list(Subdomain.objects.filter(target_id=target_id).values("id", "name")[:20])
        results.append("=== Subdomain Liveness Check (HTTP) ===")
        for sub in subdomains:
            hostname = sub["name"]
            status = "❌ DEAD"
            for scheme in ("https", "http"):
                try:
                    resp = requests.get(
                        f"{scheme}://{hostname}",
                        timeout=5,
                        allow_redirects=True,
                        verify=False,
                        headers=get_tagged_headers(target_id=target_id),
                    )
                    status = f"✅ ALIVE ({scheme.upper()}) — HTTP {resp.status_code}"
                    break
                except Exception:
                    continue
            results.append(f"  [{sub['id']}] {hostname}: {status}")

        # --- 探測 IP (ping) ---
        ips = list(IP.objects.filter(target_id=target_id).values("id", "address")[:20])
        results.append("\n=== IP Liveness Check (PING) ===")
        for ip in ips:
            addr = ip["address"]
            try:
                proc = subprocess.run(
                    ["ping", "-c", "1", "-W", "2", addr],
                    capture_output=True, text=True, timeout=5
                )
                alive = "✅ ALIVE" if proc.returncode == 0 else "❌ DEAD"
            except Exception as e:
                alive = f"❌ ERROR ({e})"
            results.append(f"  [{ip['id']}] {addr}: {alive}")

        if not subdomains and not ips:
            return f"Target ID {target_id} has no Subdomains or IPs in the database yet."

        return "\n".join(results)


    @method_tool
    def get_target_overview(self, target_name: str) -> str:
        """Fetch the latest AI strategic Overview (plan, knowledge, status) for a specific target so you can review Layer 3's progress."""
        try:
            from apps.core.models import Target
            import json
            
            target = Target.objects.get(name=target_name)
            overview = getattr(target, 'overview', None)
            if not overview:
                return f"No Overview found for target: {target_name}. Please wait for Data Pre-processing."
            
            return json.dumps({
                "id": overview.id,
                "status": overview.status,
                "summary": overview.summary,
                "reasoning_or_plan": overview.plan,
                "current_knowledge": overview.knowledge,
                "risk_score": overview.risk_score
            })
        except Exception as e:
            return f"Error retrieving overview: {str(e)}"

    @method_tool
    def create_or_update_target_overview(self, target_name: str, status: str, plan_json_string: str, risk_score: int) -> str:
        """Create or update the strategic Overview (plan and status) for a specific target. Only use this when you want to update the plan or status."""
        try:
            from apps.core.models.analyze.overview import Overview
            from apps.core.models import Target
            import json

            existing_ov_id = getattr(self, "_agent_overview_id", None)
            if existing_ov_id:
                overview = Overview.objects.filter(id=existing_ov_id).first()
                if overview:
                    target = overview.target
                else:
                    target = Target.objects.filter(name=target_name).first()
                    if not target:
                        return f"Error: Overview id={existing_ov_id} not found and no Target named '{target_name}' exists."
                    overview, _ = Overview.objects.get_or_create(target=target, defaults={"status": "PLANNING"})
            else:
                bound_target_id = None
                t = getattr(self, "_thread", None)
                if t:
                    bound_target_id = getattr(t, "bound_target_id", None)
                    if bound_target_id:
                        bound_target_id = getattr(bound_target_id, "id", bound_target_id)
                if bound_target_id:
                    target = Target.objects.filter(id=bound_target_id).first()
                else:
                    target = Target.objects.filter(name=target_name).first()
                if not target:
                    target = Target.objects.create(name=target_name)
                overview, _ = Overview.objects.get_or_create(target=target, defaults={"status": "PLANNING"})

            self._agent_overview_id = overview.id
            overview.status = status
            if plan_json_string:
                try:
                    plan_data = json.loads(plan_json_string) if isinstance(plan_json_string, str) else plan_json_string
                    overview.plan = plan_data
                except Exception:
                    pass
            overview.risk_score = risk_score
            overview.save()
            return f"Successfully updated Overview {overview.id} for target {target.name} (id={target.id}) to status {status}."
        except Exception as e:
            return f"Error updating overview: {str(e)}"



