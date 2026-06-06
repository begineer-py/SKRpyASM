"""
AI Agent 自動發現登記表

原理：掃描已知的 agent 套件，收集所有定義了 assistant_id 的類別，
以及 get_llm_instance(agent_id=...) 工具類（無 AIAssistant 基類）。

新增 agent 方式（自動被前端發現，無需手動修改清單）：
  - 在 apps.ai_assistant / apps.analyze_ai / apps.auto.assistants 下
    定義含有 `assistant_id = "your_agent_id"` 的類別即可。

回退清單（非 AIAssistant 子類，但直接使用 get_llm_instance(agent_id=...)）：
  - 在 _UTILITY_AGENT_IDS 中補充即可。
"""

import importlib
import inspect
import logging
import pkgutil

logger = logging.getLogger(__name__)

# 非 AIAssistant 子類別、直接以 agent_id 呼叫 get_llm_instance() 的工具 agent
# 新增工具 agent 時在此補一行即可
_UTILITY_AGENT_IDS: list[str] = [
    "skill_verifier_agent",
    "skill_merger_evaluator_agent",
    "compression_agent",
]

# 要掃描的套件（這些套件下所有模組都會被掃描）
_SCAN_PACKAGES: list[str] = [
    "apps.ai_assistant",
    "apps.analyze_ai",
    "apps.auto.assistants",
]


def _scan_module(module_path: str, found: set[str]) -> None:
    """掃描單個模組，收集所有定義了 id 屬性（字串）的 AIAssistant 子類。
    django_ai_assistant 框架使用 `id` 作為 agent 識別符。
    """
    try:
        module = importlib.import_module(module_path)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # 只收集定義在此模組的類別（過濾 import 進來的類別）
            if obj.__module__ != module_path:
                continue
            aid = getattr(obj, "id", None)
            if aid and isinstance(aid, str):
                found.add(aid)
    except Exception as e:
        logger.debug(f"agent_registry: 掃描模組 {module_path} 失敗: {e}")


def _scan_packages() -> set[str]:
    """遞迴掃描 _SCAN_PACKAGES 中所有子模組，收集 assistant_id。"""
    found: set[str] = set()
    for pkg_name in _SCAN_PACKAGES:
        try:
            pkg = importlib.import_module(pkg_name)
            pkg_path = getattr(pkg, "__path__", None)
            if pkg_path:
                for _, modname, _ in pkgutil.walk_packages(
                    path=pkg_path,
                    prefix=pkg.__name__ + ".",
                    onerror=lambda x: None,
                ):
                    _scan_module(modname, found)
            # 也掃描套件本身的 __init__.py / 模組本身
            _scan_module(pkg_name, found)
        except Exception as e:
            logger.debug(f"agent_registry: 掃描套件 {pkg_name} 失敗: {e}")
    return found


def discover_agent_ids() -> list[str]:
    """
    返回系統中所有已知 agent 的 agent_id 清單（已排序）。

    資料來源（兩層，取聯集）：
      1. 掃描 _SCAN_PACKAGES 中含有 assistant_id 的類別（自動發現）
      2. _UTILITY_AGENT_IDS 清單（無 AIAssistant 基類的工具 agent）

    新增 AIAssistant 子類並設定 assistant_id → 自動出現在前端。
    新增工具 agent → 在 _UTILITY_AGENT_IDS 補一行。
    不依賴 env var，不依賴 settings.py。
    """
    discovered = _scan_packages()
    all_ids = discovered | set(_UTILITY_AGENT_IDS)
    result = sorted(all_ids)
    logger.debug(f"agent_registry: 發現 {len(result)} 個 agent: {result}")
    return result
