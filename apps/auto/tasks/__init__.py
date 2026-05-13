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

            # 若無正在運行的 Overview，建立一個新的
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

@shared_task(name="apps.auto.tasks.auto_execute_plan")
@log_function_call()
def auto_execute_plan():
    """
    Celery Beat 定期任務：自動化執行引擎
    功能：查找所有狀態為 PLANNING 的 Overview，直接投入給 Layer 3 AutomationAgent 執行。
    如此一來就能達成真正的全自動：「新建 Domain -> Initial AI 產生計畫 -> 自動啟動 Subfinder」
    """
    from apps.auto.assistants.planning_agent import AutomationAgent
    from langchain_core.messages import HumanMessage
    import json
    
    overviews = Overview.objects.filter(status__in=["PLANNING", "EXECUTING"])
    if not overviews.exists():
        return
        
    for overview in overviews:
        target = overview.target
        logger.info(f"[AutoExecution] Starting autonomous execution for Target {target.name}")
        
        try:
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
            
            agent = AutomationAgent()
            llm = agent.get_llm()
            tools = agent.get_tools()
            
            # Bind tools so the LLM can output tool calls
            llm_with_tools = llm.bind_tools(tools)
            
            # 收集真實的 Asset IDs，避免 AI 幻覺亂猜 ID
            from apps.core.models import Subdomain, IP, Seed
            from apps.core.models.url_assets import URLResult
            real_subdomain_ids = list(Subdomain.objects.filter(target=target).values_list("id", flat=True)[:10])
            real_ip_ids = list(IP.objects.filter(target=target).values_list("id", flat=True)[:10])
            real_seed_ids = list(Seed.objects.filter(target=target).values("id", "type", "value")[:10])
            real_url_ids = list(URLResult.objects.filter(target=target).values_list("id", flat=True)[:10])
            
            system_prompt = agent.get_instructions()
            
            # 為每種資產生成明確的 "空清單" 警告，阻止 AI 在清單為空時亂猜 ID
            def _fmt_ids(label, ids):
                if not ids:
                    return f"{label}: [] — THIS LIST IS EMPTY. DO NOT call any tool requiring {label.split()[1]} IDs."
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
                f"{_fmt_ids('Real URL Result IDs (for URL Nuclei/tech)', real_url_ids)}\n"
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
            
            # 觸發 LLM (如果有 Tool Calling 會在 response 中反映)
            response = llm_with_tools.invoke(messages)
            
            if response.tool_calls:
                logger.info(f"[AutoExecution] LLM is triggering tools for {target.name}: {response.tool_calls}")
                # We can execute the tools directly using langchain logic
                for tool_call in response.tool_calls:
                    target_tool = next((t for t in tools if t.name == tool_call["name"]), None)
                    if target_tool:
                        tool_result = target_tool.invoke(tool_call["args"])
                        logger.info(f"[AutoExecution] Tool {tool_call['name']} Result: {tool_result}")
                        
                # Update status to EXECUTING
                overview.status = "EXECUTING"
                overview.save()
            else:
                logger.info(f"[AutoExecution] LLM decided no tools to run. {response.content}")
                
        except Exception as e:
            logger.error(f"[AutoExecution] Failed executing plan for {target.name}: {e}")
