"""
Skill Creator Agent
===================

專用技能創建代理，只負責生成符合 SkillTemplate 新架構的 script_body。

設計原則：
- AI 可「使用」已存在的 Skill（透過 execute_skill_script）
- AI 不應直接寫入 script_content — 應透過此代理創建技能
- 此代理確保 script_body 格式合法，並呼叫 assemble_full_script 組裝完整腳本

腳本格式規範：
  def main(inputs: SkillInput) -> None:
      # 業務邏輯
      ...

禁止在 script_body 裡使用：
  - sys.argv
  - argparse
  - print(json.dumps(...)) → 改用 _emit_output()
  - sys.exit()
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


SKILL_CREATOR_SYSTEM_PROMPT = """\
<role>
You are SkillCreatorAgent — a highly specialized code generator whose ONLY job is to write the
`script_body` for a SkillTemplate in a Django-based penetration testing platform.
</role>

<contract>
The platform wraps your script_body automatically with:
  1. Pydantic I/O Contract (SkillInput / SkillOutput classes)
  2. _parse_and_validate_input()  → validates JSON input from CLI arg[1]
  3. _emit_output(data: dict)     → validates and prints structured JSON output

You MUST write ONLY the `main()` function body (and any helpers).
You MUST NOT write: imports for sys/argparse/json, CLI arg parsing, print statements for output,
sys.exit() calls, or anything that handles I/O. The platform handles all I/O.
</contract>

<format_rules>
1. The FIRST function MUST be `def main(inputs: SkillInput) -> None:`.
   If the skill has no input schema, write `def main() -> None:`.
2. You MAY define helper functions BEFORE or AFTER main().
3. You MAY import third-party libraries inside the function body (they are installed in Kali sandbox).
4. Use `_emit_output({"key": value, "success": True})` to emit structured output.
5. Keep the script_body focused and minimal — no boilerplate.
</format_rules>

<example>
# Good script_body for a CSRF token fetcher:
import requests
from bs4 import BeautifulSoup

def fetch_csrf_token(url: str, session: requests.Session) -> str:
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    token_el = soup.find("input", {"name": "csrfmiddlewaretoken"})
    return token_el["value"] if token_el else ""

def main(inputs: SkillInput) -> None:
    session = requests.Session()
    token = fetch_csrf_token(inputs.url, session)
    _emit_output({"csrf_token": token, "success": bool(token)})
</example>

<output_contract>
Return ONLY the raw Python code for script_body. No markdown fences. No explanations.
Just the code. Start directly with any imports or helper functions needed.
</output_contract>
"""


def generate_script_body(
    task_description: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    language: str = "python",
    llm=None,
) -> str:
    """
    Use LLM to generate a spec-compliant script_body for the given task.

    Args:
        task_description: Natural language description of what the skill should do.
        input_schema: JSON Schema for input parameters.
        output_schema: JSON Schema for expected output.
        language: 'python' or 'bash'.
        llm: Optional LangChain LLM instance. If None, uses get_llm_instance().

    Returns:
        Generated script_body string ready to be stored in SkillTemplate.script_body.
    """
    import json

    if language != "python":
        # Bash skills don't use Pydantic — simpler prompt
        return _generate_bash_body(task_description, llm=llm)

    if llm is None:
        from apps.core.llms import get_llm_instance
        llm = get_llm_instance(temperature=0.1)

    # Build the user prompt with schema context
    input_desc = ""
    output_desc = ""

    if input_schema and input_schema.get("properties"):
        fields = []
        for fname, fschema in input_schema["properties"].items():
            req = " (required)" if fname in input_schema.get("required", []) else ""
            ftype = fschema.get("type", "any")
            fdesc = fschema.get("description", "")
            fields.append(f"  - {fname}: {ftype}{req} — {fdesc}")
        input_desc = "SkillInput fields available via inputs.FIELD_NAME:\n" + "\n".join(fields)
    else:
        input_desc = "No input schema defined. Use `def main() -> None:` (no inputs parameter)."

    if output_schema and output_schema.get("properties"):
        fields = []
        for fname, fschema in output_schema["properties"].items():
            req = " (required)" if fname in output_schema.get("required", []) else ""
            ftype = fschema.get("type", "any")
            fdesc = fschema.get("description", "")
            fields.append(f"  - {fname}: {ftype}{req} — {fdesc}")
        output_desc = "Call `_emit_output()` with these keys:\n" + "\n".join(fields)
    else:
        output_desc = "No output schema defined. Use `_emit_output({...})` with whatever makes sense for the task."

    user_prompt = f"""<task>
{task_description}
</task>

<input_contract>
{input_desc}
</input_contract>

<output_contract>
{output_desc}
</output_contract>

Write the Python script_body now:"""

    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=SKILL_CREATOR_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)
        return _clean_code_fences(raw)
    except Exception as e:
        logger.error(f"[SkillCreatorAgent] LLM call failed: {e}")
        raise RuntimeError(f"SkillCreatorAgent LLM error: {e}") from e


def _generate_bash_body(task_description: str, llm=None) -> str:
    """Generate a simple bash script body."""
    if llm is None:
        from apps.core.llms import get_llm_instance
        llm = get_llm_instance(temperature=0.1)

    from langchain_core.messages import SystemMessage, HumanMessage
    bash_prompt = """\
You are a bash script expert for a Kali Linux penetration testing environment.
Write a concise, practical bash script that solves the given task.
Output ONLY the raw bash script. No markdown fences. No explanations.
The script will be executed directly in a Kali Docker container."""

    messages = [
        SystemMessage(content=bash_prompt),
        HumanMessage(content=f"Task: {task_description}"),
    ]
    response = llm.invoke(messages)
    raw = response.content if hasattr(response, "content") else str(response)
    return _clean_code_fences(raw)


def _clean_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    import re
    # Remove ```python ... ``` or ``` ... ```
    text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()


def create_skill_from_spec(
    name: str,
    description: str,
    instructions: str,
    task_description: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    language: str = "python",
    tags: Optional[list] = None,
    llm=None,
) -> dict:
    """
    Full skill creation pipeline:
      1. Generate script_body via LLM
      2. Validate AST (for Python)
      3. Save SkillTemplate (triggers assemble_full_script + full_clean)
      4. Return result dict

    Args:
        name: Kebab-case skill name (unique).
        description: Short description (≤ 500 chars).
        instructions: How-to guide (≤ 2000 chars).
        task_description: Natural language description of what the script should do.
        input_schema: JSON Schema for inputs.
        output_schema: JSON Schema for outputs.
        language: 'python' or 'bash'.
        tags: List of tag strings.
        llm: Optional LLM instance.

    Returns:
        dict with keys: ok (bool), skill_id, skill_name, script_body, error (if any)
    """
    from apps.core.models.analyze.SkillTemplate import SkillTemplate
    from django.core.exceptions import ValidationError

    if tags is None:
        tags = []

    # Validate length constraints early
    if len(description) > 500:
        return {"ok": False, "error": f"description 超過 500 字 (目前 {len(description)} 字)"}
    if len(instructions) > 2000:
        return {"ok": False, "error": f"instructions 超過 2000 字 (目前 {len(instructions)} 字)"}

    # Step 1: Generate script_body
    try:
        script_body = generate_script_body(
            task_description=task_description,
            input_schema=input_schema,
            output_schema=output_schema,
            language=language,
            llm=llm,
        )
        logger.info(f"[SkillCreatorAgent] Generated script_body for '{name}' ({len(script_body)} chars)")
    except Exception as e:
        return {"ok": False, "error": f"LLM code generation failed: {e}"}

    # Step 2: Save SkillTemplate (clean() and save() do all validation + assembly)
    try:
        skill, created = SkillTemplate.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "instructions": instructions,
                "script_body": script_body,
                "language": language,
                "tags": tags,
                "input_schema": input_schema or {},
                "output_schema": output_schema or {},
            }
        )
        action = "Created" if created else "Updated"
        logger.info(f"[SkillCreatorAgent] {action} skill '{name}' (ID={skill.id})")

        return {
            "ok": True,
            "action": action,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "script_body": script_body,
            "script_content_length": len(skill.script_content or ""),
        }

    except ValidationError as e:
        logger.warning(f"[SkillCreatorAgent] ValidationError saving '{name}': {e}")
        return {
            "ok": False,
            "error": f"Validation failed: {e.message if hasattr(e, 'message') else str(e)}",
            "script_body": script_body,
        }
    except Exception as e:
        logger.exception(f"[SkillCreatorAgent] Unexpected error saving '{name}': {e}")
        return {"ok": False, "error": str(e)}
