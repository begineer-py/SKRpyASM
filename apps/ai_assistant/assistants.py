from apps.ai_assistant import AIAssistant, method_tool
from apps.core.llms import get_llm_instance
from apps.auto.tools.memory_tools import MemoryMixin
from langchain_community.tools import (
    ShellTool,
    FileSearchTool,
    ListDirectoryTool,
    WriteFileTool,
    ReadFileTool,
    DuckDuckGoSearchResults,
)
from apps.auto.assistants.planning_agent import AutomationAgent
import logging

logger = logging.getLogger(__name__)


def _generate_dynamic_instructions() -> str:
    """
    動態生成 HackerAssistantAgent 的系統提示詞，包含 AutomationAgent 的完整工具詳情。
    """
    base_instructions = (
        "<system>\n"
        "  <role>\n"
        "    You are the Orchestrator Hacker Assistant (Layer 2), responsible for managing\n"
        "    penetration testing workflows and coordinating specialized agents.\n"
        "  </role>\n"
        "\n"
        "  <guidelines>\n"
        "    <rule id=\"1\">Delegate low-level scanning, complex script execution, and large data analysis tasks to the AutomationAgent (Layer 3) or specific analyzer agents.</rule>\n"
        "    <rule id=\"2\">When calling the `automation_agent` tool, you must provide a clear `instruction` (e.g., 'Analyze the HTML in blob_id=45 for hidden forms'). You may optionally provide `target_name` ONLY if the instruction is related to a specific penetration testing target.</rule>\n"
        "    <rule id=\"3\">Synthesize findings from sub-agents and report progress concisely to the user.</rule>\n"
        "    <rule id=\"4\">Create seeds only for targets explicitly provided by the user; avoid using placeholders.</rule>\n"
        "    <rule id=\"5\">If a target already has discovered assets (domains, IPs, URLs), prioritize attacking/analyzing them over indefinite enumeration.</rule>\n"
        "    <rule id=\"6\">Always verify the Target ID using `list_active_targets` before performing target-specific actions.</rule>\n"
        "    <rule id=\"7\">Be concise in your communication. Acknowledge commands briefly and let the user monitor detailed progress via the UI.</rule>\n"
        "    <rule id=\"8\">[Data Management] Large tool outputs are automatically compressed and saved to the database. If you see a `blob_id`, DO NOT try to read it yourself unless it's very short. Instead, delegate the analysis to a sub-agent or use `read_content_blob` with a specific `focus_query`.</rule>\n"
        "    <rule id=\"9\">[Context Binding] Once you call `bind_to_target`, the session will be automatically bound to the active Overview. You DO NOT need to provide `overview_id` in subsequent tool calls; the system will inject it for you.</rule>\n"
        "  </guidelines>\n"
        "\n"
        "  <overview_standards tool=\"create_or_update_target_overview\">\n"
        "    <field name=\"plan_json_string\">\n"
        "      Always provide a valid JSON string with this structure:\n"
        '      {"objectives": [{"id": 1, "description": "...", "priority": "HIGH|MEDIUM|LOW", "status": "PENDING|IN_PROGRESS|DONE|FAILED"}], "reasoning": "...", "generated_at": "ISO8601"}\n'
        "    </field>\n"
        "    <field name=\"risk_score\">\n"
        "      <level range=\"0-30\">Recon only, no exploitable issues.</level>\n"
        "      <level range=\"31-60\">Low risk / info disclosure.</level>\n"
        "      <level range=\"61-85\">Mid-high severity (SQLi/SSRF/IDOR).</level>\n"
        "      <level range=\"86-100\">Critical (RCE/full auth bypass).</level>\n"
        "    </field>\n"
        "    <note>Stay calm and don't overdescribe the issue, only provide the facts.</note>\n"
        "  </overview_standards>\n"
        "</system>\n\n"
    )
    
    # 動態注入 AutomationAgent 工具詳情
    try:
        from apps.auto.cai.tool_reflector import get_tool_reflector
        
        reflector = get_tool_reflector()
        tool_catalog = reflector.generate_tool_markdown()
        tool_guide = reflector.generate_tool_decision_tree()
        
        return base_instructions + tool_catalog + tool_guide
    except Exception as e:
        logger.warning(f"Failed to generate dynamic instructions: {e}. Using base instructions only.")
        return base_instructions


class HackerAssistantAgent(MemoryMixin, AIAssistant):
    id = "hacker_assistant_agent"
    name = "Hacker Assistant"
    instructions = _generate_dynamic_instructions()


    def get_llm(self):
        return get_llm_instance(agent_id=self.id)

    @method_tool
    def bind_to_target(self, target_id: int) -> str:
        """Bind this conversation session to a specific Target ID.
        After binding, all subsequent operations will default to this target.
        Use list_active_targets first to find the correct Target ID."""
        try:
            from apps.core.models.ai_models import Thread
            from apps.core.models import Target, Overview
            thread = self._init_kwargs.get('thread')
            if not thread:
                return "Error: Cannot bind — no active thread found."
            target = Target.objects.filter(id=target_id).first()
            if not target:
                return f"Error: Target ID {target_id} does not exist in the database."
            
            # Find the latest active overview for this target
            overview = Overview.objects.filter(
                target=target, 
                status__in=["PLANNING", "EXECUTING", "NEEDS_GUIDANCE"]
            ).order_by("-updated_at").first()
            
            ov_id = overview.id if overview else None
            
            Thread.objects.filter(id=thread.id).update(
                bound_target_id=target_id,
                bound_overview_id=ov_id
            )
            
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
        from langchain_community.utilities import SQLDatabase
        from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
        from django.conf import settings
        from apps.auto.assistants.planning_agent import AutomationAgent
        from apps.analyze_ai.assistants import InitialAnalyzerAgent

        db_settings = settings.DATABASES["default"]
        db_uri = (
            f"postgresql+psycopg2://{db_settings.get('USER', 'postgres')}:"
            f"{db_settings.get('PASSWORD', '')}@{db_settings.get('HOST', 'localhost')}:"
            f"{db_settings.get('PORT', '5432')}/{db_settings.get('NAME', 'postgres')}"
        )
        db = SQLDatabase.from_uri(db_uri)

        my_custom_tools = [
            DuckDuckGoSearchResults(),
            QuerySQLDataBaseTool(db=db),
            AutomationAgent().as_tool(
                description="Delegates tasks to the Automation Agent (Layer 3). Use this for pentest loops, complex script execution, or analyzing large data/blobs discovered during recon."
            ),
            InitialAnalyzerAgent().as_tool(
                description="Delegates initial analysis of assets to the Initial Analyzer Agent."
            ),
        ]
        tools = super().get_tools()
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
            from apps.core.models.analyze.overview import Overview
            from apps.core.models import Target
            import json
            
            target = Target.objects.get(name=target_name)
            overview = Overview.objects.filter(target=target).order_by('-updated_at').first()
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
            
            target, _ = Target.objects.get_or_create(name=target_name)
            overview = Overview.objects.filter(target=target).order_by('-updated_at').first()
            if not overview:
                overview = Overview.objects.create(target=target, status="PLANNING")
            
            overview.status = status
            if plan_json_string:
                try:
                    plan_data = json.loads(plan_json_string) if isinstance(plan_json_string, str) else plan_json_string
                    overview.plan = plan_data
                except:
                    pass
            overview.risk_score = risk_score
            overview.save()
            return f"Successfully updated Overview {overview.id} for target {target_name} to status {status}."
        except Exception as e:
            return f"Error updating overview: {str(e)}"



