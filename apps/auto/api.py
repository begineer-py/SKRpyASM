import json
import logging
from ninja import Router
from ninja.errors import HttpError
from asgiref.sync import sync_to_async

from apps.core.models import IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis
from apps.analyze_ai.tasks.common import (
    fetch_ip_data_for_batch,
    fetch_subdomain_data_for_batch,
    fetch_url_data_for_batch,
)
from .schemas import AutoConvertSchema, AutoConvertResponseSchema
# The schema for creating step from analysis is WIP or to be handled by Agent

router = Router()
logger = logging.getLogger(__name__)


# =============================================================================
# 轉換端點工廠設定 Registry (AUTO_CONVERT_CONFIG)
# =============================================================================

AUTO_CONVERT_CONFIG = {
    "ip": {
        "model": IPAIAnalysis,
        "related_field": "ip",
        "asset_fk_field": "ip",
        "asset_id_attr": "ip_id",
        "data_fetcher": fetch_ip_data_for_batch,
        "not_found_msg": "IP 分析記錄",
    },
    "subdomain": {
        "model": SubdomainAIAnalysis,
        "related_field": "subdomain",
        "asset_fk_field": "subdomain",
        "asset_id_attr": "subdomain_id",
        "data_fetcher": fetch_subdomain_data_for_batch,
        "not_found_msg": "子域名分析記錄",
    },
    "url": {
        "model": URLAIAnalysis,
        "related_field": "url_result",
        "asset_fk_field": "url_result",
        "asset_id_attr": "url_result_id",
        "data_fetcher": fetch_url_data_for_batch,
        "not_found_msg": "URL 分析記錄",
    },
}


# =============================================================================
# 通用轉換邏輯（Generic Converter）
# =============================================================================

async def _convert_analysis(asset_type: str, analysis_id: int) -> AutoConvertResponseSchema:
    """
    【通用分析轉換器】

    根據 asset_type 從 AUTO_CONVERT_CONFIG 取得設定，
    執行：讀取分析記錄 → 驗證狀態 → 取資產上下文 → 建立 Step 鏈。

    Args:
        asset_type:  'ip' | 'subdomain' | 'url'
        analysis_id: 分析記錄主鍵 ID

    Returns:
        AutoConvertResponseSchema
    """
    cfg = AUTO_CONVERT_CONFIG[asset_type]
    Model = cfg["model"]
    related = cfg["related_field"]

    # ── 1. 取得分析記錄 ──────────────────────────────────────────────────────
    try:
        analysis = await sync_to_async(
            Model.objects.select_related(related).get
        )(id=analysis_id)
    except Model.DoesNotExist:
        raise HttpError(
            404, f"找不到 ID 為 {analysis_id} 的{cfg['not_found_msg']}。"
        )

    # ── 2. 狀態驗證 ──────────────────────────────────────────────────────────
    if analysis.status != "COMPLETED":
        raise HttpError(
            400,
            f"分析記錄 {analysis_id} 尚未完成（當前狀態：{analysis.status}）。",
        )

    # ── 3. 檢查是否有 command_actions ────────────────────────────────────────
    command_actions = analysis.command_actions or []
    if not command_actions:
        return AutoConvertResponseSchema(
            success=True,
            detail="分析記錄中沒有建議操作，未建立任何步驟。",
            steps_created=0,
        )

    # ── 4. 取得資產上下文（GraphQL） ─────────────────────────────────────────
    asset_id = getattr(analysis, cfg["asset_id_attr"])
    try:
        asset_data = await sync_to_async(cfg["data_fetcher"])([asset_id])
        asset_context = json.dumps(asset_data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(
            f"獲取 {cfg['not_found_msg']}#{asset_id} 資產上下文失敗: {e}"
        )
        asset_context = "{}"

    # ── 5. 呼叫自動化代理規劃後續 Step ──────────────────────────────────────────
    from django.contrib.auth import get_user_model
    from django_ai_assistant.use_cases import create_thread
    from apps.auto.assistants.planning_agent import AutomationAgent

    User = get_user_model()
    system_user = await sync_to_async(User.objects.first)()
    if not system_user:
        system_user = await sync_to_async(User.objects.create)(username="system_auto_ai")

    overview = await sync_to_async(getattr)(analysis, "overview", None)
    if not overview:
        raise HttpError(400, f"分析記錄 {analysis_id} 尚未關聯到任何 Overview 戰略點。")

    # 這個工具跑在非同步 thread pool，我們先包成 sync 函數
    def _run_agent():
        assistant = AutomationAgent()
        thread = create_thread(
            name=f"Planning for Overview#{overview.id} ({asset_type})",
            user=system_user,
            assistant_id=assistant.id
        )
        # 準備組合給 AI 的上下文 (融合舊概覽 + 新情報 + 命令)
        prompt = f"""
請依據以下的新發現情報，更新目標的 Overview，並且針對發現建立後續的攻擊 Steps。
--- 當前戰略上下文 ---
Overview_ID: {overview.id}
Knowledge: {overview.knowledge}
Current Plan: {overview.plan}

--- 最新情報 (New Intelligence) ---
Risk Score: {analysis.risk_score}
Summary: {analysis.summary}
Vulnerabilities: {analysis.potential_vulnerabilities}
Raw Content: {asset_context}

[系統指令]
請呼叫你的工具來：
1. `update_overview_status` 把這個最新得到的情報整合進 Knowledge 和 Plan 裡面。
2. `create_step` 為了挖掘上方的 Vulnerabilities 或是探索更深層次，產生 1 到 5 個具體的攻擊執行動作。
注意傳遞參數時，asset_fk_field 為 '{cfg["asset_fk_field"]}'， asset_fk_value_id 為 {asset_id}。
"""
        return assistant.run(prompt, thread_id=thread.id)

    agent_output = await sync_to_async(_run_agent)()
    count = 1 # 這邊未來可透過抓資料庫新增資料判斷實際建立多少筆

    return AutoConvertResponseSchema(
        success=True,
        detail=f"成功從分析記錄 {analysis_id} 發起規劃任務。\nAI Agent Response:\n{agent_output}",
        steps_created=count,
    )


# =============================================================================
# API 端點（精簡版）
# =============================================================================

@router.post("/convert/ip", response=AutoConvertResponseSchema)
async def convert_ip_analysis(request, payload: AutoConvertSchema):
    """將已完成的 IP AI 分析轉換為可執行的步驟。"""
    return await _convert_analysis("ip", payload.analysis_id)


@router.post("/convert/subdomain", response=AutoConvertResponseSchema)
async def convert_subdomain_analysis(request, payload: AutoConvertSchema):
    """將已完成的子域名 AI 分析轉換為可執行的步驟。"""
    return await _convert_analysis("subdomain", payload.analysis_id)


@router.post("/convert/url", response=AutoConvertResponseSchema)
async def convert_url_analysis(request, payload: AutoConvertSchema):
    """將已完成的 URL AI 分析轉換為可執行的步驟。"""
    return await _convert_analysis("url", payload.analysis_id)


# =============================================================================
# Step 執行端點 (Step Execution Runner)
# =============================================================================

from pydantic import BaseModel
from typing import Optional

class RunStepSchema(BaseModel):
    step_id: int

class RunStepResponseSchema(BaseModel):
    success: bool
    detail: str
    task_id: Optional[str] = None


@router.post("/run-step", response=RunStepResponseSchema)
async def run_step(request, payload: RunStepSchema):
    """
    【觸發步驟自動執行】

    接收 step_id，將對應的 Step 派發給 AutomationAgent 執行。
    - 若 Step 為 CLI 任務，Agent 直接執行並觸發驗證。
    - 若 Step 為大規模 API 任務，Agent 掛起並等待異步回調。
    """
    from apps.auto.tasks.execution.runner import run_step_execution

    step_id = payload.step_id
    # 驗證 Step 存在
    from apps.core.models import Step
    exists = await sync_to_async(Step.objects.filter(id=step_id).exists)()
    if not exists:
        raise HttpError(404, f"Step#{step_id} 不存在。")

    task = await sync_to_async(run_step_execution.delay)(step_id)
    return RunStepResponseSchema(
        success=True,
        detail=f"Step#{step_id} 已提交執行，task_id: {task.id}",
        task_id=str(task.id),
    )


class ResumeStepSchema(BaseModel):
    step_id: int
    task_output: str


@router.post("/resume-step", response=RunStepResponseSchema)
async def resume_step(request, payload: ResumeStepSchema):
    """
    【異步回調入口】

    由外部系統（或手動測試）呼叫，將結果帶回給已掛起的 Step。
    正常情況下由 Celery Task 的 finally 回調自動觸發，不需要手動調用。
    """
    from apps.auto.tasks.execution.runner import resume_step_execution

    task = await sync_to_async(resume_step_execution.delay)(
        payload.step_id, payload.task_output
    )
    return RunStepResponseSchema(
        success=True,
        detail=f"Step#{payload.step_id} 已接收回調輸出，驗證引擎正在啟動。",
        task_id=str(task.id),
    )
