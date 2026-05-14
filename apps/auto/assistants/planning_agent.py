import logging
from typing import Optional, Sequence
from langchain_core.callbacks import BaseCallbackHandler
from django_ai_assistant import AIAssistant
from apps.core.llms import get_llm_instance
from apps.auto.tools.db_tools import DBToolsMixin
from apps.auto.tools.scanner_tools import ScannerToolsMixin
from apps.auto.callbacks.step_log_handler import StepLogCallbackHandler
logger = logging.getLogger(__name__)


class AutomationAgent(AIAssistant, DBToolsMixin, ScannerToolsMixin):
    id = "automation_agent"
    name = "Pentest Automation Agent"
    instructions = (
        "You are an expert penetration tester (Layer 3 AutomationAgent). "
        "Before executing any recon or attack on a target, you MUST call `get_target_context(target_name)` first to retrieve the overview_id and asset IDs. "
        "Use ONLY the overview_id and asset IDs returned by that tool.\n\n"
        "DO NOT just repeat safety warnings or generic advice. Focus on actionable intelligence and attacks.\n\n"
        
        "## 執行監控（系統自動）\n"
        "系統會自動記錄你所有的工具調用、執行結果和錯誤。無需手動呼叫任何 log_* 方法。\n"
        "專注於執行任務本身，系統會為你保持完整的審計日誌。\n\n"
        
         "## HOW TO OPERATE: Iterative Recon-Attack Loop\n"
         "Do NOT follow a rigid sequential pipeline. Instead, repeat this loop:\n\n"
         "**LOOP ITERATION:**\n"
         "1. **THINK**: What do I know? What intelligence does the DB already have? Pick the most promising attack target.\n"
         "2. **QUERY**: Call `get_url_intelligence(url_id=<id>)` for any URL you want to understand. "
         "   This returns Forms, Endpoints, TechStack, Findings, Vulnerabilities, and Headers from the DB – all in one call. "
         "   Use it liberally. Never guess what a page contains.\n"
         "3. **ACT**: Perform ONE concrete action (curl a form, submit an injection payload, run a scanner tool).\n"
         "   → Execute the action\n"
         "4. **NOTE**: Immediately after each action, call `write_recon_note(overview_id, title, content)` "
         "   to save what you observed. If it's an important intelligence update (tech found, new attack vector), "
         "   also call `update_overview_status(overview_id, new_knowledge={...})` to persist it.\n"
         "5. **REPEAT**: Based on your findings, pick the next target and loop again.\n\n"

        "## CONCRETE RULES:\n\n"
        "**Reading URLs from DB:**\n"
        "When you receive a context listing URL IDs, call `get_url_intelligence(url_id=<id>)` for each one. "
        "This is cheaper than guessing and more accurate than curl. "
        "If the DB has no content yet (content_fetch_status=PENDING), THEN use `run_flaresolverr_crawler` to fetch it.\n\n"

        "**Forms and Application Logic (Skill System First!):**\n"
        "Your script logic natively executes in an isolated Kali Linux Docker container (`c2_kali_sandbox`), meaning you have access to standard CLI hacking tools. Most crucially, wordlists (e.g. `rockyou.txt`) are available under `/usr/share/wordlists/`. If your script needs brute-forcing, simply use the wordlists from this path.\n"
        "**CRITICAL - Sandbox Autonomy**: If your skill script fails with an `ImportError` (e.g., missing `pymysql`, `paramiko`) or a command not found (e.g., `mariadb-client`), DO NOT just give up! You MUST use the `install_sandbox_dependency` tool (package_manager: 'apt' or 'pip', package_name: str) to permanently install the required packages into your sandbox, and then IMMEDIATELY re-execute the script.\n"
        "If you see a complex form (like a Django form with `csrfmiddlewaretoken`), DO NOT just blindly use curl every time.\n"
        "1. First, call `search_skills` (e.g. `query='django csrf'`) to see if you have a reusable Python script in the DB.\n"
        "2. If it exists, call `load_skill` to learn how to use it, then execute it with `execute_skill_script`.\n"
        "3. If NO skill exists for a complex/repetitive task that cannot be solved with basic tools, write a temporary Python script yourself to handle it, execute it, "
        "and when successful, IMMEDIATELY call `create_or_update_skill` to save this script into the database so you (and future agents) can reuse it. "
        "CRITICAL RULE ON SKILLS: Skill scripts MUST be highly practical and solve specific, complex problems (e.g., bypassing CSRF, complex multi-step auth). "
        "DO NOT write skills for trivial tasks like checking security headers, checking if a port is open, basic HTTP GET requests, or things that native tools already handle. "
        "Writing scripts for trivial tasks is a waste of execution performance. If unsure, stick to basic tools.\n"
        "Example of temporary curl fallback: `curl -X POST https://target.com/ -d 'csrfmiddlewaretoken=...&a=b' -c /tmp/c.txt`\n"
        "Write the actual server response into a StepNote with `write_recon_note`.\n\n"

        "**Deep Discovery:**\n"
        "Call `run_subfinder_discovery`, `run_gau_url_discovery`, `run_nmap_port_scan` when you need more attack surface. "
        "These are async – call them and then wait for the callback. Do not loop-retry them.\n\n"

        "**Vulnerability Scanning:**\n"
        "Run `run_nuclei_vuln_scan_urls` or tech scans ONLY after you have read the URL intelligence "
        "and have a reason to believe a scanner would find something. Not as a first blind step.\n\n"

        "**When done with a phase or finding vulnerabilities:**\n"
        "Call `notify_caller_agent(overview_id, message)` to report up. "
        "If a scanner tool returns WAITING_FOR_ASYNC, stop and wait for the callback. Do not loop.\n\n"

        "## OVERVIEW FIELD STANDARDS:\n\n"

        "**plan** — MUST use this JSON structure when calling `update_overview_status(new_plan=...)`:\n"
        "{\"objectives\": [{\"id\": 1, \"description\": \"Enumerate all POST endpoints\", \"priority\": \"HIGH\", \"status\": \"PENDING\"|\"IN_PROGRESS\"|\"DONE\"|\"FAILED\"},  ...], \"reasoning\": \"Why these objectives in this order\", \"generated_at\": \"ISO8601\"}\n"
        "Update status of each objective as you complete it. Do NOT invent other structures.\n\n"

        "**risk_score** — Use these guidelines when calling `update_overview_status(new_risk_score=...)`:\n"
        "0-30:  Recon only. No exploitable weaknesses found.\n"
        "31-60: Information disclosure or low-risk misconfiguration (e.g. verbose errors, exposed headers).\n"
        "61-85: Confirmed mid-high severity (SQLi, SSRF, IDOR, auth bypass on non-critical path).\n"
        "86-100: Critical — RCE, full auth bypass, admin takeover, or data exfiltration confirmed.\n\n"

        "**summary** — Free-form text note. Write in plain language what you have observed so far. No format required.\n"
        "**knowledge** — Free-form JSON dict. Example: {\"csrf_bypass\": \"token fetched from /login\", \"admin_path\": \"/manage\"}. No schema required."
    )

    def __init__(self, step_id: Optional[int] = None, **kwargs):
        """Initialize AutomationAgent with optional step_id for logging.
        
        Args:
            step_id: Optional ID of the Step model to log execution to.
                     If provided, all tool calls will be automatically logged.
            **kwargs: Additional arguments to pass to parent class
        """
        super().__init__(**kwargs)
        self.step_id = step_id

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        """Provide StepLog callback handler if step_id is set.
        
        Returns:
            Sequence[BaseCallbackHandler]: List containing StepLogCallbackHandler
                                          if step_id is set, otherwise empty list
        """
        if self.step_id:
            return [StepLogCallbackHandler(step_id=self.step_id)]
        return []

    def get_llm(self):
        return get_llm_instance(temperature=0)

    def get_tools(self):
        """
        組合工具集：
        1. 從父類別 (AIAssistant + DBToolsMixin) 取得 @method_tool 方法
        2. 從 CAI Factory 動態生成所有平台 API 工具（依賴 OpenAPI schema）
        """
        base_tools = super().get_tools()

        try:
            from apps.auto.cai.api_tool_factory import build_tools_from_openapi

            api_tools = build_tools_from_openapi(
                # 排除管理性/文件類端點，以及尚未實作的工具
                exclude_paths=[
                    "/api/assistant/",
                    "/api/openapi",
                    "/api/docs",
                    "/api/http_sender/fuzz",
                    "/api/scheduler/",
                    "/api/api_keys/",
                    "/api/analyze_ai/",
                    "/api/auto_convert/",
                    "/api/targets/",
                    "/api/scanners/",          # Exclude new unified scanner API
                    "/api/flaresolverr/",      # Exclude flaresolverr
                    # These might be deprecated but just in case:
                    "/api/nuclei/",
                    "/api/get_all_url/",
                    "/api/nmap/",
                    "/api/subdomain/"
                ]
            )
            logger.info(
                f"[AutomationAgent] 成功掛載 {len(api_tools)} 個平台 API 工具。"
            )
        except Exception as e:
            logger.error(f"[AutomationAgent] 無法載入平台 API 工具: {e}")
            api_tools = []

        return base_tools + api_tools

    def as_tool(self, description: str):
        """
        Override as_tool to force Orchestrator to pass `target_name` explicitly,
        allowing us to auto-resolve the context and inject it.
        """
        import logging
        from langchain_core.tools import StructuredTool
        from langchain_core.runnables import RunnableConfig
        from typing import Any
        
        _logger = logging.getLogger("django_ai_assistant.agent")
        _logger.info(f"[AS_TOOL REGISTERED override] assistant_id={self.id!r} | description={description!r}")
        
        def _tool_func(instruction: str, target_name: str = None, config: RunnableConfig = None) -> Any:
            thread_id = None
            if config and "configurable" in config:
                thread_id = config["configurable"].get("thread_id")
                
            final_message = f"**INSTRUCTION FROM ORCHESTRATOR**:\n{instruction}"
            if target_name:
                final_message += f"\n\nTarget Focus: {target_name}. If needed, use `get_target_context('{target_name}')` to retrieve IDs."
                
            return self._run_as_tool(final_message, caller_thread_id=thread_id)
            
        return StructuredTool.from_function(
            func=_tool_func,
            name=self.id,
            description=description,
        )



