import logging
from django.conf import settings
from apps.ai_assistant import AIAssistant
from apps.ai_assistant.prompts import AgentSpec, TaskDefinition
from apps.core.llms import get_llm_instance

logger = logging.getLogger(__name__)

INITIAL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "initial_prompts.txt"
)


def _load_prompt(path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            return content.replace("{$data}", "").strip()
    except FileNotFoundError:
        logger.error(f"Cannot find prompt template: {path}")
        return "You are a cybersecurity assistant. Analyze the provided asset data."


def _load_prompt_body(_agent) -> str:
    """作為 AgentSpec extra_sections 的 callable：載入 initial_prompts.txt 的全文。

    檔案內容已含 <input_format>/<output_schema>/<risk_score_guidelines> 等 section
    （加上開頭 <system_role>），為了不破壞既有結構，整份檔案作為單一 raw_body section
    注入；AgentSpec 的 <system_role> + <task_definition> 會在它之前。
    """
    return _load_prompt(INITIAL_PROMPT_TEMPLATE_PATH)


class AnalyzerMixin:
    has_rag = False

    def get_llm(self):
        return get_llm_instance(
            agent_id="initial_analyzer_agent",
            model_kwargs={"response_format": {"type": "json_object"}},
        )


# === 規格書 0 + 1 區塊：基本資訊 + 五欄位任務定義 ============================
# initial_prompts.txt 的靜態部分被提炼成五欄位；動態/詳細 section 仍由檔案載入
# （保留檔案為單一事實來源，避免內容漂移）。

_INITIAL_ANALYZER_SPEC = AgentSpec(
    name="Initial Analyzer Agent",
    role=(
        "對一批原始資產（IPs / Subdomains / URLs）執行初步分類分析的自動化代理。"
        "評估每個資產、推斷其主要用途、給予風險分數，以便高風險資產能被分組"
        "進行更深入的滲透測試。"
    ),
    task=TaskDefinition(
        goal=(
            "對輸入批次中的每個資產執行快速 triage：1 句摘要、推斷用途、"
            "0-100 風險分數、是否值得深入分析 (worth_deep_analysis)，"
            "並輸出符合 analysis_results schema 的 JSON。"
        ),
        background=(
            "在偵察階段產出大量資產後被呼叫，作為進入深入分析前的分級層。"
            "輸入可能附帶 strategic_context（先前 overview/plan/knowledge），"
            "需用來避免與既有知識矛盾。"
        ),
        materials=(
            "JSON 物件，含 list_of_assets；每個 asset 有 correlation_id、asset_data，"
            "可能有 strategic_context。asset_data 因資產類型而異（IP/Subdomain/URL）。"
            "詳細欄位見 <raw_body> 中的 <input_format> section。"
        ),
        boundary=(
            "1. 這是 PRELIMINARY triage — 嚴禁宣告已確認漏洞；只能推斷潛在價值。\n"
            "2. risk_score >=70 僅限於已知重大漏洞、暴露憑證、debug 工具、未授權內部服務；"
            "不可僅因發現活著的 web app 或 API 就給高分。\n"
            "3. 輸出必須是符合 schema 的合法 JSON（response_format 已強制 json_object）。\n"
            "4. 只讀分析，不執行任何主動掃描或攻擊。"
        ),
        dod=(
            "對輸入中每個 asset 輸出一筆 analysis_results 項目，含："
            "correlation_id（對應輸入）、summary（1 句）、inferred_purpose、"
            "risk_score（0-100，依 risk_score_guidelines）、worth_deep_analysis（boolean）。"
        ),
    ),
    extra_sections={"raw_body": _load_prompt_body},
    section_order=("raw_body",),
)


class InitialAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "initial_analyzer_agent"
    name = "Initial Asset Analyzer"
    SPEC = _INITIAL_ANALYZER_SPEC
    _REQUIRES_SPEC = True
