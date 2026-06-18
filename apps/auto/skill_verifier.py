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


VERIFICATION_PROMPT = """<role>
You are a Skill Verification Agent. Your job is to validate whether a registered
penetration testing skill is working correctly.
</role>

<skill_context>
<name>{skill_name}</name>
<description>{skill_description}</description>
<language>{skill_language}</language>
<input_schema>{input_schema}</input_schema>
<output_schema>{output_schema}</output_schema>
<instructions>
{skill_instructions}
</instructions>
<script_content>
{script_content}
</script_content>
</skill_context>

<task>
Construct a realistic test input for this skill based on its input_schema and instructions.
</task>

<output_format>
Return ONLY valid JSON with this exact structure:
{{
  "test_input": {{ ... }},
  "reasoning": "Why this test input was chosen"
}}
</output_format>

<constraints>
- test_input must conform to the input_schema if defined
- If no input_schema, provide an empty object
- The input should be a realistic target for penetration testing (use example.com or 127.0.0.1)
- reasoning must be in Traditional Chinese
</constraints>
"""

EVALUATION_PROMPT = """<role>
You are a Skill Output Evaluation Agent. Your job is to evaluate whether a skill's
execution output matches the expected result.
</role>

<skill_context>
<name>{skill_name}</name>
<description>{skill_description}</description>
<expected_output_schema>{output_schema}</expected_output_schema>
</skill_context>

<execution_details>
<test_input_used>{test_input}</test_input_used>
<exit_code>{exit_code}</exit_code>
<raw_output>{raw_output}</raw_output>
</execution_details>

<task>
Analyze the execution output and determine if this skill executed successfully.
</task>

<output_format>
Return ONLY valid JSON with this exact structure:
{{
  "verdict": "PASSED" | "FAILED" | "INCONCLUSIVE",
  "confidence": 0-100,
  "reasoning": "Detailed analysis in Traditional Chinese",
  "suggestions": "Any suggestions for improvement or notes about the output"
}}
</output_format>

<verdict_criteria>
- PASSED: Exit code 0 AND output matches the expected schema/structure
- FAILED: Exit code non-zero OR output is clearly wrong/empty
- INCONCLUSIVE: Cannot clearly determine success or failure
</verdict_criteria>
"""


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
        """Execute skill script via Docker sandbox."""
        import docker, tempfile, os, subprocess

        host_sandbox_dir = "/tmp/c2_sandbox_scripts"
        os.makedirs(host_sandbox_dir, exist_ok=True)

        ext = ".py" if skill.language.lower() == "python" else ".sh"
        runner = "python3" if skill.language.lower() == "python" else "bash"
        started_at = datetime.now(timezone.utc)

        try:
            client = docker.from_env()
            container = client.containers.get("c2_kali_sandbox")

            with tempfile.NamedTemporaryFile(
                dir=host_sandbox_dir, suffix=ext, delete=False, mode="w", encoding="utf-8"
            ) as f:
                f.write(skill.script_content or "")
                tmp_filename = os.path.basename(f.name)
                host_path = f.name

            sandbox_path = f"/scripthub/{tmp_filename}"

            # Pass input_json as first CLI arg (JSON string)
            args = json.dumps(test_input) if test_input else ""
            exit_code, output_bytes = container.exec_run(
                cmd=[runner, sandbox_path, args],
                detach=False,
                stream=False,
            )

            if os.path.exists(host_path):
                os.remove(host_path)

            raw_output = output_bytes.decode("utf-8", errors="replace")
            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return {
                "exit_code": exit_code,
                "raw_output": raw_output,
                "duration_ms": duration_ms,
            }

        except docker.errors.NotFound:
            if "host_path" in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return {"error": "Sandbox container not found (c2_kali_sandbox)", "exit_code": -1}
        except Exception as e:
            if "host_path" in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return {"error": str(e), "exit_code": -1}

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
