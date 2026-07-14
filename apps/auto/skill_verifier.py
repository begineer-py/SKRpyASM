"""
Skill Verifier Agent

用 AI Agent 驗證技能是否正常運作，參考壓縮系統中 LLM 評估內容的設計模式。
流程：
  1. 讀取 SkillTemplate 的 instructions / input_schema / output_schema / script_content
  2. 用 LLM 構造測試 input（從 input_schema + instructions 推導）
  3. 在 sandbox 中執行技能
  4. 用 LLM 評估輸出是否符合預期
  5. 寫入 SkillVerification 記錄並更新 SkillTemplate.last_verified_at
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from apps.ai_assistant.prompts import PromptSpec, TaskDefinition

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """Extract JSON dict from LLM response text (handles markdown code blocks)."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    brace_start = text.find('{')
    if brace_start != -1:
        brace_end = text.rfind('}')
        if brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass
    return {}


class VerifierTestInput(BaseModel):
    """Structured output: LLM generates test input for a skill."""
    test_input: Optional[dict] = Field(default=None, description="構造的測試輸入（JSON）")
    reasoning: str = Field(description="為什麼選擇此測試輸入")


class VerifierEvalOutput(BaseModel):
    """Structured output: LLM evaluates skill execution result."""
    verdict: str = Field(description="驗證裁決")
    confidence: int = Field(description="信心分數 0-100", ge=0, le=100)
    reasoning: str = Field(description="詳細分析")
    suggestions: Optional[str] = Field(default="", description="改進建議")


# ════════════════════════════════════════════════════════════════════
# PromptSpec 宣告（取代原本的字串常數）
# ════════════════════════════════════════════════════════════════════

VERIFICATION_SPEC = PromptSpec(
    name="SkillVerifier-TestInput",
    role="Skill Verification Agent",
    task=TaskDefinition(
        goal="驗證已註冊的滲透測試技能是否正常運作 — 此步生成測試輸入。",
        background="技能已註冊於 SkillTemplate；本 agent 作為獨立驗證器產生測試 input。",
        materials=(
            "skill_name、skill_description、skill_language、input_schema、output_schema、"
            "skill_instructions、script_content（前 2000 字）。"
        ),
        boundary=(
            "1. test_input 必須符合 input_schema（若無 schema 則給空物件）。\n"
            "2. 測試輸入應為實際可用的滲透測試目標（example.com 或 127.0.0.1）。\n"
            "3. reasoning 必須為繁體中文。\n"
            "4. 輸出合法 JSON，不要 markdown code block。"
        ),
        dod="回傳含 test_input（dict）與 reasoning 的 JSON。",
    ),
    template_body=(
        "<skill_context>\n<name>{skill_name}</name>\n<description>{skill_description}</description>\n"
        "<language>{skill_language}</language>\n<input_schema>{input_schema}</input_schema>\n"
        "<output_schema>{output_schema}</output_schema>\n<instructions>\n{skill_instructions}\n</instructions>\n"
        "<script_content>\n{script_content}\n</script_content>\n</skill_context>\n\n"
        "<task>\nConstruct a realistic test input for this skill based on its input_schema and instructions.\n</task>"
    ),
    output_schema=VerifierTestInput,
    agent_id="skill_verifier_agent",
    temperature=0.2,
    output_format_hint=(
        "Return ONLY valid JSON with this exact structure:\n"
        '{{\n  "test_input": {{ ... }},\n  "reasoning": "Why this test input was chosen"\n}}'
    ),
)
VERIFICATION_PROMPT = VERIFICATION_SPEC  # 向後相容別名

EVALUATION_SPEC = PromptSpec(
    name="SkillVerifier-Eval",
    role="Skill Output Evaluation Agent",
    task=TaskDefinition(
        goal="評估技能執行後的輸出是否符合預期結果。",
        background="技能已在沙箱執行；本步評估輸出是否正確。",
        materials=(
            "skill_name、skill_description、output_schema、test_input（使用的輸入）、"
            "exit_code、raw_output（執行原始輸出）。"
        ),
        boundary=(
            "1. PASSED：exit code 0 且輸出符合 schema/結構。\n"
            "2. FAILED：exit code 非零或輸出明顯錯誤/空。\n"
            "3. INCONCLUSIVE：無法明確判斷。\n"
            "4. reasoning 繁體中文；輸出合法 JSON。"
        ),
        dod="回傳含 verdict、confidence、reasoning、suggestions 的 JSON。",
    ),
    template_body=(
        "<skill_context>\n<name>{skill_name}</name>\n<description>{skill_description}</description>\n"
        "<expected_output_schema>{output_schema}</expected_output_schema>\n</skill_context>\n\n"
        "<execution_details>\n<test_input_used>{test_input}</test_input_used>\n"
        "<exit_code>{exit_code}</exit_code>\n<raw_output>{raw_output}</raw_output>\n</execution_details>\n\n"
        "<task>\nAnalyze the execution output and determine if this skill executed successfully.\n</task>"
    ),
    output_schema=VerifierEvalOutput,
    agent_id="skill_verifier_agent",
    temperature=0.2,
    output_format_hint=(
        "Return ONLY valid JSON with this exact structure:\n"
        '{{\n  "verdict": "PASSED" | "FAILED" | "INCONCLUSIVE",\n'
        '  "confidence": 0-100,\n  "reasoning": "Detailed analysis in Traditional Chinese",\n'
        '  "suggestions": "Any suggestions for improvement or notes about the output"\n}}'
    ),
)
EVALUATION_PROMPT = EVALUATION_SPEC  # 向後相容別名


class SkillVerifier:
    """AI agent-based skill verifier.

    Uses an LLM to:
    1. Generate test input from skill schema + instructions
    2. Execute the skill in sandbox
    3. Evaluate the output against expectations
    """

    def __init__(self, llm=None):
        from apps.core.llms import get_llm_instance
        self._llm = llm or get_llm_instance(
            agent_id="skill_verifier_agent",
            temperature=0.2
        )

    def verify(self, skill_id: int, test_input: dict = None) -> dict:
        """Run verification on a skill by its ID.

        Args:
            skill_id: The skill ID to verify.
            test_input: Optional dict of test input. If None, LLM auto-generates.
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from apps.core.models.analyze.SkillVerification import SkillVerification

        try:
            skill = SkillTemplate.objects.get(id=skill_id)
        except SkillTemplate.DoesNotExist:
            return {"ok": False, "error": f"Skill #{skill_id} not found"}

        logger.info(f"[SkillVerifier] Starting verification for skill: {skill.name} v{skill.version}")

        try:
            # Step 1: Generate or reuse test input
            if test_input is not None:
                logger.info(f"[SkillVerifier] Using caller-provided test_input for #{skill_id}")
                test_result = {"test_input": test_input}
            else:
                test_result = self._generate_test_input(skill)

            if not test_result.get("test_input"):
                return self._record_failure(skill, "LLM failed to generate test input")

            test_input = test_result["test_input"]

            # Step 2: Execute skill in sandbox
            exec_result = self._execute_skill(skill, test_input)

            if exec_result.get("error"):
                return self._record_failure(skill, exec_result["error"])

            # Step 3: Evaluate output via LLM
            eval_result = self._evaluate_output(
                skill=skill,
                test_input=test_input,
                exit_code=exec_result.get("exit_code"),
                raw_output=exec_result.get("raw_output", ""),
            )

            verdict = eval_result.get("verdict", "INCONCLUSIVE")
            confidence = eval_result.get("confidence", 0)
            reasoning = eval_result.get("reasoning", "")
            suggestions = eval_result.get("suggestions", "")

            # Step 4: Record verification
            verification = SkillVerification.objects.create(
                skill=skill,
                verdict=verdict,
                confidence_score=confidence,
                test_input_used=test_input,
                raw_output=exec_result.get("raw_output", ""),
                agent_notes=f"Reasoning: {reasoning}\n\nSuggestions: {suggestions}",
                execution_duration_ms=exec_result.get("duration_ms"),
            )

            # Step 5: Update skill verification status
            now = datetime.now(timezone.utc)
            if verdict == "PASSED":
                skill.last_verified_at = now
                skill.last_failure_reason = None
                # Auto-promote to ROBUST after 3 consecutive passes
                recent_passes = SkillVerification.objects.filter(
                    skill=skill, verdict="PASSED"
                ).count()
                if recent_passes >= 3 and not skill.is_robust:
                    skill.is_robust = True
                skill.save(update_fields=["last_verified_at", "last_failure_reason", "is_robust"])
            elif verdict == "FAILED":
                skill.last_failure_reason = reasoning[:500]
                skill.last_verified_at = now
                if skill.is_robust:
                    skill.is_robust = False
                skill.save(update_fields=["last_failure_reason", "last_verified_at", "is_robust"])

            logger.info(
                f"[SkillVerifier] Verification #{verification.id} for {skill.name}: {verdict} (confidence={confidence})"
            )

            return {
                "ok": True,
                "verification_id": verification.id,
                "verdict": verdict,
                "confidence": confidence,
                "exit_code": exec_result.get("exit_code"),
                "duration_ms": exec_result.get("duration_ms"),
                "raw_output": exec_result.get("raw_output", ""),
                "agent_notes": f"Reasoning: {reasoning}\n\nSuggestions: {suggestions}",
            }

        except Exception as e:
            logger.exception(f"[SkillVerifier] Error verifying skill #{skill_id}: {e}")
            return self._record_failure(
                SkillTemplate.objects.filter(id=skill_id).first(),
                f"System error: {e}",
            )

    def _generate_test_input(self, skill) -> dict:
        """Use LLM to construct test input from skill schema."""
        prompt = VERIFICATION_PROMPT.format(
            skill_name=skill.name,
            skill_description=skill.description or "",
            skill_language=skill.language,
            input_schema=json.dumps(skill.input_schema or {}, indent=2, ensure_ascii=False),
            output_schema=json.dumps(skill.output_schema or {}, indent=2, ensure_ascii=False),
            skill_instructions=skill.instructions or "",
            script_content=(skill.script_content or "")[:2000],
        )

        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            data = _extract_json(content)
            validated = VerifierTestInput(**data)
            test_input = validated.test_input or {}
            return {"test_input": test_input, "reasoning": validated.reasoning}
        except Exception as e:
            logger.warning(f"[SkillVerifier] LLM test input generation failed: {e}")
            if skill.test_input_example:
                return {"test_input": skill.test_input_example, "reasoning": "Used stored example"}
            return {"test_input": {}, "reasoning": "Fallback: empty input"}

    def _execute_skill(self, skill, test_input: dict) -> dict:
        """Execute skill script via Docker sandbox (bwrap-isolated).

        腳本透過 docker put_archive 直接寫入 container 的 /scripthub，
        不依賴 host volume（避免權限問題）。
        """
        import docker, io, tarfile, time

        ext = ".py" if skill.language.lower() == "python" else ".sh"
        runner = "python3" if skill.language.lower() == "python" else "bash"
        started_at = datetime.now(timezone.utc)
        tmp_filename = f"verify_{skill.id}_{int(time.time())}{ext}"
        host_tar_created = False

        try:
            client = docker.from_env()
            container = client.containers.get("c2_kali_sandbox")

            # 把腳本打包成 tar，用 put_archive 直接放進 container 的 /scripthub
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                data = (skill.script_content or "").encode("utf-8")
                info = tarfile.TarInfo(name=tmp_filename)
                info.size = len(data)
                info.mode = 0o755
                tar.addfile(info, io.BytesIO(data))
            tar_stream.seek(0)
            container.put_archive("/scripthub", tar_stream)
            host_tar_created = True

            sandbox_path = f"/scripthub/{tmp_filename}"

            # 確保獨立的 workspace（基於 skill_id，非 target_id）
            workspace = self._ensure_workspace(container, skill_id=skill.id)
            # 用 shlex.quote 包裹 JSON 字串為單一 shell 參數，避免 bash word splitting
            # （否則 JSON 內的空格會把 payload 切成多個 argv，sys.argv[1] 會變成檔名而非 JSON）
            import shlex
            cmd_parts = [runner, sandbox_path]
            if test_input:
                cmd_parts.append(shlex.quote(json.dumps(test_input)))
            bwrap_cmd = self._build_bwrap_command(
                " ".join(cmd_parts),
                workspace,
                sandbox_path,
            )

            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", bwrap_cmd],
                detach=False,
                stream=False,
            )

            # 清理腳本
            container.exec_run(
                cmd=["/bin/bash", "-c", f"rm -f {sandbox_path}"],
                detach=False,
                stream=False,
            )

            raw_output = output_bytes.decode("utf-8", errors="replace")
            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return {
                "exit_code": exit_code,
                "raw_output": raw_output,
                "duration_ms": duration_ms,
            }

        except docker.errors.NotFound:
            return {"error": "Sandbox container not found (c2_kali_sandbox)", "exit_code": -1}
        except Exception as e:
            return {"error": str(e), "exit_code": -1}

    @staticmethod
    def _ensure_workspace(container, skill_id: int) -> str:
        """為技能驗證建立臨時 workspace（/workspace/skill_<id>）。"""
        workspace = f"/workspace/skill_{skill_id}"
        container.exec_run(
            cmd=["/bin/bash", "-c", f"mkdir -p {workspace} && chmod 700 {workspace}"],
            detach=False,
            stream=False,
        )
        return workspace

    @staticmethod
    def _build_bwrap_command(command: str, workspace: str, sandbox_path: str) -> str:
        """建構 bwrap 包裝指令（與 SandboxMixin 同邏輯，但獨立實作避免循環依賴）。"""
        import shlex
        args = [
            "bwrap", "--die-with-parent",
            "--bind", workspace, workspace,
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--ro-bind", "/etc", "/etc",
            # scripthub 需要 bind，因為腳本在那裡
            "--ro-bind", "/scripthub", "/scripthub",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--unsetenv", "HOME",
            "--setenv", "HOME", workspace,
        ]
        wrapped = " ".join(shlex.quote(a) for a in args)
        wrapped += " /bin/bash -c " + shlex.quote(command)
        return wrapped

    def _evaluate_output(self, skill, test_input: dict, exit_code: int, raw_output: str) -> dict:
        """Use LLM to evaluate execution result."""
        prompt = EVALUATION_PROMPT.format(
            skill_name=skill.name,
            skill_description=skill.description or "",
            output_schema=json.dumps(skill.output_schema or {}, indent=2, ensure_ascii=False),
            test_input=json.dumps(test_input, indent=2, ensure_ascii=False),
            exit_code=exit_code,
            raw_output=(raw_output or "")[:3000],
        )

        try:
            response = self._llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            data = _extract_json(content)
            validated = VerifierEvalOutput(**data)
            return {
                "verdict": validated.verdict,
                "confidence": validated.confidence,
                "reasoning": validated.reasoning,
                "suggestions": validated.suggestions,
            }
        except Exception as e:
            logger.warning(f"[SkillVerifier] LLM output evaluation failed: {e}")
            if exit_code == 0 and raw_output and len(raw_output.strip()) > 0:
                return {
                    "verdict": "PASSED",
                    "confidence": 50,
                    "reasoning": f"Fallback heuristic: exit_code=0, output present. LLM error: {e}",
                    "suggestions": "",
                }
            return {
                "verdict": "FAILED",
                "confidence": 80,
                "reasoning": f"Fallback heuristic: exit_code={exit_code}. LLM error: {e}",
                "suggestions": "",
            }

    def _record_failure(self, skill, reason: str) -> dict:
        """Record a failed verification."""
        if skill is None:
            return {"ok": False, "error": reason}
        from apps.core.models.analyze.SkillVerification import SkillVerification

        SkillVerification.objects.create(
            skill=skill,
            verdict="ERROR",
            agent_notes=reason,
        )
        skill.last_failure_reason = reason[:500]
        skill.save(update_fields=["last_failure_reason"])
        return {"ok": False, "error": reason}
