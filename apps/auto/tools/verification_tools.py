"""
VerificationMixin: 漏洞驗證與 POC 管理工具。

提供三個顯式工具，實現「驗證 → 記錄 → 生成 POC → 執行驗證 POC」的完整管道：

  1. run_verification(verification_id)
     執行 AI Verification — LLM 看 observation_prompt + execution_output 判定真偽。

  2. generate_poc_for_vulnerability(vulnerability_id)
     AI 生成 PoC — LLM 從漏洞證據產生可執行的 PoC 腳本，存入 PoCRecord。

  3. verify_poc_execution(poc_id)
     沙箱執行 PoC — 在 bwrap 隔離環境實際執行 PoC，LLM 判定是否成功驗證漏洞。

工作流（Agent 應依序執行）：
    create_verification → run_verification → record_vulnerability
    → generate_poc_for_vulnerability → verify_poc_execution
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from apps.ai_assistant import method_tool
from apps.ai_assistant.prompts import PromptSpec, TaskDefinition

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# Structured output schemas
# ════════════════════════════════════════════════════════════════════


class VerificationEvalOutput(BaseModel):
    """run_verification 的 LLM 結構化輸出。"""

    verdict: str = Field(
        description="驗證裁決：PASSED（通過）/ FAILED（未通過）/ INCONCLUSIVE（無法確定）"
    )
    confidence: int = Field(description="信心分數 0-100", ge=0, le=100)
    reasoning: str = Field(description="詳細分析（繁體中文）")


class PoCGenerationOutput(BaseModel):
    """generate_poc_for_vulnerability 的 LLM 結構化輸出。"""

    title: str = Field(description="PoC 標題，如 'SQL Injection via Login Form'")
    language: str = Field(
        description="PoC 語言/類型：curl / python / bash / http_request / manual"
    )
    content: str = Field(description="實際的 PoC 腳本/payload/步驟內容")
    notes: str = Field(default="", description="使用說明或注意事項（選填）")


class PoCExecutionEvalOutput(BaseModel):
    """verify_poc_execution 的 LLM 結構化輸出。"""

    is_verified: bool = Field(description="此 PoC 執行結果是否成功證明了漏洞存在")
    confidence: int = Field(description="信心分數 0-100", ge=0, le=100)
    reasoning: str = Field(description="判斷依據（繁體中文）")


# ════════════════════════════════════════════════════════════════════
# PromptSpec 宣告（取代原本的字串常數）
# ════════════════════════════════════════════════════════════════════

VERIFICATION_EVAL_SPEC = PromptSpec(
    name="VerificationEval",
    role="獨立的滲透測試驗證員",
    task=TaskDefinition(
        goal="判斷一次攻擊向量（AttackVector）的執行輸出是否達成了預期的成功標準。",
        background="Agent 已執行過攻擊向量並取得 execution_output；本驗證為獨立判定。",
        materials="observation_prompt（成功標準描述）與 execution_output（攻擊實際輸出）。",
        boundary=(
            "1. 僅依 observation_prompt 與 execution_output 判定，不參考其他資訊。\n"
            "2. PASSED 僅限輸出明確含成功標準證據；模糊不清一律 INCONCLUSIVE。\n"
            "3. 輸出必須是合法 JSON，不要 markdown code block。"
        ),
        dod="回傳含 verdict（PASSED/FAILED/INCONCLUSIVE）、confidence（0-100）、reasoning 的 JSON。",
    ),
    template_body=(
        "<observation_prompt>\n{observation_prompt}\n</observation_prompt>\n\n"
        "<execution_output>\n{execution_output}\n</execution_output>\n\n"
        "<task>\n"
        "請根據上述執行輸出，判斷是否滿足成功標準（observation_prompt）。\n\n"
        "判斷基準：\n"
        "- PASSED：執行輸出明確包含成功標準描述的證據（如漏洞回應、版本號、敏感資料）\n"
        "- FAILED：執行輸出明確不包含成功標準的證據，或顯示目標不受影響\n"
        "- INCONCLUSIVE：輸出不足或模糊，無法確定\n"
        "</task>"
    ),
    output_schema=VerificationEvalOutput,
    agent_id="verification_agent",
    temperature=0,
    output_format_hint=(
        "回傳 ONLY 合法的 JSON（不要 markdown code block）：\n"
        '{{\n  "verdict": "PASSED" | "FAILED" | "INCONCLUSIVE",\n'
        '  "confidence": 0-100,\n  "reasoning": "繁體中文的詳細分析"\n}}'
    ),
)
# 向後相容：消費端程式碼可繼續用 VERIFICATION_EVAL_PROMPT.format(...)
VERIFICATION_EVAL_PROMPT = VERIFICATION_EVAL_SPEC

POC_GENERATION_SPEC = PromptSpec(
    name="PoCGenerator",
    role="資深滲透測試員，擅長撰寫 Proof of Concept（PoC）腳本",
    task=TaskDefinition(
        goal="根據已確認的漏洞資訊，生成一個可重現該漏洞的 PoC。",
        background="漏洞已確認存在；本步驟產出可執行的 PoC 腳本以供驗證與留下證據。",
        materials=(
            "vuln_name、severity、matched_at、description、cve_info（選填）、"
            "request_raw、response_raw、extracted_results。"
        ),
        boundary=(
            "1. PoC 必須可獨立執行（含完整目標 URL/IP）。\n"
            "2. 必須包含驗證成功的判斷邏輯（如檢查回應字串）。\n"
            "3. 安全且不具破壞性（只驗證，不刪除/修改資料）。\n"
            "4. 輸出合法 JSON，不要 markdown code block。"
        ),
        dod="回傳含 title、language、content、notes 的 JSON。",
    ),
    template_body=(
        "<vulnerability_info>\n漏洞名稱：{vuln_name}\n嚴重程度：{severity}\n"
        "發現位置：{matched_at}\n描述：{description}\n</vulnerability_info>\n\n"
        "<cve_intelligence>\n{cve_info}\n</cve_intelligence>\n\n"
        "<evidence>\n原始請求：\n{request_raw}\n\n"
        "原始回應：\n{response_raw}\n\n擷取結果：\n{extracted_results}\n</evidence>\n\n"
        "<task>\n"
        "根據上述資訊，生成一個 PoC，能夠重現或驗證此漏洞。\n\n"
        "語言選擇指引：\n"
        "- curl：適合 HTTP 类漏洞（SQLi、XSS、LFI、SSRF、認證繞過）\n"
        "- python：適合需要邏輯判斷或多次請求的漏洞\n"
        "- bash：適合系統層漏洞或簡單的 curl 組合\n"
        "- http_request：適合展示原始 HTTP 請求/回應\n"
        "- manual：若漏洞難以自動化，提供手動步驟說明\n"
        "</task>"
    ),
    output_schema=PoCGenerationOutput,
    agent_id="verification_agent",
    temperature=0,
    output_format_hint=(
        "回傳 ONLY 合法的 JSON（不要 markdown code block）：\n"
        '{{\n  "title": "簡潔的 PoC 標題",\n'
        '  "language": "curl" | "python" | "bash" | "http_request" | "manual",\n'
        '  "content": "完整的 PoC 腳本內容",\n'
        '  "notes": "使用說明或注意事項（選填，可為空字串）"\n}}'
    ),
)
POC_GENERATION_PROMPT = POC_GENERATION_SPEC

POC_EXECUTION_EVAL_SPEC = PromptSpec(
    name="PoCExecutionEval",
    role="滲透測試驗證員",
    task=TaskDefinition(
        goal="判斷一個 PoC 的執行結果是否成功證明了漏洞存在。",
        background="PoC 已在沙箱執行完畢；本步驟判定執行輸出是否構成漏洞證據。",
        materials=(
            "vuln_name、matched_at、description、poc_title、poc_language、poc_content、"
            "exit_code、execution_output。"
        ),
        boundary=(
            "1. is_verified=true 僅限輸出含明確漏洞證據（錯誤訊息、敏感資料、預期回應模式）。\n"
            "2. 執行失敗/超時/無證據一律 false。\n"
            "3. 輸出合法 JSON，不要 markdown code block。"
        ),
        dod="回傳含 is_verified、confidence、reasoning 的 JSON。",
    ),
    template_body=(
        "<vulnerability>\n名稱：{vuln_name}\n位置：{matched_at}\n描述：{description}\n</vulnerability>\n\n"
        "<poc_executed>\nPoC 標題：{poc_title}\nPoC 語言：{poc_language}\n"
        "PoC 內容：\n{poc_content}\n</poc_executed>\n\n"
        "<execution_result>\n退出代碼：{exit_code}\n執行輸出：\n{execution_output}\n</execution_result>\n\n"
        "<task>\n判斷這個 PoC 的執行結果是否成功證明了上述漏洞。</task>"
    ),
    output_schema=PoCExecutionEvalOutput,
    agent_id="verification_agent",
    temperature=0,
    output_format_hint=(
        "回傳 ONLY 合法的 JSON（不要 markdown code block）：\n"
        '{{\n  "is_verified": true | false,\n'
        '  "confidence": 0-100,\n  "reasoning": "繁體中文的判斷依據"\n}}'
    ),
)
POC_EXECUTION_EVAL_PROMPT = POC_EXECUTION_EVAL_SPEC


# ════════════════════════════════════════════════════════════════════
# JSON extraction helper（仿 verification_service / skill_verifier）
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
# LLM helper
# ════════════════════════════════════════════════════════════════════


def _get_verification_llm():
    """取得驗證專用的 LLM 實例（低溫度，確保判斷穩定）。"""
    from apps.core.llms import get_llm_instance
    return get_llm_instance(
        agent_id="verification_agent",
        temperature=0,
    )


def _invoke_llm(llm, prompt: str) -> str:
    """呼叫 LLM 並取得文字回應。"""
    response = llm.invoke(prompt)
    if hasattr(response, "content"):
        return response.content
    return str(response)


# ════════════════════════════════════════════════════════════════════
# VerificationMixin
# ════════════════════════════════════════════════════════════════════


class VerificationMixin:
    """
    漏洞驗證與 POC 管理工具。
    繼承此 Mixin 的 Assistant 會獲得 run_verification、generate_poc_for_vulnerability、
    verify_poc_execution 三個 @method_tool。
    """

    # ────────────────────────────────────────────────────────────────
    # 工具 1：run_verification
    # ────────────────────────────────────────────────────────────────

    @method_tool
    def run_verification(self, verification_id: int) -> str:
        """
        執行 AI Verification — 將待驗證的 Verification 記錄送交 LLM 判定。

        流程：
        1. 讀取 Verification（狀態應為 PENDING）
        2. 取得 execution_output（從 AttackVector 的 ExecutionNode 或 Vulnerability 的 request/response）
        3. 送 LLM：observation_prompt + execution_output → verdict
        4. 寫回 verdict / confidence_score / ai_response / verified_at
        5. 若 PASSED 且 auto_create_vulnerability=True → 自動建立 Vulnerability

        Args:
            verification_id: 要執行的 Verification ID。

        Returns:
            verdict + reasoning，讓 Agent 決定下一步。
        """
        try:
            from apps.core.models.analyze.Verification import Verification
            from apps.core.models import AttackVector, ExecutionNode, Vulnerability

            try:
                v = Verification.objects.get(id=verification_id)
            except Verification.DoesNotExist:
                return f"ERROR: Verification#{verification_id} 不存在。"

            if v.verdict not in ("PENDING",):
                return (
                    f"Verification#{verification_id} 已執行過（verdict={v.verdict}）。"
                    f"如需重新驗證，請建立新的 Verification。"
                )

            # ── 取得 execution_output ────────────────────────────────
            execution_output = ""

            if v.attack_vector_id:
                # 從 AttackVector 關聯的 ExecutionNode 取最後輸出
                av = v.attack_vector
                # AttackVector 可能透過 metadata 或直接關聯 ExecutionNode
                # 嘗試從 graph 中找最近的 node output
                node = (
                    ExecutionNode.objects.filter(
                        graph__thread__overview__id=av.overview_id
                    )
                    .filter(name__icontains=av.name)
                    .order_by("-created_at")
                    .first()
                )
                if node and node.output:
                    execution_output = str(node.output)[:8000]
                elif av.payload:
                    execution_output = json.dumps(av.payload, ensure_ascii=False)[:8000]
                else:
                    execution_output = "(無可用的執行輸出)"

            if v.vulnerability_id and not execution_output:
                # 從 Vulnerability 取 request_raw + response_raw
                vuln = v.vulnerability
                parts = []
                if vuln.request_raw:
                    parts.append(f"--- Request ---\n{vuln.request_raw[:4000]}")
                if vuln.response_raw:
                    parts.append(f"--- Response ---\n{vuln.response_raw[:4000]}")
                if vuln.extracted_results:
                    parts.append(
                        f"--- Extracted ---\n{json.dumps(vuln.extracted_results, ensure_ascii=False)[:2000]}"
                    )
                execution_output = "\n\n".join(parts) if parts else "(漏洞無 request/response 證據)"

            if not execution_output:
                execution_output = "(無可用的執行輸出)"

            # ── 送 LLM 評估 ──────────────────────────────────────────
            prompt = VERIFICATION_EVAL_PROMPT.format(
                observation_prompt=v.observation_prompt or "(未設定成功標準)",
                execution_output=execution_output,
            )

            llm = _get_verification_llm()
            content = _invoke_llm(llm, prompt)
            data = _extract_json(content)

            try:
                result = VerificationEvalOutput(**data)
            except Exception:
                result = VerificationEvalOutput(
                    verdict="INCONCLUSIVE",
                    confidence=50,
                    reasoning=f"LLM 回應無法解析：{content[:500]}",
                )

            # ── 寫回 Verification ────────────────────────────────────
            v.verdict = result.verdict.upper().strip()
            if v.verdict not in ("PASSED", "FAILED", "INCONCLUSIVE"):
                v.verdict = "INCONCLUSIVE"
            v.confidence_score = result.confidence
            v.ai_response = {
                "verdict": v.verdict,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "raw_output_snippet": execution_output[:1000],
            }
            v.execution_output = execution_output[:8000]
            v.verified_at = datetime.now(timezone.utc)
            v.save()

            # ── PASSED + auto_create_vulnerability → 建立漏洞 ────────
            created_vuln_msg = ""
            if v.verdict == "PASSED" and v.auto_create_vulnerability and not v.created_vulnerability_id:
                av = v.attack_vector
                vuln = Vulnerability.objects.create(
                    name=v.vulnerability_name or (av.name if av else "Auto-created"),
                    severity=v.vulnerability_severity or "medium",
                    matched_at=(av.matched_at if av and hasattr(av, "matched_at") else "unknown"),
                    description=f"由 Verification#{v.id} 自動建立。\n\n{result.reasoning}",
                    status="confirmed",
                    source_attack_vector=av,
                    overview_id=(av.overview_id if av else None),
                    tool_source="verification-agent",
                    template_id=f"verify-{v.id}",
                )
                v.created_vulnerability = vuln
                v.save()
                created_vuln_msg = f"\n\n✅ 自動建立 Vulnerability#{vuln.id}（狀態：confirmed）。"

            logger.info(
                f"[VerificationMixin] run_verification #{verification_id}: "
                f"{v.verdict} (confidence={result.confidence})"
            )

            return (
                f"Verification#{verification_id} 完成：\n"
                f"判定：{v.verdict}（信心：{result.confidence}/100）\n"
                f"分析：{result.reasoning}"
                f"{created_vuln_msg}"
            )

        except Exception as e:
            logger.exception(f"[VerificationMixin] run_verification failed: {e}")
            return f"執行 Verification#{verification_id} 時發生錯誤: {e}"

    # ────────────────────────────────────────────────────────────────
    # 工具 2：generate_poc_for_vulnerability
    # ────────────────────────────────────────────────────────────────

    @method_tool
    def generate_poc_for_vulnerability(self, vulnerability_id: int) -> str:
        """
        AI 生成 PoC — 根據漏洞的所有證據，由 LLM 產生可重現的 PoC 腳本。

        蒐集的證據包含：漏洞名稱、描述、request_raw、response_raw、extracted_results、
        CVE 情報、matched_at、目標名稱。生成的 PoC 會存入 PoCRecord（is_verified=False）。

        生成後建議呼叫 verify_poc_execution 執行驗證。

        Args:
            vulnerability_id: 要生成 PoC 的 Vulnerability ID。

        Returns:
            生成的 PoC 摘要（含 poc_id、title、language）。
        """
        try:
            from apps.core.models import PoCRecord, Vulnerability

            try:
                vuln = Vulnerability.objects.get(id=vulnerability_id)
            except Vulnerability.DoesNotExist:
                return f"ERROR: Vulnerability#{vulnerability_id} 不存在。"

            # ── 蒐集 CVE 情報 ────────────────────────────────────────
            cve_info = "(無 CVE 關聯)"
            if vuln.cve_intelligence_id:
                try:
                    cve = vuln.cve_intelligence
                    cve_info = (
                        f"CVE: {cve.cve_id}\n"
                        f"CVSS: {cve.cvss_score or 'N/A'} ({cve.severity})\n"
                        f"描述: {(cve.description or '')[:500]}\n"
                        f"已知利用: {'是' if cve.exploit_available else '否'}\n"
                        f"CISA KEV: {'是' if cve.cisa_kev else '否'}"
                    )
                except Exception:
                    pass

            # ── 組裝 prompt ──────────────────────────────────────────
            prompt = POC_GENERATION_PROMPT.format(
                vuln_name=vuln.name or "(未命名)",
                severity=vuln.severity or "unknown",
                matched_at=vuln.matched_at or "(未知)",
                description=(vuln.description or "(無描述)")[:2000],
                cve_info=cve_info,
                request_raw=(vuln.request_raw or "(無)")[:4000],
                response_raw=(vuln.response_raw or "(無)")[:4000],
                extracted_results=json.dumps(
                    vuln.extracted_results, ensure_ascii=False
                )[:2000]
                if vuln.extracted_results
                else "(無)",
            )

            # ── 呼叫 LLM 生成 ────────────────────────────────────────
            llm = _get_verification_llm()
            content = _invoke_llm(llm, prompt)
            data = _extract_json(content)

            try:
                result = PoCGenerationOutput(**data)
            except Exception as e:
                return (
                    f"LLM 生成 PoC 失敗（回應無法解析）：{e}\n"
                    f"原始回應：{content[:500]}"
                )

            # 驗證 language 合法性
            valid_languages = {"curl", "python", "bash", "http_request", "manual"}
            if result.language not in valid_languages:
                result.language = "manual"

            # ── 存入 PoCRecord ───────────────────────────────────────
            poc = PoCRecord.objects.create(
                vulnerability=vuln,
                title=result.title,
                content=result.content,
                language=result.language,
                result=None,
                is_verified=False,
            )

            logger.info(
                f"[VerificationMixin] Generated PoC#{poc.id} for Vuln#{vulnerability_id}: "
                f"{result.title} ({result.language})"
            )

            notes_msg = f"\n備註：{result.notes}" if result.notes else ""
            return (
                f"✅ PoC 已生成並儲存。\n"
                f"PoC ID: {poc.id}\n"
                f"標題：{result.title}\n"
                f"語言：{result.language}\n"
                f"內容預覽：{result.content[:300]}{'...' if len(result.content) > 300 else ''}"
                f"{notes_msg}\n\n"
                f"建議下一步：呼叫 verify_poc_execution(poc_id={poc.id}) 執行驗證。"
            )

        except Exception as e:
            logger.exception(f"[VerificationMixin] generate_poc failed: {e}")
            return f"生成 PoC 時發生錯誤: {e}"

    # ────────────────────────────────────────────────────────────────
    # 工具 3：verify_poc_execution
    # ────────────────────────────────────────────────────────────────

    @method_tool
    def verify_poc_execution(self, poc_id: int) -> str:
        """
        沙箱執行 PoC — 在 bwrap 隔離環境實際執行 PoC 腳本，並由 LLM 判定是否成功驗證漏洞。

        僅執行 language 為 curl/python/bash 的 PoC。
        http_request/manual 類型標註為「需手動驗證」。

        執行後更新 PoCRecord 的 is_verified 與 result 欄位。

        Args:
            poc_id: 要執行的 PoCRecord ID。

        Returns:
            執行結果摘要 + LLM 判定。
        """
        try:
            from apps.core.models import PoCRecord, Vulnerability

            try:
                poc = PoCRecord.objects.select_related("vulnerability").get(id=poc_id)
            except PoCRecord.DoesNotExist:
                return f"ERROR: PoCRecord#{poc_id} 不存在。"

            vuln = poc.vulnerability
            if not vuln:
                return f"ERROR: PoCRecord#{poc_id} 沒有關聯的 Vulnerability。"

            # ── manual / http_request 不自動執行 ─────────────────────
            if poc.language in ("manual", "http_request"):
                poc.result = "此 PoC 類型（{lang}）需手動驗證，無法自動執行。".format(
                    lang=poc.language
                )
                poc.save()
                return (
                    f"PoC#{poc_id} 類型為 {poc.language}，需手動驗證。\n"
                    f"已標記 result 欄位。請人工檢視 PoC 內容並手動更新 is_verified。"
                )

            # ── 在沙箱執行 PoC ────────────────────────────────────────
            # 使用 SandboxMixin.run_command（若 self 有此方法）
            # 否則嘗試直接透過 Docker 執行
            command = self._build_poc_command(poc)
            if not command:
                return f"ERROR: 無法為 PoC#{poc_id}（語言：{poc.language}）建構執行命令。"

            overview_id = (
                vuln.overview_id
                or (vuln.target_id and None)  # target_id 沒有直接 overview
                or getattr(self, "_current_overview_id", None)
            )

            execution_output = ""
            exit_code = -1

            if hasattr(self, "run_command"):
                # 透過 SandboxMixin 執行（含 bwrap 隔離）
                result_str = self.run_command(command, overview_id=overview_id)
                execution_output = result_str
                # 嘗試從輸出解析 exit code
                m = re.search(r"Exit Code:\s*(\d+)", result_str)
                if m:
                    exit_code = int(m.group(1))
            else:
                # Fallback：直接 Docker 執行（無 bwrap，較不安全）
                execution_output = self._execute_poc_docker_fallback(command)
                exit_code = 0 if "ERROR" not in execution_output else 1

            # 截斷過長輸出
            execution_output_trunc = execution_output[:8000]

            # ── 送 LLM 判定 ──────────────────────────────────────────
            prompt = POC_EXECUTION_EVAL_PROMPT.format(
                vuln_name=vuln.name or "(未命名)",
                matched_at=vuln.matched_at or "(未知)",
                description=(vuln.description or "(無描述)")[:1000],
                poc_title=poc.title,
                poc_language=poc.language,
                poc_content=poc.content[:3000],
                exit_code=exit_code,
                execution_output=execution_output_trunc,
            )

            llm = _get_verification_llm()
            content = _invoke_llm(llm, prompt)
            data = _extract_json(content)

            try:
                eval_result = PoCExecutionEvalOutput(**data)
            except Exception:
                eval_result = PoCExecutionEvalOutput(
                    is_verified=False,
                    confidence=30,
                    reasoning=f"LLM 回應無法解析：{content[:500]}",
                )

            # ── 更新 PoCRecord ───────────────────────────────────────
            poc.is_verified = eval_result.is_verified
            poc.result = (
                f"Exit Code: {exit_code}\n"
                f"--- Output ---\n{execution_output_trunc}\n"
                f"--- AI 判定 ---\n"
                f"verified: {eval_result.is_verified}\n"
                f"confidence: {eval_result.confidence}/100\n"
                f"reasoning: {eval_result.reasoning}"
            )
            poc.save()

            logger.info(
                f"[VerificationMixin] verify_poc #{poc_id}: "
                f"verified={eval_result.is_verified} (confidence={eval_result.confidence})"
            )

            verdict_icon = "✅" if eval_result.is_verified else "❌"
            return (
                f"{verdict_icon} PoC#{poc_id} 執行驗證完成。\n"
                f"判定：{'成功驗證' if eval_result.is_verified else '未能驗證'}"
                f"（信心：{eval_result.confidence}/100）\n"
                f"Exit Code: {exit_code}\n"
                f"輸出預覽：{execution_output[:500]}{'...' if len(execution_output) > 500 else ''}\n"
                f"AI 分析：{eval_result.reasoning}"
            )

        except Exception as e:
            logger.exception(f"[VerificationMixin] verify_poc failed: {e}")
            return f"執行 PoC#{poc_id} 驗證時發生錯誤: {e}"

    # ────────────────────────────────────────────────────────────────
    # 輔助方法
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_poc_command(poc) -> str | None:
        """根據 PoC 語言建構執行命令。"""
        import shlex

        content = poc.content.strip()
        if not content:
            return None

        if poc.language == "curl":
            # curl 命令直接執行，加上 -s -i 取得 header + body
            # 若使用者已包含 curl 前綴就直接用，否則補上
            if not content.startswith("curl "):
                content = "curl -s -i " + content
            return content

        elif poc.language == "python":
            # 將 python 腳本寫入暫存檔再執行
            # 使用 heredoc 避免 escape 問題
            escaped = content.replace("'", "'\\''")
            return f"python3 -c '{escaped}'"

        elif poc.language == "bash":
            # bash 腳本直接透過 bash -c 執行
            escaped = shlex.quote(content)
            return f"bash -c {escaped}"

        return None

    @staticmethod
    def _execute_poc_docker_fallback(command: str) -> str:
        """無 SandboxMixin 時的 Docker 直接執行 fallback（無 bwrap 隔離）。"""
        try:
            import docker

            client = docker.from_env()
            container = client.containers.get("c2_kali_sandbox")
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", command],
                detach=False,
                stream=False,
            )
            return output_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            return f"ERROR: Docker 執行失敗: {e}"
