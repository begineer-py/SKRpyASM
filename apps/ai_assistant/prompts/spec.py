"""AgentSpec / PromptSpec — 結構化 prompt 框架核心實作。

設計依據（規格書 0/1 區塊）：
  0. 基本資訊：name / role
  1. 任務定義：Goal / Background / Materials / Boundary / DoD

兩種 Spec 共用同一個 TaskDefinition，但 render 方式不同：
  - AgentSpec : render 成系統提示字串，供 AIAssistant.get_instructions() 使用
  - PromptSpec: 含 .format() 樣板與 output_schema，提供 invoke() 一條龍

向後相容：未定義 SPEC 的 agent 會退回使用 instructions 屬性。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, Union

from pydantic import BaseModel

if TYPE_CHECKING:
    from apps.ai_assistant.helpers.assistants import AIAssistant

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 共用工具
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """從 LLM 回應文字中萃取 JSON dict。

    處理三種情境：
      1. 純 JSON
      2. markdown code block (```json ... ``` 或 ``` ... ```)
      3. 文字中夾帶的 { ... }（取最外層）

    萃取失敗回傳空 dict（與既有 utility agent 行為一致）。
    """
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
                return json.loads(text[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass
    return {}


# ---------------------------------------------------------------------------
# 1. 任務定義（五欄位）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaskDefinition:
    """規格書區塊 1：任務定義（承襲五欄位）。

    frozen=True → class 定義時即驗證欄位存在（少一欄位會 TypeError）。
    每個欄位對應規格書的一個小節，皆為必填、不得為空字串。
    render 時會做非空檢查並 raise，避免空欄位流入 prompt。
    """

    goal: str
    """1.1 目標 — 該 Agent 必須達成的單一具體任務目標。避免包含非本步驟的任務。"""

    background: str
    """1.2 背景 — 執行此步驟所需的上下文（付費等級、歷史對話摘要、上層分派來源等）。"""

    materials: str
    """1.3 素材 — 輸入資料來源。明確指出是來自上一級 Agent 的 JSON 輸出，還是用戶的原生輸入。"""

    boundary: str
    """1.4 邊界 — 限制條件。例如「嚴禁自行回答專業問題，僅能進行分類」。"""

    dod: str
    """1.5 完成定義 (Definition of Done) — 內部驗證機制。例如「輸出必須包含 category 與 confidence」。"""

    def __post_init__(self) -> None:
        _SEC_NUM = {
            "goal": "1.1", "background": "1.2", "materials": "1.3",
            "boundary": "1.4", "dod": "1.5",
        }
        for fname in ("goal", "background", "materials", "boundary", "dod"):
            val = getattr(self, fname)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(
                    f"TaskDefinition.{fname} 不得為空（規格書欄位 {_SEC_NUM[fname]}）"
                )

    def render(self) -> str:
        """Render 成 <task_definition> 區塊（含五個小節）。"""
        return "\n".join([
            f"## Goal\n{self.goal}",
            f"## Background\n{self.background}",
            f"## Materials\n{self.materials}",
            f"## Boundary\n{self.boundary}",
            f"## Definition of Done\n{self.dod}",
        ])


# ---------------------------------------------------------------------------
# 2. AgentSpec — AIAssistant 子類用
# ---------------------------------------------------------------------------

# extra_sections 的值可為靜態字串或 callable(agent) -> str（動態內容）
SectionValue = Union[str, Callable[["AIAssistant"], str]]


@dataclass(frozen=True)
class AgentSpec:
    """規格書區塊 0 + 1 + 額外 section — 供 AIAssistant 子類（多輪 Agent）使用。

    使用方式（agent 類別定義）::

        class ReconAgent(AIAssistant, ...):
            SPEC = AgentSpec(
                name="ReconAgent",
                role="...",
                task=TaskDefinition(goal=..., background=..., ...),
                extra_sections={"phase_guidance": "..."},
            )

    之後 AIAssistant.get_instructions() 會自動呼叫 SPEC.render_for(self)。
    """

    name: str
    """規格 0：Agent 名稱／角色（例如 ReconAgent）。"""

    role: str
    """規格 0：系統定位 — 該 Agent 在整個 Multi-Agent 工作流中處於什麼位置。"""

    task: TaskDefinition
    """規格 1：五欄位任務定義。"""

    extra_sections: dict[str, SectionValue] = field(default_factory=dict)
    """額外的 XML section（如 phase_guidance / input_contract / completion_rule）。
    順序由 section_order 決定；值可為靜態字串或 callable(self) -> str。"""

    section_order: tuple[str, ...] = ()
    """額外 section 的輸出順序；為空時使用 extra_sections 的插入順序。"""

    render_tool_catalog: bool = False
    """混合策略：是否從 agent.get_tools() 自動反射基本工具目錄。
    True 時會在末尾加上 <available_tool_catalog>（name + docstring 摘要）。
    複雜決策樹仍應放在 extra_sections["tool_decision_tree"] 手寫補充。"""

    def __post_init__(self) -> None:
        """驗證 section_order 與 extra_sections 一致性（防呆）。

        若 section_order 非空，其內每個 key 都必須存在於 extra_sections；
        否則 raise ValueError — 避免 render_for 靜默跳過（section_order 中的 key
        若不在 extra_sections 會被 `if sec_name not in self.extra_sections: continue`
        略過，造成 section 靜默消失）。

        反向（extra_sections 有 key 但 section_order 沒列）為合法行為：
        section_order 為空時 fallback 到 dict 插入順序；非空時該 key 不被 render。
        """
        if self.section_order:
            unknown = set(self.section_order) - set(self.extra_sections.keys())
            if unknown:
                raise ValueError(
                    f"AgentSpec.section_order 含未知 key {sorted(unknown)}；"
                    f"不在 extra_sections 中。請檢查拼字或將其加入 extra_sections。"
                )

    # 預設 section 順序：system_role → task_definition → extra sections → tool_catalog
    def render_for(self, agent: "AIAssistant") -> str:
        """組裝完整系統提示。

        Args:
            agent: 對應的 AIAssistant 實例（供 callable section 與工具反射使用）。
        """
        parts: list[str] = [
            _wrap("system_role", f"你是 {self.name} — {self.role}"),
            _wrap("task_definition", self.task.render()),
        ]

        order = self.section_order or tuple(self.extra_sections.keys())
        for sec_name in order:
            if sec_name not in self.extra_sections:
                continue
            content = self.extra_sections[sec_name]
            if callable(content):
                try:
                    content = content(agent)
                except Exception:
                    logger.exception("AgentSpec section %r render 失敗", sec_name)
                    continue
            if content:
                parts.append(_wrap(sec_name, content))

        if self.render_tool_catalog:
            catalog = _reflect_tool_catalog(agent)
            if catalog:
                parts.append(_wrap("available_tool_catalog", catalog))

        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# 3. PromptSpec — utility agent 用
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PromptSpec:
    """供 utility agent（一次性 LLM 呼叫）使用。

    將既有的 .format() 樣板 prompt 收斂成單一宣告式結構：
      - system_role + task_definition（五欄位）+ template_body 組裝成完整 prompt
      - output_schema 提供 invoke() 一條龍：format → llm.invoke → extract_json → pydantic 驗證

    使用範例::

        VERIFICATION_SPEC = PromptSpec(
            name="SkillVerifier",
            role="驗證技能是否正常運作",
            task=TaskDefinition(...),
            template_body="<skill_context>...</skill_context>\n<task>...</task>",
            output_schema=VerifierEvalOutput,
            agent_id="skill_verifier_agent",
            temperature=0.2,
        )

        result = VERIFICATION_SPEC.invoke(skill_name=..., exit_code=...)
        # result: 已驗證的 Pydantic 物件
    """

    name: str
    """規格 0：Agent 名稱／角色。"""

    role: str
    """規格 0：系統定位。"""

    task: TaskDefinition
    """規格 1：五欄位任務定義。"""

    template_body: str
    """樣板主體（含 {placeholders}）。會接在 system_role + task_definition 之後。"""

    output_schema: Optional[Type[BaseModel]] = None
    """輸出 Pydantic schema。invoke() 會用它驗證 extract_json 結果。
    None 表示不驗證，invoke 直接回傳 dict。"""

    agent_id: Optional[str] = None
    """對應 get_llm_instance(agent_id=...)；None 表示用預設 LLM。"""

    temperature: Optional[float] = 0.0
    """LLM 溫度；None 表示使用 get_llm_instance 預設。"""

    output_format_hint: Optional[str] = None
    """輸出格式提示（自動附加在 template_body 末尾）。
    預設會從 output_schema 生成「回傳 ONLY 合法的 JSON」提示。"""

    def __post_init__(self) -> None:
        # 確保 template_body 不含未跳脫的 format-brace 造成 KeyError
        # （此處不攔截，留待 format() 自然報錯，訊息更清楚）
        pass

    # ---- render ----

    def render(self, **format_kwargs: Any) -> str:
        """組裝完整 prompt 並填入 format_kwargs。

        結構：
            <system_role>你是 {name} — {role}</system_role>
            <task_definition>...</task_definition>
            {template_body 填入 format_kwargs}
            <output_format>...</output_format>   # 若有 output_schema
        """
        head = _wrap("system_role", f"你是 {self.name} — {self.role}")
        task_block = _wrap("task_definition", self.task.render())
        body = self.template_body.format(**format_kwargs)
        parts = [head, task_block, body]

        hint = self.output_format_hint or self._default_output_hint()
        if hint:
            parts.append(_wrap("output_format", hint))

        return "\n\n".join(parts)

    def _default_output_hint(self) -> Optional[str]:
        if self.output_schema is None:
            return None
        schema = self.output_schema.model_json_schema()
        props = schema.get("properties", {})
        fields_desc = ", ".join(
            '"{}" ({})'.format(k, v.get("type", "any")) for k, v in props.items()
        )
        return (
            "回傳 ONLY 合法的 JSON（不要 markdown code block，不要解釋文字），"
            "欄位：{}。".format(fields_desc)
        )

    # ---- invoke 一條龍 ----

    def format(self, **format_kwargs: Any) -> str:
        """Alias of render() — 與既有 .format() 用法對齊。"""
        return self.render(**format_kwargs)

    def invoke(self, **format_kwargs: Any) -> Union[BaseModel, dict]:
        """format → llm.invoke → extract_json → output_schema 驗證。

        Returns:
            若 output_schema 有設定，回傳驗證後的 Pydantic 物件；
            否則回傳 extract_json 的 dict（可能為空 {}）。

        Raises:
            原始 LLM 例外會往外拋；schema 驗證失敗則回傳 dict（容錯）。
        """
        prompt = self.render(**format_kwargs)
        llm = self._get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        data = extract_json(content)
        if self.output_schema is None:
            return data
        try:
            return self.output_schema(**data)
        except Exception as exc:
            logger.warning(
                "PromptSpec[%s] output_schema 驗證失敗 (%s)；回傳原始 dict", self.name, exc
            )
            return data

    def parse(self, raw_text: str) -> Union[BaseModel, dict]:
        """單獨解析 LLM 回應（不呼叫 LLM）。與 invoke() 的解析邏輯一致。"""
        data = extract_json(raw_text)
        if self.output_schema is None:
            return data
        try:
            return self.output_schema(**data)
        except Exception as exc:
            logger.warning(
                "PromptSpec[%s] parse 驗證失敗 (%s)；回傳原始 dict", self.name, exc
            )
            return data

    def _get_llm(self):
        """延遲 import 避免循環依賴；取得 LLM 實例。"""
        from apps.core.llms import get_llm_instance
        kwargs: dict[str, Any] = {}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return get_llm_instance(agent_id=self.agent_id, **kwargs)


# ---------------------------------------------------------------------------
# 内部 helpers
# ---------------------------------------------------------------------------

def _wrap(tag: str, body: str) -> str:
    """以 pseudo-XML tag 包裹 body（維持既有 prompt 風格）。"""
    return f"<{tag}>\n{body}\n</{tag}>"


def _reflect_tool_catalog(agent: "AIAssistant") -> str:
    """從 agent.get_tools() 反射工具清單（name + docstring 摘要）。

    混合策略：基本清單自動反射，避免手寫 catalog 與實際工具漂移；
    複雜決策樹由 extra_sections 補充。
    """
    try:
        tools = agent.get_tools()
    except Exception:
        logger.debug("AgentSpec: get_tools() 失敗，略過工具目錄反射", exc_info=True)
        return ""
    if not tools:
        return ""
    lines = ["## Available Tools (auto-reflected)"]
    for tool in tools:
        name = getattr(tool, "name", str(tool))
        desc = getattr(tool, "description", "") or ""
        desc = desc.strip().split("\n", 1)[0][:200]
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)
