"""
apps/analyze_ai/tasks/planning.py

策略規劃引擎 (Planning Engine) - 遷移至 analyze_ai
──────────────────────────────────────
核心職責:
  1. 接收 overview_id，以 Overview 為中心分析當前資產、漏洞與歷史步驟。
  2. 驅動 StrategyAgent 撰寫下一步計畫。
  3. 將計畫轉換為可執行的 Step 記錄。
"""

import json
import logging
from typing import Optional
from celery import shared_task
from django.db import transaction
from apps.core.models import Overview, AttackVector, Step

logger = logging.getLogger(__name__)


@shared_task(name="analyze_ai.tasks.planning.propose_next_steps")
def propose_next_steps(overview_id: int) -> dict:
    """
    【策略規劃任務】以 Overview 為中心分析全貌，決定接下來的自動化步驟。
    """
    try:
        overview = Overview.objects.prefetch_related(
            "ips", "subdomains", "url_results", "steps", "attack_vectors"
        ).get(id=overview_id)
    except Overview.DoesNotExist:
        logger.error(f"[Planning] Overview#{overview_id} 不存在。")
        return {"ok": False, "error": "Overview not found"}

    logger.info(f"[Planning] 🧠 開始為 Overview#{overview_id} 進行策略規劃...")

    overview.status = "PLANNING"
    overview.save(update_fields=["status", "updated_at"])

    context = _build_global_context(overview)
    user_prompt = _build_strategy_prompt(overview, context)

    try:
        from apps.auto.cai.core.agent import run_agent
        from apps.auto.cai.agent_configs import STRATEGY_AGENT_CONFIG

        result = run_agent(
            config=STRATEGY_AGENT_CONFIG,
            user_message=user_prompt,
            system_message=STRATEGY_AGENT_CONFIG["instructions"],
        )

        actions = result.get("command_actions", [])
        if not actions:
            logger.info(f"[Planning] AI 未建議更多步驟（Overview#{overview_id}）。")
            overview.status = "COMPLETED"
            overview.plan = result.get("analysis", "AI 判斷此階段已完成。")
            overview.save(update_fields=["status", "plan", "updated_at"])
            return {
                "ok": True,
                "message": "No more steps proposed",
                "analysis": overview.plan,
            }

        overview.plan = result.get("analysis", "")
        overview.status = "EXECUTING"

        # --- 自動更新 Overview 知識庫 (新增) ---
        new_knowledge = result.get("updated_knowledge")
        if new_knowledge and isinstance(new_knowledge, dict):
            knowledge = overview.knowledge or {}
            knowledge.update(new_knowledge)
            overview.knowledge = knowledge

        new_techs = result.get("updated_techs")
        if new_techs and isinstance(new_techs, list):
            techs = overview.techs or []
            # 合併去重
            techs = list(set(techs + new_techs))
            overview.techs = techs

        overview.save(
            update_fields=["plan", "status", "knowledge", "techs", "updated_at"]
        )

        created_count = _create_steps_from_planning(overview, actions)

        logger.info(
            f"[Planning] ✅ Overview#{overview_id} 建立 {created_count} 個新步驟，"
            f"觸發執行第一步。"
        )

        _trigger_first_pending_step(overview)
        return {"ok": True, "created_count": created_count}

    except Exception as e:
        logger.exception(f"[Planning] 執行異常: {e}")
        overview.status = "STALLED"
        overview.save(update_fields=["status", "updated_at"])
        return {"ok": False, "error": str(e)}


def _build_global_context(overview: Overview) -> dict:
    ips = list(overview.ips.values("id", "ipv4", "ipv6"))
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

    # 歷史執行步驟（最近 30 個）
    # 包含步驟的 Note 以及最近一筆 Verification 的結果
    recent_steps_data = []
    for st in overview.steps.order_by("-id")[:30]:
        last_verif = st.verifications.order_by("-id").first()
        recent_steps_data.append(
            {
                "id": st.id,
                "order": st.order,
                "command": st.command_template,
                "status": st.status,
                "expectation": st.expectation,
                "note": st.note,
                "verification": (
                    {
                        "verdict": last_verif.verdict if last_verif else "NONE",
                        "ai_reason": (
                            last_verif.ai_response.get("reason", "")
                            if last_verif and last_verif.ai_response
                            else ""
                        ),
                    }
                    if last_verif
                    else None
                ),
            }
        )

    step_stats = {
        "total": overview.steps.count(),
        "completed": overview.steps.filter(status="COMPLETED").count(),
        "failed": overview.steps.filter(status="FAILED").count(),
        "pending": overview.steps.filter(status="PENDING").count(),
    }

    # 蒐集深度分析結果 (AI 的初步判斷)
    ip_analyses = list(
        overview.ip_analyses.filter(status="COMPLETED").values(
            "id",
            "ip_id",
            "summary",
            "port_analysis_summary",
            "potential_vulnerabilities",
        )
    )
    subdomain_analyses = list(
        overview.subdomain_analyses.filter(status="COMPLETED").values(
            "id",
            "subdomain_id",
            "summary",
            "tech_stack_summary",
            "potential_vulnerabilities",
        )
    )
    url_analyses = list(
        overview.url_analyses.filter(status="COMPLETED").values(
            "id", "url_result_id", "summary", "potential_vulnerabilities"
        )
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
        "step_stats": step_stats,
        "recent_history": recent_steps_data,
        "deep_analysis_findings": {
            "ip": ip_analyses,
            "subdomain": subdomain_analyses,
            "url": url_analyses,
        },
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
1. **分析歷史失敗**: 仔細檢查 `recent_history` 與 `attack_vectors`。如果某個 Status 為 `EXHAUSTED` 或最近的 Step Verdict 為 `FAILED`，代表該路徑可能已封死。不要重複執行失敗的指令。
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
      "observation_prompt": "成功的判斷標準",
      "asset_type": "ip",
      "asset_id": 1
    }}
  ]
}}
"""


def _create_steps_from_planning(overview: Overview, actions: list) -> int:
    from apps.auto.tasks.start.common import create_steps_from_analysis
    from apps.core.models import IP, Subdomain, URLResult

    count = 0
    for action in actions:
        asset_type = action.get("asset_type")
        asset_id = action.get("asset_id")
        asset_obj = None
        asset_fk_field = ""
        if asset_type == "ip":
            asset_obj = IP.objects.filter(id=asset_id).first()
            asset_fk_field = "ip"
        elif asset_type == "subdomain":
            asset_obj = Subdomain.objects.filter(id=asset_id).first()
            asset_fk_field = "subdomain"
        elif asset_type == "url":
            asset_obj = URLResult.objects.filter(id=asset_id).first()
            asset_fk_field = "url_result"

        if not asset_obj:
            continue

        created = create_steps_from_analysis(
            command_actions=[action],
            asset_fk_field=asset_fk_field,
            asset_fk_value=asset_obj,
            analysis_id=0,
            analysis_summary=action.get("description", "由 StrategyAgent 自動規劃"),
            analysis_risk_score=overview.risk_score,
            potential_vulnerabilities=[],
            asset_context_json="{}",
            overview=overview,
        )
        count += created
    return count


def _trigger_first_pending_step(overview: Overview) -> None:
    first_step = (
        Step.objects.filter(overview=overview, status="PENDING")
        .order_by("order")
        .first()
    )
    if first_step:
        from apps.auto.tasks.execution.runner import run_step_execution

        run_step_execution.delay(first_step.id)
