"""
auto/tasks/start/common.py

通用 Step 建立引擎：將 AI 的 command_actions 拆解為 Step / Method / Payload / Verification。

=== 四欄位對應 ===
    Step         → 第幾步 (order) + 真實執行指令 (command_template)
    Method       → 什麼方法發送 (e.g., nmap, nuclei, curl, sqlmap)
    Payload      → 完整 action JSON 內容
    Verification → 驗證條件（pattern + match_type），
                   符合驗證 → 未來自動加入漏洞模組
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.core.models import Step, Method, Payload, Verification

logger = logging.getLogger(__name__)


# =============================================================================
# 工具自動偵測（正則匹配命令中的工具名稱）
# =============================================================================

TOOL_PATTERNS = {
    "nmap": re.compile(r"\bnmap\b", re.IGNORECASE),
    "nuclei": re.compile(r"\bnuclei\b", re.IGNORECASE),
    "sqlmap": re.compile(r"\bsqlmap\b", re.IGNORECASE),
    "hydra": re.compile(r"\bhydra\b", re.IGNORECASE),
    "curl": re.compile(r"\bcurl\b", re.IGNORECASE),
    "nikto": re.compile(r"\bnikto\b", re.IGNORECASE),
    "ffuf": re.compile(r"\bffuf\b", re.IGNORECASE),
    "gobuster": re.compile(r"\bgobuster\b", re.IGNORECASE),
    "wfuzz": re.compile(r"\bwfuzz\b", re.IGNORECASE),
    "dig": re.compile(r"\bdig\b", re.IGNORECASE),
    "subfinder": re.compile(r"\bsubfinder\b", re.IGNORECASE),
    "amass": re.compile(r"\bamass\b", re.IGNORECASE),
    "whatweb": re.compile(r"\bwhatweb\b", re.IGNORECASE),
}

# 工具預設驗證模式（僅作為 fallback，prompt 已要求 AI 提供 verification）
DEFAULT_VERIFICATION = {
    "nmap": {"pattern": "open", "match_type": "contains"},
    "nuclei": {"pattern": "\\[.*\\]", "match_type": "regex"},
    "sqlmap": {"pattern": "injectable|vulnerable", "match_type": "regex"},
    "hydra": {"pattern": "login:|password:", "match_type": "regex"},
    "nikto": {"pattern": "OSVDB-|\\+ ", "match_type": "regex"},
    "curl": {"pattern": "HTTP/", "match_type": "contains"},
}


def _detect_method(command_str: str) -> str:
    """從命令字串中自動偵測工具名稱，例如 'nmap -sV ...' → 'nmap'"""
    for tool_name, pattern in TOOL_PATTERNS.items():
        if pattern.search(command_str):
            return tool_name
    return "shell_command"


def _normalize_action(raw_action: Any) -> Dict[str, Any]:
    """
    將不同格式的 command_action 統一為標準 dict：
    {
        "command": "真實執行指令",
        "method": "工具名稱",
        "description": "描述",
        "verification": {"pattern": "...", "match_type": "..."},
    }

    支援的輸入：
    - str:  "nmap -sV -p 80 1.2.3.4"（舊資料相容）
    - dict: {"command": "...", "method": "...", "description": "...", "verification": {...}}
    """
    if isinstance(raw_action, str):
        method = _detect_method(raw_action)
        return {
            "command": raw_action,
            "method": method,
            "description": "",
            "verification": DEFAULT_VERIFICATION.get(method),
        }

    if isinstance(raw_action, dict):
        cmd = raw_action.get("command", raw_action.get("cmd", str(raw_action)))
        method = raw_action.get("method", raw_action.get("type", _detect_method(cmd)))

        # 取得 AI 提供的 verification（新格式）
        verification = raw_action.get("verification")
        if not verification:
            # 退回使用預設驗證
            verification = DEFAULT_VERIFICATION.get(method)

        return {
            "command": cmd,
            "method": method,
            "description": raw_action.get("description", raw_action.get("desc", "")),
            "verification": verification,
        }

    return {
        "command": str(raw_action),
        "method": "unknown",
        "description": "",
        "verification": None,
    }


def create_steps_from_analysis(
    *,
    command_actions: list,
    asset_fk_field: str,
    asset_fk_value: Any,
    analysis_id: int,
    analysis_summary: Optional[str],
    analysis_risk_score: Optional[int],
    potential_vulnerabilities: Optional[list],
    asset_context_json: str,
) -> int:
    """
    通用 Step 建立引擎：
    將 command_actions 列表轉換為 Step + Method + Payload + Verification。

    Args:
        command_actions:          AI 產出的動作列表
        asset_fk_field:           Step 的 FK 欄位名 ('ip' / 'subdomain' / 'url_result')
        asset_fk_value:           FK 指向的資產物件
        analysis_id:              來源分析記錄 ID
        analysis_summary:         AI 摘要
        analysis_risk_score:      AI 風險評分
        potential_vulnerabilities: AI 推斷的漏洞列表
        asset_context_json:       GraphQL 資產快照 JSON

    Returns:
        成功建立的 Step 數量
    """
    created = 0

    with transaction.atomic():
        for idx, raw_action in enumerate(command_actions, start=1):
            action = _normalize_action(raw_action)

            # ── Step: 第幾步 + 真實執行指令 ──────────────
            step = Step.objects.create(
                order=idx,
                command_template=action["command"],
                expectation=action.get("description", ""),
                note=(
                    f"來源: Analysis#{analysis_id}\n"
                    f"風險評分: {analysis_risk_score or 'N/A'}\n"
                    f"摘要: {analysis_summary or 'N/A'}\n"
                    f"---\n"
                    f"GraphQL 資產快照:\n{asset_context_json}"
                ),
                status="PENDING",
            )
            # ManyToMany fields require .add() after creation
            getattr(step, asset_fk_field).add(asset_fk_value)

            # ── Method: 什麼方法發送 ──────────────────
            Method.objects.create(
                step=step,
                name=action["method"],
                description=action.get("description", ""),
            )

            # ── Payload: 完整 action 內容 ──────────────
            Payload.objects.create(
                step=step,
                content=json.dumps(raw_action, ensure_ascii=False)
                    if not isinstance(raw_action, str) else raw_action,
                platform=action.get("method", "cli"),
            )

            # ── Verification: 驗證條件 ────────────────
            verification_data = action.get("verification")
            if verification_data and isinstance(verification_data, dict):
                Verification.objects.create(
                    step=step,
                    pattern=verification_data.get("pattern", ""),
                    match_type=verification_data.get("match_type", "contains"),
                    verify_strategy=verification_data.get("verify_strategy", "regex"),
                    ai_prompt=verification_data.get("ai_prompt", ""),
                    confidence_threshold=verification_data.get("confidence_threshold", 80),
                    auto_create_vulnerability=verification_data.get("auto_create_vulnerability", False),
                    vulnerability_severity=verification_data.get("vulnerability_severity", "medium"),
                    vulnerability_name=verification_data.get("vulnerability_name", ""),
                )

            created += 1

    return created
