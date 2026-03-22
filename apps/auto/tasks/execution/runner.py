"""
apps/auto/tasks/execution/runner.py

自動化步驟執行器 (StepRunner)
──────────────────────────────────────
核心職責:
  1. 接收 step_id，驅動 AutomationAgent 執行 Step 中的 command_template
  2. 同步指令: 直接取得輸出並回寫，觸發驗證引擎
  3. 異步工具: 掛起 Step 為 WAITING_FOR_ASYNC，等待外部回調喚醒
  4. 提供 resume_step_execution: 由異步工具 Callback 呼叫，接續驗證流程

設計原則:
  - 絕不輪詢 (no polling)
  - 每個任務都是短暫的 Celery Task，用完即釋放 Worker 資源
  - 異步工具的結果由 callback 帶入，無需等待
"""

import logging
import json
from typing import Optional

from celery import shared_task
from django.utils import timezone

from apps.core.models import Step, Verification

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────
# Celery 任務: 執行指定 Step
# ──────────────────────────────────────────────────

@shared_task(name="auto.tasks.execution.run_step")
def run_step_execution(step_id: int) -> dict:
    """
    【主要執行任務】接收 step_id，驅動 AI 執行該步驟。

    流程:
      1. 載入 Step 及相關資產上下文。
      2. 組裝 Prompt 送入 AutomationAgent。
      3. Agent 自主決策: 執行 CLI 指令 或 呼叫系統異步工具。
      4. 同步結果直接回寫 output，異步工具回傳標記並掛起。
    """
    try:
        # 1. 載入 Step
        step = Step.objects.prefetch_related(
            "ip", "subdomain", "url_result", "verifications"
        ).get(id=step_id)
    except Step.DoesNotExist:
        logger.error(f"[StepRunner] Step#{step_id} 不存在，任務終止。")
        return {"ok": False, "error": "Step not found"}

    if step.status not in ("PENDING", "FAILED"):
        logger.warning(
            f"[StepRunner] Step#{step_id} 狀態為 {step.status}，跳過執行。"
        )
        return {"ok": False, "error": f"Step already in state {step.status}"}

    # 2. 標記為執行中
    step.status = "RUNNING"
    step.save(update_fields=["status"])
    logger.info(f"[StepRunner] ▶ 開始執行 Step#{step_id}: {step.command_template[:80]}...")

    # 3. 組裝資產上下文
    asset_context = _build_asset_context(step)
    # 載入所有 Verification 模板
    verifications = list(step.verifications.all())
    verification_info = [
        {
            "observation_prompt": v.observation_prompt,
            "confidence_threshold": v.confidence_threshold,
            "auto_create_vulnerability": v.auto_create_vulnerability,
            "vulnerability_name": v.vulnerability_name,
            "vulnerability_severity": v.vulnerability_severity,
        }
        for v in verifications
    ]

    # 4. 驅動 AutomationAgent 執行
    result = _run_automation_agent(step, asset_context, verification_info)

    # 5. 依 Agent 回傳結果決定後續狀態
    if result.get("type") == "sync_done":
        # 同步執行完成: 直接存輸出並觸發驗證
        output = result.get("output", "")
        _save_execution_output(step, verifications, output)

        step.status = "COMPLETED"
        step.save(update_fields=["status"])
        logger.info(f"[StepRunner] ✅ Step#{step_id} 同步執行完成，觸發驗證引擎。")

        # 觸發驗證引擎
        from apps.auto.tasks.evaluation.engine import process_verification
        for v in verifications:
            process_verification.delay(v.id)

    elif result.get("type") == "async_dispatched":
        # 異步工具已觸發: 掛起並等待 Callback 喚醒
        # 狀態由此對應的目標任務完成後呼叫 resume_step_execution 時更新
        step.status = "WAITING_FOR_ASYNC"
        step.note = (step.note or "") + f"\n[{timezone.now().isoformat()}] 已派發異步任務: {result.get('dispatched_tool')}"
        step.save(update_fields=["status", "note"])
        logger.info(
            f"[StepRunner] ⏳ Step#{step_id} 已掛起，等待異步工具回調: {result.get('dispatched_tool')}"
        )

    else:
        # Agent 執行失敗
        step.status = "FAILED"
        step.note = (step.note or "") + f"\n[ERROR] {result.get('error', 'Unknown error')}"
        step.save(update_fields=["status", "note"])
        logger.error(f"[StepRunner] ❌ Step#{step_id} 執行失敗: {result.get('error')}")

    return result


# ──────────────────────────────────────────────────
# Celery 任務: 異步工具回調喚醒
# ──────────────────────────────────────────────────

@shared_task(name="auto.tasks.execution.resume_step")
def resume_step_execution(step_id: int, task_output: str) -> dict:
    """
    【異步回調任務】由系統其他 Celery Task (e.g. Nuclei, Nmap) 完成時呼叫。

    參數:
        step_id:     原本被掛起的 Step ID
        task_output: 異步工具產生的輸出摘要或結果 JSON 字串
    """
    try:
        step = Step.objects.prefetch_related("verifications").get(id=step_id)
    except Step.DoesNotExist:
        logger.error(f"[Resume] Step#{step_id} 不存在。")
        return {"ok": False, "error": "Step not found"}

    if step.status != "WAITING_FOR_ASYNC":
        logger.warning(f"[Resume] Step#{step_id} 狀態為 {step.status}，跳過回調。")
        return {"ok": False, "error": "Step is not in WAITING_FOR_ASYNC state"}

    logger.info(f"[Resume] 🔔 Step#{step_id} 回調喚醒，接收輸出并觸發驗證。")

    verifications = list(step.verifications.all())
    _save_execution_output(step, verifications, task_output)

    step.status = "COMPLETED"
    step.note = (step.note or "") + f"\n[{timezone.now().isoformat()}] 異步工具回調完成，觸發驗證。"
    step.save(update_fields=["status", "note"])

    # 觸發所有 Verification 的驗證引擎
    from apps.auto.tasks.evaluation.engine import process_verification
    for v in verifications:
        process_verification.delay(v.id)

    return {"ok": True, "step_id": step_id, "verifications_triggered": len(verifications)}


# ──────────────────────────────────────────────────
# 私有輔助函數
# ──────────────────────────────────────────────────

def _build_asset_context(step: "Step") -> str:
    """組裝 Step 關聯的資產上下文 (IP, Subdomain, URLResult)，以 JSON 字串返回。"""
    context = {}

    ips = list(step.ip.values("id", "address", "version"))
    if ips:
        context["ips"] = ips

    subdomains = list(step.subdomain.values("id", "name", "is_active", "is_resolvable"))
    if subdomains:
        context["subdomains"] = subdomains

    urls = list(step.url_result.values("id", "url", "status_code", "title"))
    if urls:
        context["urls"] = urls

    return json.dumps(context, ensure_ascii=False, indent=2)


def _save_execution_output(step: "Step", verifications: list, output: str) -> None:
    """將執行輸出回寫到所有關聯的 Verification 記錄。"""
    Verification.objects.filter(step=step).update(execution_output=output)
    logger.debug(
        f"[StepRunner] Step#{step.id} 執行輸出已寫入 {len(verifications)} 個驗證記錄。"
    )


def _run_automation_agent(step: "Step", asset_context: str, verification_info: list) -> dict:
    """
    驅動 AutomationAgent 執行 Step。

    回傳格式:
        {"type": "sync_done",       "output": "...命令輸出..."}
        {"type": "async_dispatched","dispatched_tool": "nuclei", "callback_step_id": step.id}
        {"type": "error",           "error": "...錯誤訊息..."}
    """
    try:
        from apps.auto.cai.core.agent import run_agent
        from apps.auto.cai.agent_configs import AUTOMATION_AGENT_CONFIG

        # 組裝給 Agent 的 Prompt
        system_prompt = AUTOMATION_AGENT_CONFIG["instructions"]
        user_prompt = _build_execution_prompt(step, asset_context, verification_info)

        # 運行 AI Agent (同步執行，內部調用 function_tool)
        agent_result = run_agent(
            config=AUTOMATION_AGENT_CONFIG,
            user_message=user_prompt,
            system_message=system_prompt,
        )
        return agent_result

    except Exception as e:
        logger.exception(f"[StepRunner] AutomationAgent 執行異常: {e}")
        return {"type": "error", "error": str(e)}


def _build_execution_prompt(step: "Step", asset_context: str, verification_info: list) -> str:
    """組裝傳給 AutomationAgent 的完整 Prompt。"""
    verif_desc = json.dumps(verification_info, ensure_ascii=False, indent=2)
    return f"""## 自動化步驟執行任務

### Step 資訊
- ID: {step.id}
- 執行命令: `{step.command_template}`
- 預期結果: {step.expectation or '(無預期描述)'}
- 背景筆記: {step.note or '(無)'}

### 資產上下文 (GraphQL 快照)
```json
{asset_context}
```

### 驗證條件
```json
{verif_desc}
```

## 你的任務
請根據上述資訊，選擇最合適的方式執行這個 Step：

1. **如果是 CLI 指令** (nmap, nuclei, curl 等)：
   - 使用 `generic_linux_command` 真實執行它。
   - 根據輸出撰寫分析，決定是否有漏洞跡象。
   - 回傳格式: `{{"type": "sync_done", "output": "命令輸出...", "analysis": "你的分析..."}}`

2. **如果應交由系統異步工具處理** (大規模掃描任務等)：
   - 調用對應的系統 API 工具，並在參數中帶上 `callback_step_id={step.id}`。
   - 回傳格式: `{{"type": "async_dispatched", "dispatched_tool": "工具名稱", "callback_step_id": {step.id}}}`

3. **如果需要更多資產資訊**：
   - 先用 `query_graphql` 或相關工具查詢你需要的資訊。
   - 再決定如何執行。

你也可以更新筆記 (透過 `mutate_graphql` 更新 Step.note 欄位) 記錄關鍵發現。
"""
