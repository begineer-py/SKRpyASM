import logging
import json
from celery import shared_task
from c2_core.config.logging import log_function_call
from apps.ai_assistant.helpers.use_cases import create_thread
from apps.core.models import Target, Subdomain, IP
from apps.core.models.analyze.overview import Overview

logger = logging.getLogger(__name__)


def _handle_guidance_request(overview):
    """
    當 AutomationAgent 卡住時（overview.status == NEEDS_GUIDANCE），
    自動讀取其問題、當前上下文、步驟歷史，然後使用 LLM 產生戰略指導建議。
    指導建議會以 Message 形式發送到 AutomationAgent 的 Thread，然後恢復 EXECUTING 狀態。
    """
    import json
    from apps.core.llms import get_llm_instance
    from apps.core.models import ExecutionGraph

    target = overview.target
    knowledge = overview.knowledge or {}
    escalation = knowledge.pop('_escalation', None)
    if not escalation:
        logger.warning(f"[Guidance] Overview {overview.id} is NEEDS_GUIDANCE but no escalation data found. Resetting to EXECUTING.")
        overview.status = "EXECUTING"
        overview.save(update_fields=['status'])
        return

    question = escalation.get('question', 'No question provided')
    thread_ids = [value for value in [overview.thread_id, overview.parent_thread_id] if value]
    recent_executions = list(
        ExecutionGraph.objects.filter(thread_id__in=thread_ids)
        .order_by('-started_at')[:10]
        .values('id', 'status', 'assistant_id', 'title', 'started_at', 'completed_at')
    ) if thread_ids else []

    prompt = (
        "You are a senior penetration testing strategist advising a sub-agent that is stuck.\n\n"
        f"## Target\n{target.name} ({target.description or 'No description'})\n\n"
        f"## Current Risk Score\n{overview.risk_score}/100\n\n"
        f"## Current Knowledge\n{json.dumps(knowledge, indent=2)}\n\n"
        f"## Recent Executions (last 10)\n{json.dumps(recent_executions, indent=2, default=str)}\n\n"
        f"## Sub-agent's Question\n{question}\n\n"
        "Your task: Provide focused, actionable strategic guidance. Be specific — "
        "mention exact tools, techniques, or alternative attack paths. "
        "Consider: is this the right attack vector? Should they pivot to a different "
        "endpoint/service? Is there a configuration weakness they missed? "
        "Format your response as a concise paragraph (max 300 words). "
        "Do NOT ask the sub-agent to do things they've already tried."
    )

    try:
        llm = get_llm_instance(temperature=0.3)
        resp = llm.invoke(prompt)
        guidance = resp.content if hasattr(resp, 'content') else str(resp)
    except Exception as e:
        guidance = (
            f"[Auto-Guidance] The system was unable to generate strategic analysis. "
            f"Try these general approaches:\n"
            f"1. Pivot to a different endpoint/service — don't fixate on one vector\n"
            f"2. Run more recon: check for hidden endpoints, subdomains, or open ports\n"
            f"3. Review the technology stack for version-specific exploits\n"
            f"4. Try chaining multiple low-severity issues together\n"
            f"5. Consider completely different attack categories (e.g. switch from injection to auth bypass)"
        )
        logger.warning(f"[Guidance] LLM call failed, using fallback guidance: {e}")

    from apps.core.models.ai_models import Thread as AIThread
    from apps.core.models import Message as DjangoMessage
    from langchain_core.messages import HumanMessage, message_to_dict

    try:
        guidance_thread = AIThread.objects.get(id=overview.thread_id)
        guidance_msg = HumanMessage(
            content=f"🧠 **Orchestrator Strategic Guidance**\n\n{guidance}\n\n---\n*Auto-generated. Use this to decide your next move.*"
        )
        DjangoMessage.objects.create(
            thread=guidance_thread,
            role="human",
            message=message_to_dict(guidance_msg),
        )
        logger.info(f"[Guidance] Saved guidance message to thread {overview.thread_id}")
    except Exception as e:
        logger.error(f"[Guidance] Failed to save guidance to thread {overview.thread_id}: {e}")

    # Clean escalation data from knowledge
    overview.knowledge = knowledge
    overview.status = "EXECUTING"
    overview.save(update_fields=['knowledge', 'status'])

    logger.info(f"[Guidance] Delivered strategic guidance to Overview {overview.id} (thread {overview.thread_id})")


@shared_task(name="apps.auto.tasks.auto_execute_plan")
@log_function_call()
def auto_execute_plan():
    """
    Celery Beat 定期任務：自動化執行引擎（鏈式流程最終環節）

    完整鏈式流程：
      新資產 → periodic_initial_analysis_bootstrapper (Layer 1)
             → propose_next_steps (Layer 2)
             → auto_execute_plan (Layer 3, 本任務)

    職責：
    1. 對卡在 PLANNING 狀態的 Overview 自動觸發策略規劃
    2. 對 NEEDS_GUIDANCE 狀態的 Overview 自動生成指導建議
    3. 對 EXECUTING 狀態的 Overview 驅動 AutomationAgent 執行
    """
    from apps.auto.assistants.planning_agent import AutomationAgent
    from langchain_core.messages import HumanMessage
    import json

    # ═══ Phase 0: 對停滯在 PLANNING 的 Overview 自動觸發策略規劃 ═══
    stalled_planning = Overview.objects.filter(status="PLANNING")
    for ov in stalled_planning:
        from apps.core.models import ExecutionGraph

        thread_ids = [value for value in [ov.thread_id, ov.parent_thread_id] if value]
        has_active_execution = ExecutionGraph.objects.filter(
            thread_id__in=thread_ids,
            status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
        ).exists() if thread_ids else False
        if not has_active_execution:
            from apps.analyze_ai.tasks.planning import propose_next_steps
            logger.info(f"[AutoExecute] Overview#{ov.id} 停滯在 PLANNING 且無 active execution，觸發策略規劃")
            propose_next_steps.delay(ov.id)

    overviews = Overview.objects.filter(status__in=["EXECUTING", "NEEDS_GUIDANCE"])
    if not overviews.exists():
        return

    for overview in overviews:
        # ════════════════════════════════════════════════════════════════
        # NEEDS_GUIDANCE handling: Auto-generate strategic guidance
        # when AutomationAgent escalates with a question.
        # ════════════════════════════════════════════════════════════════
        if overview.status == "NEEDS_GUIDANCE":
            logger.info(f"[AutoExecution] Overview {overview.id} is NEEDS_GUIDANCE — generating strategic guidance...")
            try:
                _handle_guidance_request(overview)
            except Exception as e:
                logger.error(f"[AutoExecution] Guidance generation failed for Overview {overview.id}: {e}")
                overview.status = "EXECUTING"
                overview.save(update_fields=['status'])
            continue

        target = overview.target
        logger.info(f"[AutoExecution] Starting autonomous execution for Target {target.name}")
        
        try:
            # _crawl_pending_urls 已移除，URL 爬取由 scheduler 定時任務負責
            # （scan_urls_missing_response + periodic_initial_analysis_bootstrapper）
            
            # 確保每個 Overview 有屬於自己的 Django AI Thread
            if not overview.thread_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                system_user = User.objects.filter(is_superuser=True).first()
                thread_obj = create_thread(
                    name=f"Auto-Pentest: {target.name} (Overview {overview.id})",
                    assistant_id="automation_agent",
                    user=system_user,
                    is_hidden=True,
                )
                overview.thread_id = thread_obj.id
                overview.save(update_fields=['thread_id'])
                logger.info(f"[AutoExecution] Created new Thread {thread_obj.id} for Overview {overview.id}")
            else:
                from apps.core.models.ai_models import Thread
                thread_obj = Thread.objects.get(id=overview.thread_id)
            
            from apps.core.models import ExecutionGraph

            if ExecutionGraph.objects.filter(
                thread=thread_obj,
                status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
            ).exists():
                logger.info(f"[AutoExecution] Overview#{overview.id} already has an active execution graph, skipping to avoid concurrent agents")
                continue
            
            # AIAssistant.invoke creates the ExecutionGraph; no legacy Step wrapper is needed.
            agent = AutomationAgent(thread=thread_obj)
            
            # ════════════════════════════════════════════════════════════════
            # 注入未消化的子代理回報摘要（喚醒後提示 agent 去消化）
            # ════════════════════════════════════════════════════════════════
            from apps.core.models import SubAgentDispatch
            pending_dispatches = list(
                SubAgentDispatch.objects.filter(
                    overview=ov, status="COMPLETED", synthesized=False
                ).order_by("-completed_at")[:5]
            )
            dispatch_hint = ""
            if pending_dispatches:
                dispatch_lines = []
                for d in pending_dispatches:
                    dispatch_lines.append(
                        f"- [{d.sub_agent_type}] completed at {d.completed_at}: {(d.result_summary or '(無摘要)')[:300]}"
                    )
                dispatch_hint = (
                    f"\n\n=== ⚠️ SUB-AGENT REPORTS (awaiting your synthesis) ===\n"
                    f"You have {len(pending_dispatches)} completed sub-agent dispatch(es) to review.\n"
                    f"Call `query_dispatched_agents` immediately to get full details.\n"
                    f"Preview:\n" + "\n".join(dispatch_lines) + "\n=== END ===\n"
                )
            
            # 收集真實的 Asset IDs，避免 AI 幻覺亂猜 ID
            from apps.core.models import Subdomain, IP, Seed
            from apps.core.models.url_assets import URLResult
            real_subdomain_ids = list(Subdomain.objects.filter(target=target).values_list("id", flat=True)[:10])
            real_ip_ids = list(IP.objects.filter(target=target).values_list("id", flat=True)[:10])
            real_seed_ids = list(Seed.objects.filter(target=target).values("id", "type", "value")[:10])
            # 只給 AI 已經爬取完成的 URL（非 PENDING），AI 不需要也不應該自己爬
            real_url_ids = list(
                URLResult.objects.filter(target=target)
                .exclude(content_fetch_status="PENDING")
                .values_list("id", flat=True)[:15]
            )
            
            system_prompt = agent.get_instructions()
            
            # 為每種資產生成明確的 "空清單" 警告，阻止 AI 在清單為空時亂猜 ID
            def _fmt_ids(label, ids):
                if not ids:
                    return f"{label}: [] — THIS LIST IS EMPTY. DO NOT call any tool requiring this type of IDs."
                return f"{label}: {ids}"
            
            user_prompt = (
                f"[SYSTEM CRITICAL]: Your session has been bound to a single Overview for this target. "
                f"The platform auto-injects the correct overview_id into all your tool calls — "
                f"DO NOT pass overview_id / thread_id / parent_thread_id explicitly. "
                f"NEVER invent or guess any IDs.\n\n"
                f"=== SESSION CONTEXT ===\n"
                f"Target Name: {target.name}\n"
                f"Target ID: {target.id}\n"
                f"{_fmt_ids('Real Seed IDs (for Subfinder/crawler)', real_seed_ids)}\n"
                f"{_fmt_ids('Real Subdomain IDs (for Nuclei)', real_subdomain_ids)}\n"
                f"{_fmt_ids('Real IP IDs (for Nmap/Nuclei)', real_ip_ids)}\n"
                f"{_fmt_ids('Real URL Result IDs (already crawled)', real_url_ids)}\n"
                f"=== END OF CONTEXT ===\n\n"
                f"Current Knowledge: {json.dumps(overview.knowledge)}\n"
                f"Current Plan: {json.dumps(overview.plan)}\n"
                f"{dispatch_hint}\n\n"
                f"Task: Execute the PENDING objectives in the plan using your tools. "
                "Use ONLY the IDs listed above. If a list is empty, skip tools that require those IDs."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use agent.invoke() which automatically applies callbacks
            result = agent.invoke(
                {"input": user_prompt},
                thread=thread_obj,
                thread_id=thread_obj.id
            )
            
            logger.info(f"[AutoExecution] Agent execution completed for {target.name}")
                 
        except Exception as e:
            logger.error(f"[AutoExecution] Failed executing plan for {target.name}: {e}")

@shared_task(name="apps.auto.tasks.run_automation_agent_async", bind=True, max_retries=2, default_retry_delay=120)
@log_function_call()
def run_automation_agent_async(self, message: str, caller_thread_id: int = None):
    from apps.auto.assistants.planning_agent import AutomationAgent
    from langgraph.errors import GraphRecursionError

    agent = AutomationAgent(caller_thread_id=caller_thread_id)
    try:
        result = agent._run_as_tool(message, caller_thread_id=caller_thread_id)
        agent._auto_notify_parent(result=result)
        return result
    except GraphRecursionError:
        # 不重試 recursion 錯誤——重試只會再次撞上限（問題 ⑤）
        logger.warning(
            f"[run_automation_agent_async] GraphRecursionError (caller_thread_id={caller_thread_id}); "
            f"notifying parent and skipping retry."
        )
        agent._auto_notify_parent(
            error="Agent 已達思考步驟上限（GraphRecursionError），任務中止以免無限重試。"
        )
        return {"output": "GraphRecursionError: agent hit recursion limit.", "error": "GraphRecursionError"}
    except Exception as e:
        logger.exception(f"[run_automation_agent_async] Failed: {e}")
        agent._auto_notify_parent(error=str(e))
        raise self.retry(exc=e)


def _run_sub_agent(agent_class, agent_id_label, message, caller_thread_id):
    """共用輔助函式：執行子 Agent；graph lifecycle 由 AIAssistant.invoke 管理。

    回傳 dict: {result, sub_thread_id, agent_instance}
      - sub_thread_id: 子代理綁定的 Thread ID（供 SubAgentDispatch 記錄）
    """
    from langgraph.errors import GraphRecursionError

    agent = agent_class(caller_thread_id=caller_thread_id)
    sub_thread_id = None
    try:
        result = agent._run_as_tool(message, caller_thread_id=caller_thread_id)
        # _run_as_tool 會把 self._thread 設為 sub_thread
        sub_thread = getattr(agent, '_thread', None)
        if sub_thread:
            sub_thread_id = getattr(sub_thread, 'id', None)
        return {"result": result, "sub_thread_id": sub_thread_id, "agent_instance": agent}
    except GraphRecursionError:
        logger.warning(
            f"[{agent_id_label}] GraphRecursionError swallowed (caller_thread_id={caller_thread_id})"
        )
        sub_thread = getattr(agent, '_thread', None)
        if sub_thread:
            sub_thread_id = getattr(sub_thread, 'id', None)
        return {
            "result": {"output": "GraphRecursionError: agent hit recursion limit.", "error": "GraphRecursionError"},
            "sub_thread_id": sub_thread_id,
            "agent_instance": agent,
        }
    except Exception as e:
        logger.exception(f"[{agent_id_label}] Failed: {e}")
        raise


def _resolve_overview_for_dispatch(overview_id, target_name, caller_thread_id, task_label):
    """解析子代理任務的 Overview 並綁定 parent_thread_id（1:1 關係下確保唯一）。

    回傳 (overview, overview_id) — 若無法解析則 (None, None)
    """
    if not (overview_id or target_name):
        return None, None
    try:
        from apps.core.models import Target, Overview
        ov = None
        if overview_id:
            ov = Overview.objects.filter(id=overview_id).first()
        elif target_name:
            target = Target.objects.filter(name=target_name).first()
            if target:
                ov = getattr(target, 'overview', None)
        if ov and caller_thread_id and not ov.parent_thread_id:
            ov.parent_thread_id = caller_thread_id
            ov.save(update_fields=["parent_thread_id"])
        return ov, (ov.id if ov else None)
    except Exception as e:
        logger.warning(f"[{task_label}] Could not resolve/bind overview: {e}")
        return None, None


def _record_dispatch(overview_id, dispatcher_thread_id, sub_agent_type, sub_thread_id, objective, task_label, status="RUNNING"):
    """建立 SubAgentDispatch 記錄，讓 AutomationAgent 能結構化追蹤子代理。"""
    if not overview_id:
        return None
    try:
        from apps.core.models import SubAgentDispatch
        dispatch = SubAgentDispatch.objects.create(
            overview_id=overview_id,
            dispatcher_thread_id=dispatcher_thread_id,
            sub_agent_type=sub_agent_type,
            sub_thread_id=sub_thread_id,
            objective=objective or "",
            status=status,
        )
        logger.info(f"[{task_label}] Recorded dispatch #{dispatch.id}: {sub_agent_type} → Overview#{overview_id}")
        return dispatch
    except Exception as e:
        logger.warning(f"[{task_label}] Failed to record dispatch: {e}")
        return None


@shared_task(name="apps.auto.tasks.run_recon_agent_async", bind=True, max_retries=2, default_retry_delay=120)
@log_function_call()
def run_recon_agent_async(self, message: str, target_name: str = "", caller_thread_id: int = None, overview_id: int = None, dispatcher_thread_id: int = None):
    from apps.auto.agents.recon_agent import ReconAgent

    ov, resolved_ov_id = _resolve_overview_for_dispatch(overview_id, target_name, caller_thread_id, "run_recon_agent_async")

    full_message = message
    if target_name:
        full_message = (
            f"[RECON MISSION] Target: {target_name}\n\n"
            f"First call get_target_context('{target_name}') to obtain overview_id and asset IDs.\n"
            f"Then execute full reconnaissance (subfinder, nmap, gau, katana, nuclei tech scan).\n"
            f"When all async tasks are dispatched, call notify_caller_agent with a full recon report.\n\n"
            f"Additional context: {message}"
        )
    try:
        result = _run_sub_agent(ReconAgent, "run_recon_agent_async", full_message, caller_thread_id)
        # 建立派發記錄（使用 task 執行後取得的 sub_thread_id）
        if resolved_ov_id:
            sub_tid = result.get("sub_thread_id") if isinstance(result, dict) else None
            _record_dispatch(
                overview_id=resolved_ov_id,
                dispatcher_thread_id=dispatcher_thread_id or caller_thread_id,
                sub_agent_type="recon_agent",
                sub_thread_id=sub_tid,
                objective=full_message[:500],
                task_label="run_recon_agent_async",
            )
        return result.get("result", result) if isinstance(result, dict) else result
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(name="apps.auto.tasks.run_post_exploit_agent_async", bind=True, max_retries=2, default_retry_delay=120)
@log_function_call()
def run_post_exploit_agent_async(self, message: str, target_name: str = "", caller_thread_id: int = None, overview_id: int = None, dispatcher_thread_id: int = None):
    from apps.auto.agents.post_exploit_agent import PostExploitAgent

    ov, resolved_ov_id = _resolve_overview_for_dispatch(overview_id, target_name, caller_thread_id, "run_post_exploit_agent_async")

    full_message = message
    if target_name:
        full_message = (
            f"[POST-EXPLOITATION MISSION] Target: {target_name}\n\n"
            f"First call get_target_context('{target_name}') to obtain overview_id.\n"
            f"Then execute post-exploitation: confirm environment, collect internal network info, "
            f"gather credentials, attempt lateral movement.\n"
            f"Record findings with record_vulnerability() and call notify_caller_agent when done.\n\n"
            f"Additional context: {message}"
        )
    try:
        result = _run_sub_agent(PostExploitAgent, "run_post_exploit_agent_async", full_message, caller_thread_id)
        if resolved_ov_id:
            sub_tid = result.get("sub_thread_id") if isinstance(result, dict) else None
            _record_dispatch(
                overview_id=resolved_ov_id,
                dispatcher_thread_id=dispatcher_thread_id or caller_thread_id,
                sub_agent_type="post_exploit_agent",
                sub_thread_id=sub_tid,
                objective=full_message[:500],
                task_label="run_post_exploit_agent_async",
            )
        return result.get("result", result) if isinstance(result, dict) else result
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(name="apps.auto.tasks.run_reporting_agent_async", bind=True, max_retries=2, default_retry_delay=120)
@log_function_call()
def run_reporting_agent_async(
    self,
    message: str,
    target_name: str = "",
    overview_id: int = None,
    caller_thread_id: int = None,
    dispatcher_thread_id: int = None,
):
    from apps.auto.agents.reporting_agent import ReportingAgent

    ov, resolved_ov_id = _resolve_overview_for_dispatch(overview_id, target_name, caller_thread_id, "run_reporting_agent_async")

    full_message = message
    if target_name or overview_id:
        ctx = f"Target: {target_name}" if target_name else ""
        if overview_id:
            ctx += f" | Overview ID: {overview_id}"
        full_message = (
            f"[REPORTING MISSION] {ctx}\n\n"
            f"Query all steps, vulnerabilities, and findings from the database.\n"
            f"Generate a structured penetration test report.\n"
            f"Update overview status to COMPLETED and call notify_caller_agent with the full report.\n\n"
            f"Additional context: {message}"
        )
    try:
        result = _run_sub_agent(ReportingAgent, "run_reporting_agent_async", full_message, caller_thread_id)
        if resolved_ov_id:
            sub_tid = result.get("sub_thread_id") if isinstance(result, dict) else None
            _record_dispatch(
                overview_id=resolved_ov_id,
                dispatcher_thread_id=dispatcher_thread_id or caller_thread_id,
                sub_agent_type="reporting_agent",
                sub_thread_id=sub_tid,
                objective=full_message[:500],
                task_label="run_reporting_agent_async",
            )
        return result.get("result", result) if isinstance(result, dict) else result
    except Exception as e:
        raise self.retry(exc=e)
