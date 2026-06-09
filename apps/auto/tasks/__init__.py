import logging
import json
from celery import shared_task
from c2_core.config.logging import log_function_call
from apps.ai_assistant.helpers.use_cases import create_thread
from apps.core.models import Target, Subdomain, IP
from apps.core.models.analyze.overview import Overview
from django.utils import timezone

logger = logging.getLogger(__name__)


def _handle_guidance_request(overview):
    """
    當 AutomationAgent 卡住時（overview.status == NEEDS_GUIDANCE），
    自動讀取其問題、當前上下文、步驟歷史，然後使用 LLM 產生戰略指導建議。
    指導建議會以 Message 形式發送到 AutomationAgent 的 Thread，然後恢復 EXECUTING 狀態。
    """
    import json
    from apps.core.llms import get_llm_instance
    from apps.core.models import Step

    target = overview.target
    knowledge = overview.knowledge or {}
    escalation = knowledge.pop('_escalation', None)
    if not escalation:
        logger.warning(f"[Guidance] Overview {overview.id} is NEEDS_GUIDANCE but no escalation data found. Resetting to EXECUTING.")
        overview.status = "EXECUTING"
        overview.save(update_fields=['status'])
        return

    question = escalation.get('question', 'No question provided')
    recent_steps = list(Step.objects.filter(overview=overview).order_by('-created_at')[:10].values(
        'id', 'status', 'operation_type', 'created_at'
    ))

    prompt = (
        "You are a senior penetration testing strategist advising a sub-agent that is stuck.\n\n"
        f"## Target\n{target.name} ({target.description or 'No description'})\n\n"
        f"## Current Risk Score\n{overview.risk_score}/100\n\n"
        f"## Current Knowledge\n{json.dumps(knowledge, indent=2)}\n\n"
        f"## Recent Steps (last 10)\n{json.dumps(recent_steps, indent=2, default=str)}\n\n"
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
        # 檢查是否有 PENDING 的 Step（有 = 正在等規劃結果，跳過）
        has_pending_steps = ov.steps.filter(status="PENDING").exists()
        if not has_pending_steps:
            from apps.analyze_ai.tasks.planning import propose_next_steps
            logger.info(f"[AutoExecute] Overview#{ov.id} 停滯在 PLANNING 且無待執行步驟，觸發策略規劃")
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
            
            # Create a Step to track this execution
            from apps.core.models import Step

            # Skip if another worker is already running an agent for this overview.
            if Step.objects.filter(overview=overview, status="RUNNING").exists():
                logger.info(f"[AutoExecution] Overview#{overview.id} already has a RUNNING step, skipping to avoid concurrent agents")
                continue

            step = Step.objects.create(
                overview=overview,
                operation_type="AI_AUTOMATION_EXECUTION",
                status="RUNNING"
            )
            
            # Initialize agent with step_id for logging + thread for checkpointing conversation
            agent = AutomationAgent(step_id=step.id, thread=thread_obj)
            
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
                f"[SYSTEM CRITICAL]: The ONLY valid overview_id is {overview.id}. "
                f"You MUST use overview_id={overview.id} in ALL tool calls. NEVER invent or guess IDs.\n\n"
                f"=== VALID IDs FOR THIS SESSION (DO NOT USE ANY OTHER IDs) ===\n"
                f"Target Name: {target.name}\n"
                f"Overview ID: {overview.id}\n"
                f"Target ID: {target.id}\n"
                f"{_fmt_ids('Real Seed IDs (for Subfinder/crawler)', real_seed_ids)}\n"
                f"{_fmt_ids('Real Subdomain IDs (for Nuclei)', real_subdomain_ids)}\n"
                f"{_fmt_ids('Real IP IDs (for Nmap/Nuclei)', real_ip_ids)}\n"
                f"{_fmt_ids('Real URL Result IDs (already crawled)', real_url_ids)}\n"
                f"=== END OF VALID IDs ===\n\n"
                f"Current Knowledge: {json.dumps(overview.knowledge)}\n"
                f"Current Plan: {json.dumps(overview.plan)}\n\n"
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
                thread_id=thread_obj.id
            )
            
            logger.info(f"[AutoExecution] Agent execution completed for {target.name}")
            
            # Mark step as completed
            step.status = "COMPLETED"
            step.completed_at = timezone.now()
            step.save(update_fields=["status", "completed_at"])
                
        except Exception as e:
            logger.error(f"[AutoExecution] Failed executing plan for {target.name}: {e}")
            # Mark step as failed on exception
            if 'step' in locals():
                step.status = "FAILED"
                step.completed_at = timezone.now()
                step.save(update_fields=["status", "completed_at"])

@shared_task(name="apps.auto.tasks.run_automation_agent_async")
@log_function_call()
def run_automation_agent_async(message: str, caller_thread_id: int = None):
    from apps.auto.assistants.planning_agent import AutomationAgent
    from apps.core.models import Step

    step = Step.objects.create(
        operation_type="AI_AUTOMATION_EXECUTION",
        status="RUNNING"
    )

    agent = AutomationAgent(step_id=step.id, caller_thread_id=caller_thread_id)
    try:
        result = agent._run_as_tool(message, caller_thread_id=caller_thread_id)
        step.status = "COMPLETED"
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "completed_at"])
        agent._auto_notify_parent(result=result)
        return result
    except Exception as e:
        logger.exception(f"[run_automation_agent_async] Failed: {e}")
        step.status = "FAILED"
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "completed_at"])
        agent._auto_notify_parent(error=str(e))
        raise


def _run_sub_agent(agent_class, agent_id_label, message, caller_thread_id):
    """共用輔助函式：建立 Step、執行子 Agent、處理完成/失敗。"""
    from apps.core.models import Step

    step = Step.objects.create(
        operation_type="AI_AUTOMATION_EXECUTION",
        status="RUNNING"
    )
    agent = agent_class(step_id=step.id, caller_thread_id=caller_thread_id)
    try:
        result = agent._run_as_tool(message, caller_thread_id=caller_thread_id)
        step.status = "COMPLETED"
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "completed_at"])
        return result
    except Exception as e:
        logger.exception(f"[{agent_id_label}] Failed: {e}")
        step.status = "FAILED"
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "completed_at"])
        raise


@shared_task(name="apps.auto.tasks.run_recon_agent_async")
@log_function_call()
def run_recon_agent_async(message: str, target_name: str = "", caller_thread_id: int = None):
    from apps.auto.agents.recon_agent import ReconAgent

    # Bind the overview's parent_thread_id to caller so notify_caller_agent routes correctly
    if caller_thread_id and target_name:
        try:
            from apps.core.models import Target, Overview
            target = Target.objects.filter(name=target_name).first()
            if target:
                ov = Overview.objects.filter(target=target).order_by("-updated_at").first()
                if ov and not ov.parent_thread_id:
                    ov.parent_thread_id = caller_thread_id
                    ov.save(update_fields=["parent_thread_id"])
        except Exception as e:
            logger.warning(f"[run_recon_agent_async] Could not bind overview parent_thread_id: {e}")

    full_message = message
    if target_name:
        full_message = (
            f"[RECON MISSION] Target: {target_name}\n\n"
            f"First call get_target_context('{target_name}') to obtain overview_id and asset IDs.\n"
            f"Then execute full reconnaissance (subfinder, nmap, gau, katana, nuclei tech scan).\n"
            f"When all async tasks are dispatched, call notify_caller_agent with a full recon report.\n\n"
            f"Additional context: {message}"
        )
    return _run_sub_agent(ReconAgent, "run_recon_agent_async", full_message, caller_thread_id)


@shared_task(name="apps.auto.tasks.run_post_exploit_agent_async")
@log_function_call()
def run_post_exploit_agent_async(message: str, target_name: str = "", caller_thread_id: int = None):
    from apps.auto.agents.post_exploit_agent import PostExploitAgent

    if caller_thread_id and target_name:
        try:
            from apps.core.models import Target, Overview
            target = Target.objects.filter(name=target_name).first()
            if target:
                ov = Overview.objects.filter(target=target).order_by("-updated_at").first()
                if ov and not ov.parent_thread_id:
                    ov.parent_thread_id = caller_thread_id
                    ov.save(update_fields=["parent_thread_id"])
        except Exception as e:
            logger.warning(f"[run_post_exploit_agent_async] Could not bind overview parent_thread_id: {e}")

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
    return _run_sub_agent(PostExploitAgent, "run_post_exploit_agent_async", full_message, caller_thread_id)


@shared_task(name="apps.auto.tasks.run_reporting_agent_async")
@log_function_call()
def run_reporting_agent_async(
    message: str,
    target_name: str = "",
    overview_id: int = None,
    caller_thread_id: int = None,
):
    from apps.auto.agents.reporting_agent import ReportingAgent

    if caller_thread_id and overview_id:
        try:
            from apps.core.models import Overview
            ov = Overview.objects.filter(id=overview_id).first()
            if ov and not ov.parent_thread_id:
                ov.parent_thread_id = caller_thread_id
                ov.save(update_fields=["parent_thread_id"])
        except Exception as e:
            logger.warning(f"[run_reporting_agent_async] Could not bind overview parent_thread_id: {e}")

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
    return _run_sub_agent(ReportingAgent, "run_reporting_agent_async", full_message, caller_thread_id)
