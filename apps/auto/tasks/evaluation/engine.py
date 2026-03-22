"""
apps/auto/tasks/evaluation/engine.py

AI 驗證引擎 (VerificationEngine)
──────────────────────────────────────
核心職責:
  1. 接收 Verification.id，使用 AI 判斷執行輸出是否達成成功標準
  2. 驗證通過後，若 auto_create_vulnerability=True，自動建立 Vulnerability 記錄
  3. 所有 Step 完成後，觸發下一輪 AIAnalysis 推動 Continuous Loop

設計原則:
  - 純 AI 判斷，不做正則/字串比對
  - 強制 JSON 輸出，避免 AI 自由發揮造成解析失敗
  - Vulnerability 建立後關聯回 Verification.created_vulnerability
"""

import json
import hashlib
import logging
import requests
from typing import Optional

from celery import shared_task
from django.utils import timezone

from apps.core.models import Verification, Vulnerability

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# AI 驗證 System Prompt
# ──────────────────────────────────────────────────

VERIFICATION_SYSTEM_PROMPT = """你是一個專業的資安測試驗證引擎。

## 你的任務
根據「成功標準」判斷工具的實際輸出是否達成預期結果。

## 成功標準
{observation_prompt}

## 工具實際輸出
{execution_output}

請仔細分析後，嚴格以 JSON 格式回覆，絕對不可包含其他 markdown 標籤或說明文字：
{{
  "verified": true 或 false,
  "confidence": 0 到 100 的整數（你對判斷的確信度）,
  "reason": "簡短說明為什麼達成或未達成標準",
  "evidence": "從輸出中擷取的關鍵證據片段（若未通過則留空）"
}}"""


# ──────────────────────────────────────────────────
# Celery 任務: 處理驗證結果
# ──────────────────────────────────────────────────

@shared_task(name="auto.tasks.evaluation.process_verification")
def process_verification(verification_id: int) -> dict:
    """
    【AI 驗證任務】接收 Verification.id，送交 AI 判斷是否達成觀察標準。

    若驗證通過且 auto_create_vulnerability=True，自動建立 Vulnerability。
    """
    try:
        v = Verification.objects.select_related(
            "step", "created_vulnerability"
        ).get(id=verification_id)
    except Verification.DoesNotExist:
        logger.error(f"[VerificationEngine] Verification#{verification_id} 不存在。")
        return {"ok": False, "error": "Verification not found"}

    if v.verdict != "PENDING":
        logger.info(
            f"[VerificationEngine] Verification#{verification_id} 已有結果 ({v.verdict})，跳過。"
        )
        return {"ok": True, "verdict": v.verdict, "skipped": True}

    output = v.execution_output or ""
    logger.info(
        f"[VerificationEngine] 🔍 AI 判斷 Verification#{verification_id} "
        f"(Step#{v.step_id})"
    )

    # ── 呼叫 AI 判斷 ──────────────────────────────
    ai_result = _run_ai_judge(v.observation_prompt, output)
    verified = ai_result.get("verified", False)
    confidence = ai_result.get("confidence", 0)
    reason = ai_result.get("reason", "")
    evidence = ai_result.get("evidence", "")

    # ── 判斷最終結果 ──────────────────────────────
    passes = verified and (confidence >= v.confidence_threshold)
    verdict = "PASSED" if passes else ("INCONCLUSIVE" if not verified and confidence < 30 else "FAILED")

    _update_verification(v, verdict=verdict, reason=reason, confidence=confidence, ai_response=ai_result)

    logger.info(
        f"[VerificationEngine] {'✅ 通過' if passes else '❌ 未通過'} "
        f"Verification#{verification_id} → {verdict} (信心: {confidence}%)"
    )

    # ── 自動建立漏洞 ──────────────────────────────
    if passes and v.auto_create_vulnerability:
        vuln = _create_vulnerability(v, reason, evidence)
        if vuln:
            v.created_vulnerability = vuln
            v.save(update_fields=["created_vulnerability"])
            logger.info(
                f"[VerificationEngine] 🚨 Vulnerability#{vuln.id} 已建立 "
                f"(名稱: {vuln.name}, 嚴重度: {vuln.severity})"
            )
            _check_and_trigger_continuation(v.step)
            return {
                "ok": True,
                "verdict": verdict,
                "vulnerability_id": vuln.id,
                "vulnerability_name": vuln.name,
            }

    # ── 自動接續邏輯 ──────────────────────────────
    _check_and_trigger_continuation(v.step)

    return {
        "ok": True,
        "verdict": verdict,
        "reason": reason,
        "confidence": confidence,
        "evidence": evidence,
    }


def _check_and_trigger_continuation(step: "Step") -> None:
    """
    檢查該 Step 是否所有驗證都已完成，若是，推動 Continuous Loop。
    僅使用 Overview-based 路徑，不再有舊版 Target 反向查詢。
    """
    # 1. 檢查是否還有 PENDING 的驗證
    if Verification.objects.filter(step=step, verdict="PENDING").exists():
        logger.debug(
            f"[VerificationEngine] Step#{step.id} 還有驗證在進行中，暫不接續。"
        )
        return

    logger.info(f"[VerificationEngine] Step#{step.id} 所有驗證已完成，推動後續流程。")

    if not step.overview_id:
        logger.warning(
            f"[VerificationEngine] Step#{step.id} 沒有關聯的 Overview，"
            f"無法自動接續。請手動觸發下一步。"
        )
        return

    from apps.core.models import Step as StepModel

    # 2. 尋找下一個 PENDING Step
    next_step = StepModel.objects.filter(
        overview=step.overview,
        status="PENDING",
        order__gt=step.order
    ).order_by("order").first()

    if next_step:
        logger.info(
            f"[VerificationEngine] 發現下一步 Step#{next_step.id} "
            f"(Order: {next_step.order})，觸發執行。"
        )
        from apps.auto.tasks.execution.runner import run_step_execution
        run_step_execution.delay(next_step.id)
    else:
        # 無更多步驟 → 觸發 Continuous Planning
        logger.info(
            f"[VerificationEngine] Overview#{step.overview_id} 所有步驟已完成，"
            f"觸發新一輪 AI 分析。"
        )
        # 這裡不再手動建立分析，而是交給 Planning 決定是否需要更多分析
        from apps.analyze_ai.tasks.planning import propose_next_steps
        propose_next_steps.delay(step.overview_id)


def _create_next_ai_analysis(step: "Step") -> None:
    """
    Continuous Loop: 建立下一輪 AI 分析記錄，將控制權交回給規劃引擎。
    """
    from apps.core.models import IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis

    if step.ip.exists():
        analysis = IPAIAnalysis.objects.create(
            ip=step.ip.first(),
            overview=step.overview,
            triggered_by_step=step,
            status="PENDING"
        )
        logger.info(f"[VerificationEngine] 建立 IPAIAnalysis#{analysis.id} 等待下一輪分析。")

    elif step.subdomain.exists():
        analysis = SubdomainAIAnalysis.objects.create(
            subdomain=step.subdomain.first(),
            overview=step.overview,
            triggered_by_step=step,
            status="PENDING"
        )
        logger.info(f"[VerificationEngine] 建立 SubdomainAIAnalysis#{analysis.id} 等待下一輪分析。")

    elif step.url_result.exists():
        analysis = URLAIAnalysis.objects.create(
            url_result=step.url_result.first(),
            overview=step.overview,
            triggered_by_step=step,
            status="PENDING"
        )
        logger.info(f"[VerificationEngine] 建立 URLAIAnalysis#{analysis.id} 等待下一輪分析。")

    else:
        logger.warning(
            f"[VerificationEngine] Step#{step.id} 無關聯資產，無法建立下一輪分析。"
        )


# ──────────────────────────────────────────────────
# AI 判斷引擎
# ──────────────────────────────────────────────────

def _run_ai_judge(observation_prompt: Optional[str], execution_output: str) -> dict:
    """
    AI 判斷：將觀察標準與輸出送給 AI，獲取結構化 JSON 判斷。
    強制 JSON 輸出，避免自由格式。
    """
    import os

    if not observation_prompt:
        return {
            "verified": False, "confidence": 0,
            "reason": "observation_prompt 為空，無法驗證",
            "evidence": ""
        }
    if not execution_output.strip():
        return {
            "verified": False, "confidence": 0,
            "reason": "execution_output 為空，工具未產生輸出",
            "evidence": ""
        }

    prompt = VERIFICATION_SYSTEM_PROMPT.format(
        observation_prompt=observation_prompt,
        execution_output=execution_output[:4000]  # 防止超長輸出
    )

    try:
        from c2_core.config.config import Config
        ai_url = Config.get("gemini_json_ai") or os.getenv("AI_API_URL")
        if not ai_url:
            logger.error("[VerificationEngine] 未設定 AI API URL。")
            return {
                "verified": False, "confidence": 0,
                "reason": "AI API 未設定", "evidence": ""
            }

        resp = requests.post(
            ai_url,
            json={"messages": [{"role": "user", "content": prompt}]},
            timeout=60
        )
        resp.raise_for_status()
        raw = resp.json()

        content = raw.get("content") or raw.get("text") or str(raw)
        # 清理可能的 markdown code block
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip().strip("```").strip()

        result = json.loads(content)

        if "verified" not in result:
            raise ValueError("AI 回應缺少 'verified' 欄位")

        # 確保必要欄位存在
        result.setdefault("confidence", 0)
        result.setdefault("reason", "")
        result.setdefault("evidence", "")

        return result

    except json.JSONDecodeError as e:
        logger.error(
            f"[VerificationEngine] AI 回應 JSON 解析失敗: {e}"
        )
        return {
            "verified": False, "confidence": 0,
            "reason": f"AI 回應格式錯誤: {e}", "evidence": ""
        }
    except Exception as e:
        logger.exception(f"[VerificationEngine] AI 判斷請求失敗: {e}")
        return {
            "verified": False, "confidence": 0,
            "reason": f"AI 請求失敗: {e}", "evidence": ""
        }


# ──────────────────────────────────────────────────
# 漏洞建立引擎
# ──────────────────────────────────────────────────

def _create_vulnerability(
    v: "Verification", reason: str, evidence: str
) -> Optional["Vulnerability"]:
    """
    根據 AI 驗證結果自動建立 Vulnerability 記錄。
    使用 fingerprint 避免重複建立。
    """
    step = v.step
    vuln_name = v.vulnerability_name or f"Step#{step.id} AI 驗證通過的潛在漏洞"
    severity = v.vulnerability_severity or "medium"

    ip_asset = step.ip.first()
    subdomain_asset = step.subdomain.first()
    url_asset = step.url_result.first()

    matched_at = (
        url_asset.url if url_asset
        else subdomain_asset.name if subdomain_asset
        else ip_asset.ipv4 if ip_asset
        else f"step_{step.id}"
    )

    template_id = v.vulnerability_name or f"auto-step-{step.id}"
    fingerprint = hashlib.sha256(
        f"{template_id}::{matched_at}".encode()
    ).hexdigest()

    # 防重複
    existing = Vulnerability.objects.filter(fingerprint=fingerprint).first()
    if existing:
        logger.info(
            f"[VerificationEngine] 漏洞指紋已存在 ({fingerprint[:16]}...)，更新 last_seen。"
        )
        existing.last_seen = timezone.now()
        existing.save(update_fields=["last_seen"])
        return existing

    description = (
        f"由 Step#{step.id} AI 驗證通過自動建立。\n"
        f"驗證理由: {reason}\n"
        f"關鍵證據: {evidence}"
    )

    return Vulnerability.objects.create(
        ip_asset=ip_asset,
        subdomain_asset=subdomain_asset,
        url_asset=url_asset,
        name=vuln_name,
        severity=severity,
        tool_source="auto_ai_verification",
        template_id=template_id,
        matched_at=matched_at,
        fingerprint=fingerprint,
        description=description,
        status="confirmed",
    )


def _update_verification(
    v: "Verification",
    verdict: str,
    reason: str,
    confidence: int = 0,
    ai_response: Optional[dict] = None,
) -> None:
    """回寫驗證結果到資料庫，並在 Step.note 中留下紀錄。"""
    v.verdict = verdict
    v.confidence_score = confidence
    v.verified_at = timezone.now()
    if ai_response:
        v.ai_response = ai_response

    v.step.note = (
        (v.step.note or "")
        + f"\n[Verification#{v.id}] {verdict} (信心:{confidence}%): {reason}"
    )
    v.step.save(update_fields=["note"])
    v.save(update_fields=["verdict", "confidence_score", "verified_at", "ai_response"])
