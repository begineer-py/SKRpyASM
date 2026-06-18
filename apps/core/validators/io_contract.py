"""
Pydantic I/O Contract Generator

Automatically generates Pydantic validation code from SkillTemplate's
input_schema / output_schema and wraps it into the script_content.

Python skills only — Bash skills cannot use Pydantic validation.
"""
from __future__ import annotations

import json
from typing import Any, Optional


def _schema_to_pydantic_field(
    field_name: str,
    field_schema: dict,
    required_fields: set | None = None,
    indent: int = 4,
) -> str:
    """Convert a single JSON Schema property to a Pydantic field definition.

    Args:
        field_name: The field name.
        field_schema: The JSON Schema for this property.
        required_fields: Set of required field names (from parent schema's ``required`` array).
            Fields in this set are rendered as non-Optional, no-default fields.
        indent: Indentation spaces.
    """
    pad = " " * indent
    required_fields = required_fields or set()
    field_type = field_schema.get("type", "Any")
    description = field_schema.get("description", "")

    # map JSON types to Python types
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
        "null": "None",
    }
    py_type = type_map.get(field_type, "Any")

    is_required = field_name in required_fields
    has_explicit_default = "default" in field_schema

    # --- Collect Field() kwargs ---
    field_kwargs: list[str] = []

    if is_required:
        # Required: no default, non-Optional. Pydantic enforces presence.
        if description:
            field_kwargs.append(f"description={json.dumps(description)}")
    else:
        # Optional: wrap in Optional, provide default
        py_type = f"Optional[{py_type}]"
        if has_explicit_default:
            field_kwargs.append(f"default={json.dumps(field_schema['default'])}")
        else:
            field_kwargs.append("default=None")
        if description:
            field_kwargs.append(f"description={json.dumps(description)}")

    # Pattern validation for strings
    pattern = field_schema.get("pattern")
    if pattern and field_type == "string":
        field_kwargs.append(f"pattern={json.dumps(pattern)}")

    # Numeric constraints
    minimum = field_schema.get("minimum")
    maximum = field_schema.get("maximum")
    if minimum is not None:
        field_kwargs.append(f"ge={minimum}")
    if maximum is not None:
        field_kwargs.append(f"le={maximum}")

    # Enum validation
    enum_values = field_schema.get("enum")
    if enum_values:
        field_kwargs.append(f"enum={json.dumps(enum_values)}")

    if field_kwargs:
        return f"{pad}{field_name}: {py_type} = Field({', '.join(field_kwargs)})"
    return f"{pad}{field_name}: {py_type}"


def _schema_to_pydantic_model(model_name: str, schema: dict) -> str:
    """Convert a full JSON Schema object to a Pydantic BaseModel class string."""
    if not schema or not isinstance(schema, dict):
        return ""

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    lines = [f"class {model_name}(BaseModel):"]
    if not properties:
        lines.append("    pass")
        return "\n".join(lines)

    for field_name, field_schema in properties.items():
        pydantic_field = _schema_to_pydantic_field(
            field_name, field_schema, required_fields=required_fields
        )
        lines.append(pydantic_field)

    # Add model_config
    lines.append("")
    lines.append("    model_config = ConfigDict(extra='forbid')")
    return "\n".join(lines)


def _generate_input_wrapper(input_schema: dict) -> str:
    """Generate the input validation wrapper code."""
    if not input_schema:
        return ""
    return '''
def _parse_and_validate_input() -> SkillInput:
    """Parse CLI args or stdin JSON, validate against SkillInput schema."""
    import sys, json
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input", "success": False}))
        sys.exit(1)
    try:
        return SkillInput(**data)
    except Exception as e:
        print(json.dumps({"error": f"Input validation failed: {e}", "success": False}))
        sys.exit(1)
'''


def _generate_output_wrapper(output_schema: dict) -> str:
    """Generate the output validation wrapper code."""
    if not output_schema:
        return ""
    return '''
def _emit_output(data: dict) -> None:
    """Validate and emit structured output."""
    try:
        validated = SkillOutput(**data)
        print(json.dumps(validated.model_dump()))
    except Exception as e:
        print(json.dumps({"error": f"Output validation failed: {e}", "success": False}))
        sys.exit(1)
'''


def generate_io_contract(
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
) -> str:
    """Generate the complete I/O contract wrapper code for a Python skill.

    Args:
        input_schema: JSON Schema dict for input validation.
        output_schema: JSON Schema dict for output validation.

    Returns:
        Python source code string containing the I/O contract wrapper.
        Returns empty string if both schemas are empty.
    """
    if not input_schema and not output_schema:
        return ""

    parts = [
        "# === AUTO-GENERATED I/O CONTRACT (Pydantic) ===",
        "from pydantic import BaseModel, Field, ConfigDict",
        "from typing import Optional, Any, List, Dict",
        "import json, sys",
        "",
    ]

    # Generate input model
    if input_schema:
        input_model_code = _schema_to_pydantic_model("SkillInput", input_schema)
        parts.append(input_model_code)
        parts.append("")

    # Generate output model
    if output_schema:
        output_model_code = _schema_to_pydantic_model("SkillOutput", output_schema)
        parts.append(output_model_code)
        parts.append("")

    # Generate wrapper functions
    wrapper = _generate_input_wrapper(input_schema) + _generate_output_wrapper(output_schema)
    parts.append(wrapper)
    parts.append("# === END I/O CONTRACT ===")
    parts.append("")

    return "\n".join(parts)


def inject_io_contract(
    script_content: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
) -> str:
    """Wrap existing script_content with auto-generated I/O contract code.

    The generated code provides _parse_and_validate_input() and _emit_output()
    helper functions that the script can call at entry/exit points.

    Args:
        script_content: The original Python script source code.
        input_schema: JSON Schema for input validation.
        output_schema: JSON Schema for output validation.

    Returns:
        The script with I/O contract prepended (if any schema provided).
        Returns original script unchanged if no schemas given.
    """
    wrapper = generate_io_contract(input_schema, output_schema)
    if not wrapper:
        return script_content
    return wrapper + "\n" + script_content


class IOContractGenerator:
    """High-level interface for generating I/O contracts on SkillTemplate."""

    @staticmethod
    def wrap_skill(
        script_content: str,
        language: str,
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
    ) -> str:
        """Wrap a skill's script with I/O contract.

        Only wraps Python skills with at least one schema defined.
        Bash skills are returned unchanged.
        """
        if language != "python":
            return script_content
        if not input_schema and not output_schema:
            return script_content
        return inject_io_contract(script_content, input_schema, output_schema)

    @staticmethod
    def extract_pydantic_models(
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
    ) -> str:
        """Extract just the Pydantic model definitions (no wrappers)."""
        parts = []
        parts.append("from pydantic import BaseModel, Field, ConfigDict")
        parts.append("from typing import Optional, Any, List, Dict")
        parts.append("")
        if input_schema:
            parts.append(_schema_to_pydantic_model("SkillInput", input_schema))
            parts.append("")
        if output_schema:
            parts.append(_schema_to_pydantic_model("SkillOutput", output_schema))
            parts.append("")
        return "\n".join(parts)


def assemble_full_script(
    script_body: str,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
) -> str:
    """從 script_body + schema 組裝完整的可執行腳本。

    組裝順序：
    1. I/O Contract header（Pydantic 模型 + _parse_and_validate_input + _emit_output）
    2. script_body（AI 撰寫的 main() 函式）
    3. Entrypoint（main(_parse_and_validate_input()) 呼叫）

    Returns:
        完整的 Python 腳本字串，可直接在 sandbox 中執行
    """
    parts = []
    io_header = generate_io_contract(input_schema, output_schema)
    if io_header:
        parts.append(io_header)
    parts.append(script_body)
    if input_schema:
        parts.append("\nif __name__ == '__main__':\n    main(_parse_and_validate_input())\n")
    else:
        parts.append("\nif __name__ == '__main__':\n    main()\n")
    return "\n".join(parts)

