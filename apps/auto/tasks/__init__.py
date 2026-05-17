import logging
import json
from celery import shared_task
from c2_core.config.logging import log_function_call
from django_ai_assistant import AIAssistant, method_tool
from django_ai_assistant.helpers.use_cases import create_thread
from apps.core.models import Target, Subdomain, IP
from apps.core.models.analyze.overview import Overview
from apps.analyze_ai.assistants import InitialAnalyzerAgent
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.auto.tasks.preprocess_data")
@log_function_call()
def preprocess_data():
    """
    Celery Beat 定期任務：Data Pre-processing Layer
    功能：掃描全平台 Target 的新資產，呼叫 InitialAnalyzerAgent，並將其結果寫入 Overview 提供給第 2 層。
    """
    targets = Target.objects.all()
    for target in targets:
        # 尋找是否已經有 PLANNING 或 EXECUTING 的 overview
        active_overview = Overview.objects.filter(target=target, status__in=["PLANNING", "EXECUTING"]).first()
        
        # 收集資產資訊 (拿最新的 50 筆供 Initial AI 分析)
        from apps.core.models import Seed
        seeds = list(Seed.objects.filter(target=target).values("type", "value"))
        subdomains = list(Subdomain.objects.filter(target=target).values_list("name", flat=True)[:50])
        ips = list(IP.objects.filter(target=target).values_list("address", flat=True)[:50])
        
        if not seeds and not subdomains and not ips:
            continue
            
        data_to_analyze = {
            "target": target.name,
            "description": target.description,
            "seeds": seeds,
            "subdomains_sample": subdomains,
            "ips_sample": ips
        }
        
        try:
            agent = InitialAnalyzerAgent()
            llm = agent.get_llm() # Returns JSON format ChatMistralAI
            system_prompt = agent.get_instructions()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(data_to_analyze)}
            ]
            response = llm.invoke(messages)
            
            # 解析 Initial Analyzer 的 JSON 回應
            try:
                ai_result = json.loads(response.content)
            except json.JSONDecodeError:
                ai_result = {"raw": response.content}

            # 若無正在運行的 Overview，建立一個新的（使用 select_for_update 防並發重複建立）
            from django.db import transaction
            with transaction.atomic():
                active_overview = Overview.objects.select_for_update().filter(
                    target=target, status__in=["PLANNING", "EXECUTING"]
                ).first()
                if not active_overview:
                    active_overview = Overview.objects.create(
                        target=target,
                        status="PLANNING",
                        summary=f"Automated pre-processing summary for {target.name}",
                    )
            
            active_overview.knowledge = ai_result.get("knowledge", ai_result)
            
            # 初始化規劃
            # 我們給 Layer 3 的 Plan
            # Initial AI 找出攻擊點後，更新 plan 讓 Orchestrator (Layer 2) 知道
            new_plan = ai_result.get("plan", {
                "objectives": [{"id": 1, "description": "Investigate newly found subdomains and IPs.", "status": "PENDING"}],
                "reasoning": "Data pre-processing detected active assets."
            })
            active_overview.plan = new_plan
            active_overview.save()
            
            logger.info(f"[PreProcess] Successfully updated Overview ID {active_overview.id} for Target {target.name}")
            
        except Exception as e:
            logger.error(f"[PreProcess] Failed analyzing target {target.name}: {e}")

def _crawl_pending_urls(target):
    """
    在交給 AI 之前，由系統自動爬取所有 PENDING 的 URL。
    流量削鋒：少量多次，每次最多爬 3 個，間隔 10 秒，避免瞬間大量請求。
    """
    from apps.core.models.url_assets import URLResult
    pending = list(URLResult.objects.filter(
        target=target, content_fetch_status="PENDING"
    ).values("id", "url")[:20])
    
    if not pending:
        return
    
    logger.info(f"[AutoExecution] Auto-crawling {len(pending)} PENDING URLs for {target.name} (流量削鋒: 每次最多3個, 間隔10s)")
    import requests
    import time
    from django.conf import settings
    API_BASE = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")
    
    batch_size = 3
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        for url_item in batch:
            try:
                resp = requests.post(
                    f"{API_BASE.rstrip('/')}/flaresolverr/start_scanner",
                    json={"url": url_item["url"], "method": "GET"},
                    timeout=10,
                )
                if resp.status_code >= 400:
                    logger.warning(f"[AutoExecution] Crawl dispatch failed for URL {url_item['id']}: {resp.status_code}")
            except Exception as e:
                logger.warning(f"[AutoExecution] Crawl error for URL {url_item['id']}: {e}")
        if i + batch_size < len(pending):
            logger.info(f"[AutoExecution] 流量削鋒: 已送出 {min(i+batch_size, len(pending))}/{len(pending)}，等待 10 秒後繼續...")
            time.sleep(10)


def _handle_guidance_request(overview):
    """
    當 AutomationAgent 卡住時（overview.status == NEEDS_GUIDANCE），
    自動讀取其問題、當前上下文、步驟歷史，然後使用 LLM 產生戰略指導建議。
    指導建議會以 Message 形式發送到 AutomationAgent 的 Thread，然後恢復 EXECUTING 狀態。
    """
    import json
    from apps.core.llms import get_llm_instance
    from apps.core.models import Step
    from django_ai_assistant.helpers.use_cases import create_message
    from django.contrib.auth import get_user_model

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

    User = get_user_model()
    system_user = User.objects.filter(is_superuser=True).first()

    create_message(
        assistant_id="automation_agent",
        thread_id=overview.thread_id,
        user=system_user,
        content=f"🧠 **Orchestrator Strategic Guidance**\n\n{guidance}\n\n---\n*Auto-generated. Use this to decide your next move.*"
    )

    # Clean escalation data from knowledge
    overview.knowledge = knowledge
    overview.status = "EXECUTING"
    overview.save(update_fields=['knowledge', 'status'])

    logger.info(f"[Guidance] Delivered strategic guidance to Overview {overview.id} (thread {overview.thread_id})")


@shared_task(name="apps.auto.tasks.auto_execute_plan")
@log_function_call()
def auto_execute_plan():
    """
    Celery Beat 定期任務：自動化執行引擎
    功能：
    1. 先自動爬取所有 PENDING URL（不讓 AI 浪費時間做爬蟲）
    2. 查找所有狀態為 PLANNING/EXECUTING 的 Overview，投入給 Layer 3 AutomationAgent 執行。
    如此一來就能達成真正的全自動：「新建 Domain -> Initial AI 產生計畫 -> 自動爬 URL -> 自動攻擊」
    """
    from apps.auto.assistants.planning_agent import AutomationAgent
    from langchain_core.messages import HumanMessage
    import json
    
    overviews = Overview.objects.filter(status__in=["PLANNING", "EXECUTING", "NEEDS_GUIDANCE"])
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
            # === Step 0: 系統自動爬取所有 PENDING URL ===
            _crawl_pending_urls(target)
            
            # 確保每個 Overview 有屬於自己的 Django AI Thread
            if not overview.thread_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                system_user = User.objects.filter(is_superuser=True).first()
                thread_obj = create_thread(
                    name=f"Auto-Pentest: {target.name} (Overview {overview.id})",
                    assistant_id="automation_agent",
                    user=system_user,
                )
                overview.thread_id = thread_obj.id
                overview.save(update_fields=['thread_id'])
                logger.info(f"[AutoExecution] Created new Thread {thread_obj.id} for Overview {overview.id}")
            else:
                from django_ai_assistant.models import Thread
                thread_obj = Thread.objects.get(id=overview.thread_id)
            
            # Create a Step to track this execution
            from apps.core.models import Step
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
    agent = AutomationAgent(caller_thread_id=caller_thread_id)
    try:
        result = agent._run_as_tool(message, caller_thread_id=caller_thread_id)
        agent._auto_notify_parent(result=result)
    except Exception as e:
        logger.error(f"[run_automation_agent_async] Failed: {e}")
        agent._auto_notify_parent(error=str(e))
