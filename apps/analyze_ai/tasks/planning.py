"""
apps/analyze_ai/tasks/planning.py

策略規劃引擎 (Planning Engine) - 遷移至 analyze_ai
──────────────────────────────────────
核心職責:
  1. 接收 overview_id，以 Overview 為中心分析當前資產、漏洞與歷史步驟。
  2. 驅動 StrategyAgent 撰寫下一步計畫。
  3. 將計畫保存到 Overview，交由 LangGraph execution runtime 執行。
"""

import json
import logging
from typing import Optional
from celery import shared_task
from django.db import transaction
from apps.core.models import Overview, AttackVector

logger = logging.getLogger(__name__)


@shared_task(name="analyze_ai.tasks.planning.propose_next_steps")
def propose_next_steps(overview_id: int) -> dict:
    """
    【策略規劃任務】以 Overview 為中心分析全貌，決定接下來的自動化步驟。
    鏈式流程：InitialAIAnalysis → (本任務) → auto_execute_plan
    """
    try:
        overview = Overview.objects.prefetch_related(
            "ips", "subdomains", "url_results", "attack_vectors"
        ).get(id=overview_id)
    except Overview.DoesNotExist:
        logger.error(f"[Planning] Overview#{overview_id} 不存在。")
        return {"ok": False, "error": "Overview not found"}

    # 防護：避免對已進入執行中或已完成的 Overview 重複規劃
    if overview.status in ("EXECUTING", "COMPLETED", "STALLED"):
        logger.warning(
            f"[Planning] Overview#{overview_id} 狀態為 {overview.status}，跳過重複規劃。"
        )
        return {"ok": False, "error": f"Overview status is {overview.status}, skip planning"}

    logger.info(f"[Planning] 🧠 開始為 Overview#{overview_id} 進行策略規劃...")

    overview.status = "PLANNING"
    overview.save(update_fields=["status", "updated_at"])

    # CAI strategy agent framework 尚未實作（apps.auto.cai.core 不存在）。
    # 直接將 Overview 推進到 EXECUTING，由 Layer 3 AutomationAgent 接管策略規劃與執行。
    logger.info(
        f"[Planning] CAI strategy agent not available — "
        f"advancing Overview#{overview_id} directly to EXECUTING"
    )
    overview.status = "EXECUTING"
    overview.save(update_fields=["status", "updated_at"])

    # 鏈式觸發：交給 Layer 3 執行
    from apps.auto.tasks import auto_execute_plan
    logger.info(f"[Chain] 策略規劃跳過，自動觸發 auto_execute_plan")
    auto_execute_plan.delay()

    return {"ok": True, "message": "Skipped CAI strategy agent, advanced to EXECUTING"}


def _build_global_context(overview: Overview) -> dict:
    ips = list(overview.ips.values("id", "address", "version"))
    subdomains = list(
        overview.subdomains.values("id", "name", "is_resolvable", "is_active")
    )
    url_results = list(overview.url_results.values("id", "url", "status_code", "title"))

    # 全部攻擊向量 (含已失敗的)
    attack_vectors = list(
        overview.attack_vectors.values(
            "id", "name", "vector_type", "status", "risk_score", "description"
        )
    )

    thread_ids = [value for value in [overview.thread_id, overview.parent_thread_id] if value]
    recent_executions_data = []
    execution_stats = {"total": 0, "succeeded": 0, "failed": 0, "running": 0, "waiting": 0}
    if thread_ids:
        from apps.core.models import ExecutionGraph

        graphs = list(
            ExecutionGraph.objects.filter(thread_id__in=thread_ids)
            .prefetch_related("nodes", "events")
            .order_by("-started_at")[:30]
        )
        execution_stats["total"] = len(graphs)
        for graph in graphs:
            key = graph.status.lower()
            if key in execution_stats:
                execution_stats[key] += 1
            latest_event = graph.events.order_by("-sequence").first()
            recent_executions_data.append(
                {
                    "id": graph.id,
                    "status": graph.status,
                    "assistant_id": graph.assistant_id,
                    "title": graph.title,
                    "nodes": [
                        {"id": node.id, "name": node.name, "status": node.status, "kind": node.kind}
                        for node in graph.nodes.order_by("sequence")[:10]
                    ],
                    "latest_event": {
                        "type": latest_event.event_type,
                        "status": latest_event.status,
                        "content": latest_event.content[:1000],
                    } if latest_event else None,
                }
            )

    return {
        "overview_summary": overview.summary,
        "overview_plan": overview.plan,
        "risk_score": overview.risk_score,
        "techs": overview.techs,
        "knowledge": overview.knowledge,
        "ips": ips,
        "subdomains": subdomains,
        "url_results": url_results,
        "attack_vectors": attack_vectors,
        "execution_stats": execution_stats,
        "recent_history": recent_executions_data,
    }


def _build_strategy_prompt(overview: Overview, context: dict) -> str:
    return f"""你是一個資深滲透測試專家 (Strategic Planning Agent)。
你的任務是分析當前目標的所有情報，制定下一步的攻擊計畫。

## 任務背景 (Strategic Overview)
- **ID**: {overview.id}
- **目標摘要**: {overview.summary or '尚未提供'}
- **當前計畫**: {overview.plan or '尚未制定'}
- **已檢測技術棧**: {json.dumps(overview.techs, ensure_ascii=False) if overview.techs else '未知'}
- **現有知識庫**: {json.dumps(overview.knowledge, ensure_ascii=False) if overview.knowledge else '空白'}

## 當前環境情報 (Context)
```json
{json.dumps(context, indent=2, ensure_ascii=False)}
```

## 指揮原則
1. **分析歷史失敗**: 仔細檢查 `recent_history` 與 `attack_vectors`。如果某個 Status 為 `EXHAUSTED` 或最近的 execution/node 為 `FAILED`，代表該路徑可能已封死。不要重複執行失敗的指令。
2. **優先權排序**: 優先驗證高風險 (High Risk) 的 `AttackVector`。如果發現新資產，先進行初步探查。
3. **動態更新**: 如果你從歷史輸出中發現了新的技術 (tech) 或關鍵知識 (knowledge)，請在回傳中包含 `updated_techs` 與 `updated_knowledge`。
4. **具體指令**: 產出的 `command_actions` 必須是真實、可執行的 CLI 指令。

## 回傳格式 (JSON)
{{
  "analysis": "你對當前局勢的詳細評估與下一步邏輯推理...",
  "updated_techs": ["Nginx", "PHP 7.4", "..."],
  "updated_knowledge": {{ "key_finding": "描述發現..." }},
  "command_actions": [
    {{
      "command": "nmap -sV -p 80 1.2.3.4",
      "description": "為什麼要做這一步",
      "requires_verification": false, 
      "observation_prompt": "成功的判斷標準 (若是情報收集如nmap/subfinder，requires_verification設為false，本欄可留空)",
      "asset_type": "ip",
      "asset_id": 123  // 警告：請務必從上方 Context 中的 ips/subdomains/urls 陣列尋找真實存在的 ID，嚴禁憑空捏造！
    }}
  ]
}}
"""


