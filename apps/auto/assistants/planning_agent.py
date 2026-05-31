import logging
from typing import Optional, Sequence
from langchain_core.callbacks import BaseCallbackHandler
from apps.ai_assistant import AIAssistant
from apps.core.llms import get_llm_instance
from apps.auto.tools.db_tools import DBToolsMixin
from apps.auto.tools.scanner_tools import ScannerToolsMixin
from apps.auto.callbacks.step_log_handler import StepLogCallbackHandler

logger = logging.getLogger(__name__)


class AutomationAgent(AIAssistant, DBToolsMixin, ScannerToolsMixin):
    id = "automation_agent"
    name = "Pentest Automation Agent"
    instructions = (
        "<system_role>\n"
        "You are an expert penetration tester (Layer 3 AutomationAgent) operating in a secure, isolated sandbox.\n"
        "Your mission is to autonomously discover, analyze, and exploit vulnerabilities on the designated targets.\n"
        "</system_role>\n\n"
        
        "<parent_notification_rule>\n"
        "⚠️ IMPORTANT: YOU MUST FOLLOW THIS EXACTLY ⚠️\n"
        "This agent was invoked by a parent/orchestrator agent that expects a completion report.\n"
        "At the END of your task (after ALL objectives are done or failed), you MUST call:\n"
        "  `notify_caller_agent(message='<summary of findings>')`\n"
        "If you do NOT call notify_caller_agent, the parent agent will hang forever.\n"
        "The system also has an auto-notify fallback, but you MUST still call it yourself.\n"
        "</parent_notification_rule>\n\n"

        "<escalation_rule>\n"
        "🆘 ESCALATION — WHEN YOU ARE STUCK 🆘\n"
        "If you try 3+ different approaches on the same attack vector and ALL fail "
        "(e.g. all standard SSTI bypasses blocked, all SQLi filters working, all auth bypasses rejected):\n"
        "1. Call `escalate_to_orchestrator(question)` with DETAILED context of what you tried and what failed\n"
        "2. Then call `read_orchestrator_guidance()` — the Orchestrator will analyze the situation\n"
        "3. If no guidance yet, take a break: check OTHER endpoints, do more recon, or scan for new attack surface\n"
        "4. Come back later and call `read_orchestrator_guidance()` again for fresh strategic directions\n"
        "NEVER waste more than 5 attempts on the same blocked vector before escalating.\n"
        "</escalation_rule>\n\n"

        "<context_rule>\n"
        "Before executing any recon or attack on a target, you MUST call `get_target_context(target_name)` first to retrieve the overview_id and asset IDs.\n"
        "Once you have called get_target_context, your session will be automatically bound to that target and overview. You DO NOT need to provide overview_id in subsequent tool calls.\n"
        "DO NOT just repeat safety warnings or generic advice. Focus on actionable intelligence and attacks.\n"
        "</context_rule>\n\n"

        "<execution_monitoring>\n"
        "## 執行監控（系統自動）\n"
        "系統會自動記錄你所有的工具調用、執行結果和錯誤。無需手動呼叫 any log_* 方法。\n"
        "專注於執行任務本身，系統會為你保持完整的審計日誌。\n"
        "</execution_monitoring>\n\n"

        "<operational_loop>\n"
        "## HOW TO OPERATE: Iterative Recon-Attack Loop\n"
        "Do NOT follow a rigid sequential pipeline. Instead, repeat this loop:\n"
        "1. **THINK**: What do I know? What intelligence does the DB already have? Pick the most promising attack target.\n"
        "2. **QUERY**: Call `get_url_intelligence(url_id=<id>)` for any URL you want to understand.\n"
        "   This returns Forms, Endpoints, TechStack, Findings, Vulnerabilities, and Headers from the DB – all in one call.\n"
        "   Use it liberally. Never guess what a page contains.\n"
        "3. **ACT**: Perform ONE concrete action (curl a form, submit an injection payload, run a scanner tool).\n"
        "4. **NOTE**: Immediately after each action, call `write_recon_note(title, content)`\n"
        "   to save what you observed. If it's an important intelligence update (tech found, new attack vector),\n"
        "   also call `update_overview_status(new_knowledge={...})` to persist it.\n"
        "5. **REPEAT**: Based on your findings, pick the next target and loop again.\n"
        "</operational_loop>\n\n"

        "<concrete_rules>\n"
        "### Reading URLs from DB:\n"
        "When you receive a context listing URL IDs, call `get_url_intelligence(url_id=<id>)` for each one.\n"
        "This is cheaper than guessing and more accurate than curl.\n"
        "All URL IDs provided to you have ALREADY been crawled by the system. Do NOT call run_flaresolverr_crawler — your job is to attack, not fetch.\n\n"
        
        "### Forms and Application Logic (Skill System First! + Type Validation!):\n"
        "Your script logic natively executes in an isolated Kali Linux Docker container (`c2_kali_sandbox`), meaning you have access to standard CLI hacking tools. Most crucially, wordlists (e.g. `rockyou.txt`) are available under `/usr/share/wordlists/`. If your script needs brute-forcing, simply use the wordlists from this path.\n"
        "**CRITICAL - Sandbox Autonomy**: If your skill script fails with an `ImportError` (e.g., missing `pymysql`, `paramiko`) or a command not found (e.g., `mariadb-client`), DO NOT just give up! You MUST use the `install_sandbox_dependency` tool (package_manager: 'apt' or 'pip', package_name: str) to permanently install the required packages into your sandbox, and then IMMEDIATELY re-execute the script.\n"
        "If you see a complex form (like a Django form with `csrfmiddlewaretoken`), DO NOT just blindly use curl every time.\n"
        "1. First, call `search_skills` (e.g. `query='django csrf'`) to see if you have a reusable Python script in the DB.\n"
        "2. If it exists, call `load_skill` to learn how to use it, then execute it with `execute_skill_script`.\n"
        "3. If NO skill exists for a complex/repetitive task that cannot be solved with basic tools, write a temporary Python script yourself to handle it, execute it,\n"
        "and when successful, IMMEDIATELY call `request_skill_creation` to generate and save a structured skill into the database so you (and future agents) can reuse it.\n"
        "   ⚠️ DO NOT write raw script_content directly. `request_skill_creation` takes a `task_description` (natural language) + schemas — SkillCreatorAgent handles the code generation.\n\n"
        

        "### 類型驗證與執行追蹤\n"
        "所有腳本（臨時或持久）執行都會自動被記錄到 ScriptExecution，前端可查看執行歷史與關聯 StepLog。\n\n"
        "**輸入參數驗證（Input Schema）**：\n"
        "When saving to SkillTemplate, ALWAYS define `input_schema` for parameters. Example:\n"
        "```json\n"
        "input_schema: {\"type\": \"object\", \"properties\": {\"url\": {\"type\": \"string\", \"pattern\": \"^https?://.*\"}}, \"required\": [\"url\"]}\n"
        "```\n"
        "When calling `execute_skill_script(name, input_json={\"url\": \"https://...\"})`, the system will validate input BEFORE execution.\n"
        "If input fails validation, execution is aborted with error message.\n\n"
        "**輸出驗證（Output Schema）**：\n"
        "Define `output_schema` for expected script output format. Example:\n"
        "```json\n"
        "output_schema: {\"type\": \"object\", \"properties\": {\"token\": {\"type\": \"string\"}, \"success\": {\"type\": \"boolean\"}}, \"required\": [\"token\", \"success\"]}\n"
        "```\n"
        "Your script MUST output valid JSON (or text containing JSON). The system will extract and validate the JSON against output_schema.\n"
        "If output fails validation, the execution is marked VALIDATION_ERROR and `last_failure_reason` is recorded.\n\n"
        "**臨時腳本執行追蹤**：\n"
        "Even if you write a one-off temporary script (不存到 SkillTemplate)，the system STILL records it in ScriptExecution:\n"
        "- 完整的腳本內容（script_content）\n"
        "- 輸入參數（input_json）與輸出（output_json）\n"
        "- 執行狀態（SUCCESS/FAILED/TIMEOUT）\n"
        "- 關聯的 Step 與 StepLog（便於前端顯示）\n"
        "This means you can always query `SELECT * FROM ScriptExecution WHERE attack_vector_id=123` to see all scripts run against a vector.\n\n"
        "CRITICAL RULE ON SKILLS: Skill scripts MUST be highly practical and solve specific, complex problems (e.g., bypassing CSRF, complex multi-step auth).\n"
        "DO NOT write skills for trivial tasks like checking security headers, checking if a port is open, basic HTTP GET requests, or things that native tools already handle.\n"
        "Writing scripts for trivial tasks is a waste of execution performance. If unsure, stick to basic tools.\n"
        "Example of temporary curl fallback: `curl -X POST https://target.com/ -d 'csrfmiddlewaretoken=...&a=b' -c /tmp/c.txt`\n"
        "Write the actual server response into a StepNote with `write_recon_note`.\n\n"
        
        "### Deep Discovery:\n"
        "Use `run_subfinder_discovery`, `run_gau_url_discovery`, `run_nmap_port_scan` for passive/network recon.\n"
        "These are async – call them and then wait for the callback. Do not loop-retry them.\n"
        "For active web enumeration (directories, files, parameters), use Kali tools via `run_command` in the sandbox — e.g.,\n"
        "`gobuster dir -u <url> -w /usr/share/wordlists/dirb/common.txt`, `dirb <url>`,\n"
        "`wfuzz -c -z file,/usr/share/wordlists/wfuzz/general/common.txt <url>/FUZZ`.\n\n"
        
        "### Vulnerability Scanning (Prefer Kali tools over Nuclei):\n"
        "Your sandbox is Kali Linux — use its native tools via `run_command` whenever possible. Examples:\n"
        "- **SQL injection**: `sqlmap -u <url> --batch --random-agent`\n"
        "- **Brute-force / auth**: `hydra -l admin -P /usr/share/wordlists/rockyou.txt <target> <service>`\n"
        "- **Directory/file discovery**: `gobuster dir -u <url> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt`\n"
        "- **Web vuln scanning**: `nikto -h <url>`\n"
        "- **Web fuzzing**: `wfuzz -c -z file,/usr/share/wordlists/wfuzz/general/common.txt <url>/FUZZ`\n"
        "Reserve Nuclei scans (`run_nuclei_vuln_scan_urls`, `run_nuclei_tech_scan_*`) for AFTER you have read the URL intelligence\n"
        "and have a reason to believe a scanner would find something. Not as a first blind step.\n\n"
        
        "### When done with a phase or finding vulnerabilities:\n"
        "Call `notify_caller_agent(message)` to report up.\n"
        "If a scanner tool returns WAITING_FOR_ASYNC, stop and wait for the callback. Do not loop.\n"
        "</concrete_rules>\n\n"

        "<overview_field_standards>\n"
        "**plan** — MUST use this JSON structure when calling `update_overview_status(new_plan=...)`:\n"
        '{"objectives": [{"id": 1, "description": "Enumerate all POST endpoints", "priority": "HIGH", "status": "PENDING"|"IN_PROGRESS"|"DONE"|"FAILED"},  ...], "reasoning": "Why these objectives in this order", "generated_at": "ISO8601"}\n'
        "Update status of each objective as you complete it. Do NOT invent other structures.\n\n"
        "**risk_score** — Use these guidelines when calling `update_overview_status(new_risk_score=...)`:\n"
        "0-30: Recon only. No exploitable weaknesses found.\n"
        "31-60: Information disclosure or low-risk misconfiguration (e.g. verbose errors, exposed headers).\n"
        "61-85: Confirmed mid-high severity (SQLi, SSRF, IDOR, auth bypass on non-critical path).\n"
        "86-100: Critical — RCE, full auth bypass, admin takeover, or data exfiltration confirmed.\n\n"
        "**summary** — Free-form text note. Write in plain language what you have observed so far. No format required.\n"
        '**knowledge** — Free-form JSON dict. Example: {"csrf_bypass": "token fetched from /login", "admin_path": "/manage"}. No schema required.\n'
        "</overview_field_standards>"
    )

    def __init__(
        self,
        step_id: Optional[int] = None,
        thread=None,
        caller_thread_id: Optional[int] = None,
        **kwargs,
    ):
        """Initialize AutomationAgent with optional step_id for logging.

        Args:
            step_id: Optional ID of the Step model to log execution to.
            thread: Optional Thread object for checkpointing conversation history.
            caller_thread_id: Thread ID of the parent agent that invoked this agent.
                              Used to auto-populate overview.parent_thread_id and
                              enable automatic parent notification on completion.
            **kwargs: Additional arguments to pass to parent class
        """
        super().__init__(**kwargs)
        self.step_id = step_id
        self._thread = thread
        self._caller_thread_id = caller_thread_id
        self._agent_overview_id = None

    def _auto_notify_parent(self, result=None, error=None):
        """Auto-notify parent agent when task completes or fails.

        Called by run_automation_agent_async after _run_as_tool returns.
        Only fires if:
        - An overview was created/used (_agent_overview_id is set)
        - The overview has parent_thread_id (meaning it was invoked by a parent)
        """
        if not self._agent_overview_id:
            return
        try:
            from apps.core.models import Overview

            overview = Overview.objects.filter(id=self._agent_overview_id).first()
            if not overview or not overview.parent_thread_id:
                return

            if error:
                msg = f"[Auto-Notify] Overview #{self._agent_overview_id} task FAILED:\n{error}"
            elif result:
                last_msgs = (
                    result.get("messages", []) if isinstance(result, dict) else []
                )
                summary = ""
                for m in reversed(last_msgs):
                    if hasattr(m, "content") and m.content:
                        summary = m.content[:500]
                        break
                msg = (
                    f"[Auto-Notify] Overview #{self._agent_overview_id} task COMPLETED.\n"
                    f"Risk Score: {overview.risk_score}\n"
                    f"Summary: {overview.summary or 'No summary'}\n"
                    f"Last AI message: {summary}"
                )
            else:
                msg = (
                    f"[Auto-Notify] Overview #{self._agent_overview_id} task completed."
                )

            self.notify_caller_agent(self._agent_overview_id, msg)
        except Exception as e:
            logger.warning(f"[AutoNotify] Failed: {e}")

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        """Provide StepLog + ThreadCheckpoint callback handlers.

        Returns:
            Sequence[BaseCallbackHandler]: List of callback handlers
        """
        callbacks: list[BaseCallbackHandler] = []
        if self.step_id:
            callbacks.append(StepLogCallbackHandler(step_id=self.step_id))
        if hasattr(self, "_thread") and self._thread:
            from apps.auto.callbacks.checkpoint_handler import ThreadCheckpointHandler

            callbacks.append(ThreadCheckpointHandler(thread=self._thread))
        return callbacks

    def get_llm(self):
        return get_llm_instance(
            agent_id="automation_agent",
            temperature=0
        )

    def get_tools(self):
        """
        組合工具集：
        1. 從父類別 (AIAssistant + DBToolsMixin) 取得 @method_tool 方法
        2. 從 CAI Factory 動態生成所有平台 API 工具（依賴 OpenAPI schema）
        """
        base_tools = super().get_tools()

        # 檢查是否已經存在 notify_caller_agent
        if not any(t.name == "notify_caller_agent" for t in base_tools):
            from apps.auto.tools.step_management_tools import StepManagementMixin
            # 如果因為某種原因基類沒抓到，手動補上
            # 但根據 AIAssistant 邏輯，應該已經在 base_tools 裡了
            pass

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
                    "/api/scanners/",  # Exclude new unified scanner API
                    "/api/flaresolverr/",  # Exclude flaresolverr
                    # These might be deprecated but just in case:
                    "/api/nuclei/",
                    "/api/get_all_url/",
                    "/api/nmap/",
                    "/api/subdomain/",
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

        _logger = logging.getLogger("ai_assistant.agent")
        _logger.info(
            f"[AS_TOOL REGISTERED override] assistant_id={self.id!r} | description={description!r}"
        )

        def _tool_func(
            instruction: str, target_name: str = None, config: RunnableConfig = None
        ) -> Any:
            thread_id = None
            if config and "configurable" in config:
                thread_id = config["configurable"].get("thread_id")

            final_message = f"**INSTRUCTION FROM ORCHESTRATOR**:\n{instruction}"
            if target_name:
                final_message += f"\n\nTarget Focus: {target_name}. If needed, use `get_target_context('{target_name}')` to retrieve IDs."

            from apps.auto.tasks import run_automation_agent_async

            run_automation_agent_async.delay(final_message, caller_thread_id=thread_id)
            return "Task delegated successfully to AutomationAgent in the background. Tell the user that the automation task has started."

        return StructuredTool.from_function(
            func=_tool_func,
            name=self.id,
            description=description,
        )
