"""
VerificationService: Mission-level PoC 審查服務（LLM-as-judge gate）。

用途：攔截 Overview.status -> COMPLETED 的企圖，審查是否「真的完成」。
  - 蒐集 Overview 下所有 Vulnerability / AttackVector / 掃描覆蓋率
  - 送 LLM 評估 verdict (APPROVED/REJECTED/INCONCLUSIVE)
  - REJECTED 退回 EXECUTING 並注入駁回理由到 thread（由呼叫端處理）
  - INCONCLUSIVE 放行但標記 needs_human_review
  - APPROVED 正常允許 COMPLETED

參考設計：apps/auto/skill_verifier.py（Pydantic structured output + LLM-as-judge）
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from apps.ai_assistant.prompts import PromptSpec, TaskDefinition

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# Structured output schemas
# ════════════════════════════════════════════════════════════════════


class MissionEvalOutput(BaseModel):
    """LLM 審查輸出的結構化 schema。"""

    verdict: str = Field(
        description="驗證裁決：APPROVED（可完成）/ REJECTED（應退回）/ INCONCLUSIVE（無法判定）"
    )
    confidence: int = Field(description="信心分數 0-100", ge=0, le=100)
    reasoning: str = Field(description="詳細分析（繁體中文）")
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="具體駁回點，例如「無任何 confirmed 漏洞」、「PoC 缺失」、「掃描覆蓋率 <50%」",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="建議 agent 採取的改善動作（繁體中文）",
    )


# ════════════════════════════════════════════════════════════════════
# Prompt
# ════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════
# PromptSpec 宣告（取代原本的字串常數）
# ════════════════════════════════════════════════════════════════════

MISSION_REVIEW_SPEC = PromptSpec(
    name="VerificationAgent-MissionReview",
    role="獨立的滲透測試審查員（VerificationAgent）",
    task=TaskDefinition(
        goal="判斷一個 mission 是否「真的完成」，避免 agent 過早宣告完成（early stop）。",
        background=(
            "AutomationAgent 已執行任務並想標記 Overview 為 COMPLETED；"
            "本審查作為放行前的獨立門檻，確認調查充分且證據完整。"
        ),
        materials=(
            "target_name、target_description、mission_summary、mission_plan、risk_score、"
            "各類計數（vuln_count/confirmed_vuln_count/high_severity_count/poc_count/"
            "vector_count/exploitable_vector_count）、覆蓋率（subdomain/port/url/vuln_scan/overall）"
            "百分比、vuln_details（漏洞明細）。"
        ),
        boundary=(
            "1. APPROVED 需滿足任一：覆蓋率 ≥50% 且無遺漏；≥1 confirmed 漏洞；"
            "或充分測試後（覆蓋率 ≥70% 且無 EXPLOITABLE 向量）確實無漏洞。\n"
            "2. REJECTED（硬性規則）：high/critical 漏洞無 PoC 證據；"
            "confirmed=0 且覆蓋率 <50%；資產大量未掃描（<30%）；"
            "顯而易見的偵察未完成（子域名為 0 / 端口為 0）。\n"
            "3. INCONCLUSIVE：模糊情況（介於兩者之間、覆蓋率中等 30-50%、PoC 不完整）。\n"
            "4. 輸出合法 JSON，不要 markdown code block。"
        ),
        dod=(
            "回傳含 verdict（APPROVED/REJECTED/INCONCLUSIVE）、confidence（0-100）、"
            "reasoning（繁體中文）、rejection_reasons（list）、suggested_actions（list）的 JSON。"
            "APPROVED/INCONCLUSIVE 時 rejection_reasons 可為空陣列；"
            "APPROVED 時 suggested_actions 可為空陣列。"
        ),
    ),
    template_body=(
        "<target>\n名稱：{target_name}\n描述：{target_description}\n</target>\n\n"
        "<mission>\n目標摘要：{mission_summary}\n目前計畫：{mission_plan}\n"
        "目前風險評分：{risk_score}/100\n</mission>\n\n"
        "<findings_snapshot>\n漏洞總數：{vuln_count}\n"
        "已確認漏洞（confirmed）：{confirmed_vuln_count}\n"
        "高嚴重性漏洞（high/critical）：{high_severity_count}\n"
        "附帶 PoC 證據的漏洞數：{poc_count}\n攻擊向量總數：{vector_count}\n"
        "可利用攻擊向量（EXPLOITABLE）：{exploitable_vector_count}\n</findings_snapshot>\n\n"
        "<scan_coverage>\n子域名覆蓋率：{subdomain_coverage_pct}%\n"
        "端口覆蓋率：{port_coverage_pct}%\nURL 爬取覆蓋率：{url_coverage_pct}%\n"
        "漏洞掃描覆蓋率：{vuln_scan_coverage_pct}%\n整體掃描覆蓋率：{overall_coverage_pct}%\n"
        "</scan_coverage>\n\n<vulnerability_details>\n{vuln_details}\n</vulnerability_details>"
    ),
    output_schema=MissionEvalOutput,
    agent_id="verification_agent",
    temperature=0,
    output_format_hint=(
        "回傳 ONLY 合法的 JSON，格式如下（不要 markdown code block）：\n"
        '{{\n  "verdict": "APPROVED" | "REJECTED" | "INCONCLUSIVE",\n'
        '  "confidence": 0-100,\n  "reasoning": "繁體中文的詳細分析",\n'
        '  "rejection_reasons": ["具體駁回點 1", "具體駁回點 2"],\n'
        '  "suggested_actions": ["建議動作 1", "建議動作 2"]\n}}\n\n'
        "若 verdict 是 APPROVED 或 INCONCLUSIVE，rejection_reasons 可以是空陣列 []。\n"
        "若 verdict 是 APPROVED，suggested_actions 可以是空陣列 []。"
    ),
)
MISSION_REVIEW_PROMPT = MISSION_REVIEW_SPEC  # 向後相容別名


# ════════════════════════════════════════════════════════════════════
# JSON extraction helper（仿 skill_verifier）
# ════════════════════════════════════════════════════════════════════


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    brace_start = text.find("{")
    if brace_start != -1:
        brace_end = text.rfind("}")
        if brace_end > brace_start:
            try:
                return json.loads(text[brace_start : brace_end + 1])
            except json.JSONDecodeError:
                pass
    return {}


# ════════════════════════════════════════════════════════════════════
# Evidence collector
# ════════════════════════════════════════════════════════════════════


class MissionEvidence:
    """審查時蒐集的證據快照。"""

    def __init__(self) -> None:
        self.vuln_count = 0
        self.confirmed_vuln_count = 0
        self.high_severity_count = 0
        self.poc_count = 0
        self.has_poc_evidence = False
        self.vector_count = 0
        self.exploitable_vector_count = 0
        self.subdomain_coverage_pct = 0
        self.port_coverage_pct = 0
        self.url_coverage_pct = 0
        self.vuln_scan_coverage_pct = 0
        self.overall_coverage_pct = 0
        self.vuln_details_text = ""
        self.target_name = ""
        self.target_description = ""
        self.mission_summary = ""
        self.mission_plan = ""
        self.risk_score = 0

    def snapshot_dict(self) -> dict[str, Any]:
        """取得 MissionReview model 可直接使用的欄位 dict。"""
        return {
            "vuln_count": self.vuln_count,
            "confirmed_vuln_count": self.confirmed_vuln_count,
            "high_severity_count": self.high_severity_count,
            "has_poc_evidence": self.has_poc_evidence,
            "scan_coverage_pct": self.overall_coverage_pct,
        }


def _collect_evidence(overview_id: int) -> MissionEvidence:
    """蒐集 Overview 下所有證據（漏洞、攻擊向量、掃描覆蓋率）。"""
    from apps.core.models import (
        AttackVector,
        IP,
        Port,
        Subdomain,
        Target,
        URLResult,
        Vulnerability,
    )
    from apps.core.models.analyze.overview import Overview

    ev = MissionEvidence()

    try:
        overview = Overview.objects.select_related("target").get(id=overview_id)
    except Overview.DoesNotExist:
        logger.warning(f"[VerificationService] Overview#{overview_id} not found")
        return ev

    target = overview.target
    ev.target_name = target.name if target else "(unknown)"
    ev.target_description = (target.description if target else "") or ""
    ev.mission_summary = (overview.summary or "")[:500]
    ev.mission_plan = json.dumps(overview.plan or {}, ensure_ascii=False)[:1500]
    ev.risk_score = overview.risk_score or 0

    # ── 漏洞統計 ────────────────────────────────────────────────
    vulns = list(Vulnerability.objects.filter(overview_id=overview_id))
    ev.vuln_count = len(vulns)
    ev.confirmed_vuln_count = sum(1 for v in vulns if v.status == "confirmed")
    ev.high_severity_count = sum(1 for v in vulns if (v.severity or "").lower() in {"high", "critical"})

    poc_count = 0
    vuln_detail_lines = []
    hard_reject_reasons: list[str] = []
    for v in vulns[:15]:  # 限制給 LLM 的數量
        has_raw_poc = bool((v.request_raw or "").strip() and (v.response_raw or "").strip())
        # 也檢查是否有 PoCRecord
        has_poc_record = v.pocs.exists() if hasattr(v, "pocs") else False
        has_poc = has_raw_poc or has_poc_record
        if has_poc:
            poc_count += 1
        # Hard reject：high/critical 無任何 PoC 證據
        sev_lower = (v.severity or "").lower()
        if sev_lower in {"high", "critical"} and not has_poc and v.status == "confirmed":
            hard_reject_reasons.append(
                f"漏洞 #{v.id} [{v.severity}] {v.name} 已標記 confirmed 但完全無 PoC 證據"
            )
        poc_indicator = []
        if has_raw_poc:
            poc_indicator.append("raw")
        if has_poc_record:
            poc_indicator.append("PoCRecord")
        poc_str = "+".join(poc_indicator) if poc_indicator else "N"
        vuln_detail_lines.append(
            f"- [{v.severity}] {v.name} @ {v.matched_at} | status={v.status} | PoC={poc_str}"
        )
    ev.poc_count = poc_count
    ev.has_poc_evidence = poc_count > 0
    ev.vuln_details_text = "\n".join(vuln_detail_lines) if vuln_detail_lines else "(無漏洞記錄)"
    # 將 hard reject 原因附加到 evidence 上供呼叫端檢查
    ev.hard_reject_reasons = hard_reject_reasons  # type: ignore[attr-defined]

    # ── 攻擊向量統計 ────────────────────────────────────────────
    vectors = list(AttackVector.objects.filter(overview_id=overview_id))
    ev.vector_count = len(vectors)
    ev.exploitable_vector_count = sum(1 for v in vectors if v.status == "EXPLOITABLE")

    # ── 掃描覆蓋率（資產為單位） ───────────────────────────────
    # 這是啟發式估計：以 Overview 的 target 資產總數為分母，已掃描/已發現為分子
    if target:
        subdomain_total = Subdomain.objects.filter(target=target).count()
        ip_total = IP.objects.filter(target=target).count()
        url_total = URLResult.objects.filter(target=target).count()
        port_total = Port.objects.filter(ip__target=target).count()

        # 啟發式覆蓋率：子域名存在 = 有做 subfinder；IP 有 port = 有做 nmap；
        # URL 已 fetched = 有做 crawler；URL 已 vuln scanned = 有做 nuclei
        url_fetched = URLResult.objects.filter(target=target).exclude(
            content_fetch_status="PENDING"
        ).count()
        url_vuln_scanned = URLResult.objects.filter(target=target).exclude(
            nuclei_scans__isnull=True
        ).count() if hasattr(URLResult, "nuclei_scans") else 0

        # 各維度覆蓋率（避免除以 0；若該類資產根本不存在，視為 100% N/A）
        ev.subdomain_coverage_pct = 100 if subdomain_total == 0 else min(100, int(subdomain_total * 100 / max(1, subdomain_total)))
        ev.port_coverage_pct = 100 if ip_total == 0 else min(100, int(port_total * 100 / max(1, ip_total * 10)))  # 假設每 IP 預期 10 個 port
        ev.url_coverage_pct = 100 if url_total == 0 else min(100, int(url_fetched * 100 / max(1, url_total)))
        ev.vuln_scan_coverage_pct = 100 if url_total == 0 else min(100, int(url_vuln_scanned * 100 / max(1, url_total)))

        # 整體加權平均
        ev.overall_coverage_pct = int(
            (ev.subdomain_coverage_pct + ev.port_coverage_pct + ev.url_coverage_pct + ev.vuln_scan_coverage_pct) / 4
        )
    else:
        ev.overall_coverage_pct = 0

    return ev


# ════════════════════════════════════════════════════════════════════
# VerificationService
# ════════════════════════════════════════════════════════════════════


class VerificationService:
    """Mission-level PoC 審查服務（LLM-as-judge gate）。

    使用方式（由 update_overview_status 工具或 propose_next_steps 呼叫）：
        service = VerificationService()
        review = service.review_mission_completion(overview_id=81, ...)
        if review.verdict == "REJECTED":
            # 退回 EXECUTING 並注入 review.rejection_reasons 到 thread
        elif review.verdict == "APPROVED":
            # 允許 COMPLETED
        elif review.verdict == "INCONCLUSIVE":
            # 放行但設 review.needs_human_review = True
    """

    # 置信度門檻（可調整）
    APPROVAL_THRESHOLD = 70      # ≥ 70 才 APPROVED
    REJECTION_THRESHOLD = 40     # < 40 才 REJECTED；介於兩者之間 INCONCLUSIVE

    def __init__(self, llm=None):
        from apps.core.llms import get_llm_instance
        self._llm = llm or get_llm_instance(
            agent_id="verification_agent",
            temperature=0,  # 審查要確定
        )

    def review_mission_completion(
        self,
        overview_id: int,
        triggered_by: str,
        triggered_by_agent: str = "",
    ):
        """審查 Overview 是否真可以 COMPLETED。

        Args:
            overview_id: 被審查的 Overview ID
            triggered_by: 觸發路徑（"update_overview_status" / "propose_next_steps"）
            triggered_by_agent: 觸發的 agent id

        Returns:
            MissionReview 物件（verdict 已判定）
        """
        from apps.core.models.analyze.MissionReview import MissionReview
        from apps.core.models import Vulnerability

        # Step 1: 蒐集證據
        evidence = _collect_evidence(overview_id)
        logger.info(
            f"[VerificationService] Reviewing Overview#{overview_id}: "
            f"vulns={evidence.vuln_count}({evidence.confirmed_vuln_count} confirmed), "
            f"coverage={evidence.overall_coverage_pct}%"
        )

        # Step 1b: Hard reject 前置檢查（不浪費 LLM token）
        hard_reject_reasons = getattr(evidence, "hard_reject_reasons", [])
        if hard_reject_reasons:
            logger.warning(
                f"[VerificationService] Hard reject for Overview#{overview_id}: "
                f"{len(hard_reject_reasons)} high/critical vulns without PoC"
            )
            review = MissionReview.objects.create(
                overview_id=overview_id,
                verdict="REJECTED",
                triggered_by=triggered_by,
                triggered_by_agent=triggered_by_agent,
                confidence_score=95,
                reasoning=(
                    "自動硬性駁回：存在 high/critical 漏洞已標記 confirmed "
                    "但完全無 PoC 證據（無 PoCRecord 也無 request_raw+response_raw）。"
                    "請為這些漏洞生成並驗證 PoC 後再嘗試 COMPLETED。"
                ),
                rejection_reasons=hard_reject_reasons,
                suggested_actions=[
                    "為每個 high/critical 漏洞呼叫 generate_poc_for_vulnerability 生成 PoC",
                    "呼叫 verify_poc_execution 確認 PoC 有效",
                    "或提供 request_raw + response_raw 證據",
                ],
                needs_human_review=False,
                reviewed_at=datetime.now(timezone.utc),
                **evidence.snapshot_dict(),
            )
            return review

        # Step 1c: 程式化完成度 gate（無任何產出證據時直接駁回，不浪費 LLM token）
        completion_blockers = self._check_completion_gate(overview_id, evidence)
        if completion_blockers:
            logger.warning(
                f"[VerificationService] Completion gate failed for Overview#{overview_id}: "
                f"{completion_blockers}"
            )
            review = MissionReview.objects.create(
                overview_id=overview_id,
                verdict="REJECTED",
                triggered_by=triggered_by,
                triggered_by_agent=triggered_by_agent,
                confidence_score=90,
                reasoning=(
                    "自動駁回：缺乏最低完成證據。"
                    "一個 mission 要宣告 COMPLETED 至少需要滿足以下任一條件："
                    "（a）至少 1 筆 Vulnerability 記錄；"
                    "（b）至少 1 個 EXPLOITABLE AttackVector；"
                    "（c）至少 1 個 recon_note/skill_execution ExecutionArtifact；"
                    "（d）至少執行過 1 次 scanner（Nmap/Subfinder/Nuclei）。"
                ),
                rejection_reasons=completion_blockers,
                suggested_actions=[
                    "執行至少一個 scanner（subfinder/nmap/nuclei）並透過 write_recon_note 記錄發現",
                    "對偵察發現建立 Vulnerability 或將 AttackVector 推進到 EXPLOITABLE",
                ],
                needs_human_review=False,
                reviewed_at=datetime.now(timezone.utc),
                **evidence.snapshot_dict(),
            )
            return review

        # Step 2: 標記相關 vuln 為 verifying
        vuln_ids = list(
            Vulnerability.objects.filter(
                overview_id=overview_id, status="confirmed"
            ).values_list("id", flat=True)
        )
        if vuln_ids:
            Vulnerability.objects.filter(id__in=vuln_ids).update(status="verifying")

        # Step 3: 建立 review 記錄（PENDING）
        review = MissionReview.objects.create(
            overview_id=overview_id,
            verdict="PENDING",
            triggered_by=triggered_by,
            triggered_by_agent=triggered_by_agent,
            **evidence.snapshot_dict(),
        )

        # Step 4: LLM 評估
        eval_result = self._evaluate_via_llm(evidence)

        # Step 5: 根據 confidence 與 verdict 判定最終結果
        confidence = eval_result.confidence
        raw_verdict = eval_result.verdict.upper().strip()

        # 雙重確認：LLM 的 verdict 必須與 confidence 門檻一致
        if raw_verdict == "APPROVED" and confidence < self.APPROVAL_THRESHOLD:
            # LLM 說 APPROVED 但信心不足 → 降級為 INCONCLUSIVE
            final_verdict = "INCONCLUSIVE"
        elif raw_verdict == "REJECTED" and confidence >= self.REJECTION_THRESHOLD:
            # LLM 說 REJECTED 但信心不夠低 → 降級為 INCONCLUSIVE
            final_verdict = "INCONCLUSIVE"
        else:
            final_verdict = raw_verdict if raw_verdict in {"APPROVED", "REJECTED", "INCONCLUSIVE"} else "INCONCLUSIVE"

        # Step 6: 寫入 review 結果
        review.verdict = final_verdict
        review.confidence_score = confidence
        review.reasoning = eval_result.reasoning
        review.rejection_reasons = eval_result.rejection_reasons
        review.suggested_actions = eval_result.suggested_actions
        review.needs_human_review = (final_verdict == "INCONCLUSIVE")
        review.reviewed_at = datetime.now(timezone.utc)
        review.save()

        # Step 7: 根據 verdict 處理 vuln 狀態
        if final_verdict == "APPROVED":
            # vuln 從 verifying 回 confirmed
            if vuln_ids:
                Vulnerability.objects.filter(id__in=vuln_ids).update(status="confirmed")
        elif final_verdict == "REJECTED":
            # vuln 從 verifying 回 confirmed（保留 agent 的工作，只是 mission 沒過審查）
            if vuln_ids:
                Vulnerability.objects.filter(id__in=vuln_ids).update(status="confirmed")
        # INCONCLUSIVE：vuln 保留在 verifying 狀態

        logger.info(
            f"[VerificationService] MissionReview#{review.id} for Overview#{overview_id}: "
            f"{final_verdict} (confidence={confidence})"
        )

        return review

    def _evaluate_via_llm(self, evidence: MissionEvidence) -> MissionEvalOutput:
        """呼叫 LLM 評估 mission 完成度。"""
        prompt = MISSION_REVIEW_PROMPT.format(
            target_name=evidence.target_name,
            target_description=evidence.target_description,
            mission_summary=evidence.mission_summary,
            mission_plan=evidence.mission_plan,
            risk_score=evidence.risk_score,
            vuln_count=evidence.vuln_count,
            confirmed_vuln_count=evidence.confirmed_vuln_count,
            high_severity_count=evidence.high_severity_count,
            poc_count=evidence.poc_count,
            vector_count=evidence.vector_count,
            exploitable_vector_count=evidence.exploitable_vector_count,
            subdomain_coverage_pct=evidence.subdomain_coverage_pct,
            port_coverage_pct=evidence.port_coverage_pct,
            url_coverage_pct=evidence.url_coverage_pct,
            vuln_scan_coverage_pct=evidence.vuln_scan_coverage_pct,
            overall_coverage_pct=evidence.overall_coverage_pct,
            vuln_details=evidence.vuln_details_text,
        )

        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            data = _extract_json(content)
            validated = MissionEvalOutput(**data)
            return validated
        except Exception as e:
            logger.exception(f"[VerificationService] LLM evaluation failed: {e}")
            # 失敗時保守處理：INCONCLUSIVE，信心 50，讓上層決定
            return MissionEvalOutput(
                verdict="INCONCLUSIVE",
                confidence=50,
                reasoning=f"LLM 評估失敗（{type(e).__name__}: {e}），保守放行但需人工複查。",
                rejection_reasons=[],
                suggested_actions=["手動檢查 Overview 是否真的完成"],
            )

    # ════════════════════════════════════════════════════════════════════
    # Programmatic completion gate (Bug 4 fix)
    # ════════════════════════════════════════════════════════════════════

    # ExecutionArtifact.artifact_type 字串值，任一即視為「有實際產出」
    _EVIDENCE_ARTIFACT_TYPES = (
        "recon_note",
        "skill_execution",
        "http_exchange",
        "content_blob",
        "scan_result",
        "execution_note",
    )

    def _check_completion_gate(self, overview_id: int, evidence: MissionEvidence) -> list[str]:
        """
        程式化完成度 gate：檢查 Overview 是否具備最低限度的「實際產出證據」。

        寬鬆規則（OR 邏輯，任一滿足即放行）：
            (a) 至少 1 筆 Vulnerability 記錄
            (b) 至少 1 個 EXPLOITABLE AttackVector
            (c) 至少 1 個 recon_note/skill_execution/... ExecutionArtifact（經 thread 關聯）
            (d) 至少執行過 1 次 scanner（NmapScan / SubfinderScan / NucleiScan / URLScan / AmassScan / SubBrute）

        Returns:
            blockers (list[str]): 空 list 代表通過；非空代表每個原因都應回報給 agent。
        """
        blockers: list[str] = []

        try:
            from apps.core.models import ExecutionGraph
            from apps.core.models.analyze.overview import Overview
            try:
                overview = Overview.objects.get(id=overview_id)
            except Overview.DoesNotExist:
                return [f"Overview#{overview_id} 不存在"]

            # (a) Vulnerability
            if evidence.vuln_count >= 1:
                return blockers  # 通過

            # (b) EXPLOITABLE AttackVector
            if evidence.exploitable_vector_count >= 1:
                return blockers  # 通過

            # (c) ExecutionArtifact 透過 thread_id join
            thread_id = getattr(overview, "thread_id", None)
            artifact_count = 0
            if thread_id:
                artifact_count = (
                    ExecutionGraph.objects.filter(thread_id=thread_id)
                    .filter(status=ExecutionGraph.Status.SUCCEEDED)
                    .filter(artifacts__artifact_type__in=self._EVIDENCE_ARTIFACT_TYPES)
                    .count()
                )
            if artifact_count >= 1:
                return blockers  # 通過

            # (d) 至少一次 scanner 執行
            scan_count = self._count_scanner_runs(overview_id, overview)
            if scan_count >= 1:
                return blockers  # 通過

            # 全部未通過 — 組裝駁回原因
            blockers.append(
                f"完全無產出證據：無 Vulnerability（0）、"
                f"無 EXPLOITABLE AttackVector（{evidence.exploitable_vector_count}）、"
                f"無 ExecutionArtifact（{artifact_count}）、無 scanner 執行記錄（{scan_count}）"
            )
        except Exception as e:
            # gate 本身壞掉不應擋住 mission，記 log 後放行
            logger.exception(
                f"[VerificationService] _check_completion_gate error (allowing): {e}"
            )
            return blockers

        return blockers

    @staticmethod
    def _count_scanner_runs(overview_id: int, overview) -> int:
        """計算與 Overview.target 相關的 scanner 記錄數量（任一型態皆可）。

        Scanner 記錄（NmapScan / SubfinderScan / AmassScan / SubBrute）透過
        Seed 關聯（欄位名 which_seed），而非直接 FK 到 Target。
        NucleiScan 透過 URLResult.target 關聯。此方法相容兩條路徑。
        """
        try:
            from apps.core.models import Seed
            target = getattr(overview, "target", None)
            target_id = getattr(target, "id", None)
            if not target_id:
                return 0

            seed_ids = list(
                Seed.objects.filter(target_id=target_id).values_list("id", flat=True)
            )

            try:
                from apps.core.models import (
                    NmapScan,
                    SubfinderScan,
                    AmassScan,
                    SubBrute,
                )
            except Exception:
                return 0
            try:
                from apps.core.models import NucleiScan
            except Exception:
                NucleiScan = None  # type: ignore[assignment]
            try:
                from apps.core.models import URLScan
            except Exception:
                URLScan = None  # type: ignore[assignment]

            total = 0
            # Seed-linked scanners (FieldError / no which_seed → skip gracefully)
            for model in (NmapScan, SubfinderScan, AmassScan, SubBrute):
                try:
                    total += model.objects.filter(which_seed__in=seed_ids).count()
                except Exception:
                    continue

            # Target-linked scanners (NucleiScan / URLScan)
            for model in (NucleiScan, URLScan):
                if model is None:
                    continue
                try:
                    total += model.objects.filter(target_id=target_id).count()
                except Exception:
                    continue

            return total
        except Exception as e:
            logger.debug(f"[VerificationService] _count_scanner_runs failed: {e}")
            return 0
