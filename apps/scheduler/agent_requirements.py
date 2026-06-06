"""
定義哪些 Celery task 在執行時需要 AI API 密鑰，
並提供驗證函數供 scheduler API 在創建/更新任務前調用。

新增需要 AI 的 task 時，只需在 TASK_AGENT_REQUIREMENTS 中加入記錄即可。
"""

# 靜態映射：Celery task name → 所需資源
# agent_id: 使用 AutoAppConfig.get_agent_config() + LLM factory 的 agent
# provider:  直接使用特定 LLM provider（不走 agent framework，如 compress_long_threads）
TASK_AGENT_REQUIREMENTS: dict = {
    "scheduler.tasks.watchdog_stalled_overviews": {
        "agent_id": "automation_agent",
        "description": "需要 automation_agent 的 API 密鑰（用於偵測停滯任務並發送救援訊息 + 自動觸發策略規劃）",
    },
    "scheduler.tasks.cleanup_orphaned_assets": {
        "description": "清除沒有關聯 Target 的孤立資產（IP、Subdomain、URLResult、Overview）",
    },
    "analyze_ai.tasks.periodic_initial_analysis_bootstrapper": {
        "agent_id": "initial_analyzer_agent",
        "description": "需要 initial_analyzer_agent 的 API 密鑰（用於初步資產 AI 分析）",
    },
    "analyze_ai.tasks.planning.propose_next_steps": {
        "agent_id": "automation_agent",
        "description": "需要 automation_agent / StrategyAgent 的 API 密鑰（用於策略規劃）",
    },
    "apps.auto.tasks.auto_execute_plan": {
        "agent_id": "automation_agent",
        "description": "需要 automation_agent 的 API 密鑰（用於自動化滲透執行）",
    },
    "apps.auto.tasks.verify_skills_periodic": {
        "agent_id": "automation_agent",
        "description": "需要 automation_agent 的 API 密鑰（用於定期驗證技能）",
    },
    "apps.auto.tasks.evaluate_skill_merges": {
        "agent_id": "automation_agent",
        "description": "需要 automation_agent 的 API 密鑰（用於評估技能合併）",
    },
    "scheduler.tasks.trigger_scan_js": {
        "agent_id": "initial_analyzer_agent",
        "description": "需要 initial_analyzer_agent 的 API 密鑰（用於 JS AI 掃描）",
    },
}


def _has_key_for_agent(agent_id: str) -> bool:
    """
    Check agent API key availability:
      AgentLLMConfig.api_key_ref → AGENT_<ID>_API_KEY env → global provider key (DB + env)
    """
    try:
        from apps.auto.settings import AutoAppConfig
        from apps.api_keys.utils import get_ai_provider_key

        cfg = AutoAppConfig.get_agent_config(agent_id)

        # agent-specific key（DB ref 或 AGENT_<ID>_API_KEY env var）
        if cfg.get("api_key"):
            return True

        # 全域 provider key（DB APIKey 記錄 + env var fallback）
        provider = cfg.get("provider", "")
        return bool(provider and get_ai_provider_key(provider))
    except Exception:
        return False


def _has_key_for_provider(provider: str) -> bool:
    """Check if a global API key exists for the given provider (DB + env var)."""
    try:
        from apps.api_keys.utils import get_ai_provider_key
        return bool(get_ai_provider_key(provider))
    except Exception:
        return False


def check_task_api_requirements(task_name: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    is_valid=True → task can be created.
    is_valid=False → error_message explains what's missing.
    Tasks not in TASK_AGENT_REQUIREMENTS are always allowed.
    """
    req = TASK_AGENT_REQUIREMENTS.get(task_name)
    if not req:
        return True, ""

    description = req.get("description", "")

    if "agent_id" in req:
        agent_id = req["agent_id"]
        if not _has_key_for_agent(agent_id):
            return False, (
                f"無法創建定時任務：{description}。"
                f"請先在 /agent-config 為 '{agent_id}' 配置 API 密鑰，"
                f"或在 /api-keys 新增對應 provider 的全域密鑰。"
            )

    if "provider" in req:
        provider = req["provider"]
        if not _has_key_for_provider(provider):
            return False, (
                f"無法創建定時任務：{description}。"
                f"請先在 /api-keys 新增 '{provider}' 的 API 密鑰。"
            )

    return True, ""


def get_task_requirements_info(task_name: str) -> dict:
    """
    返回任務的 API 需求資訊供前端展示（GET /scheduler/task-requirements 端點使用）。
    """
    req = TASK_AGENT_REQUIREMENTS.get(task_name)
    if not req:
        return {
            "task": task_name,
            "requires_api": False,
            "agent_id": None,
            "provider": None,
            "has_key": True,
            "description": None,
            "missing_key_hint": None,
        }

    agent_id = req.get("agent_id")
    provider = req.get("provider")
    description = req.get("description")

    is_valid, error_msg = check_task_api_requirements(task_name)

    return {
        "task": task_name,
        "requires_api": True,
        "agent_id": agent_id,
        "provider": provider,
        "has_key": is_valid,
        "description": description,
        "missing_key_hint": None if is_valid else error_msg,
    }
