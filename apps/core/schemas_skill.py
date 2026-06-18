from ninja import Schema
from typing import Optional
from datetime import datetime


class SkillOut(Schema):
    id: int
    name: str
    description: str
    instructions: str
    script_content: Optional[str] = None
    script_body: Optional[str] = None
    language: str
    tags: list
    usage_count: int
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    is_robust: bool
    is_deprecated: bool
    has_io_contract: bool
    version: int
    last_verified_at: Optional[datetime] = None
    last_failure_reason: Optional[str] = None
    test_input_example: Optional[dict] = None
    merged_from: Optional[list] = None
    created_at: datetime
    updated_at: datetime


class SkillCreate(Schema):
    name: str
    description: str
    instructions: str
    language: str = "python"
    tags: Optional[list] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    script_body: Optional[str] = None
    script_content: Optional[str] = None


class SkillUpdate(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[list] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    script_body: Optional[str] = None
    script_content: Optional[str] = None
    is_deprecated: Optional[bool] = None


class SkillTestRequest(Schema):
    test_input: Optional[dict] = None   # optional: if provided, used instead of LLM auto-generation


class SkillTestOut(Schema):
    ok: bool
    verification_id: Optional[int] = None
    verdict: Optional[str] = None          # PASSED / FAILED / INCONCLUSIVE
    confidence: Optional[int] = None       # 0-100 scale (already from backend, do NOT multiply)
    error: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None
    raw_output: Optional[str] = None       # truncated to ~2000 chars for safety
    agent_notes: Optional[str] = None      # LLM evaluation reasoning
