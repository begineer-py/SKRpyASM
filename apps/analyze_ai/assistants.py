import logging
from django.conf import settings
from django_ai_assistant import AIAssistant
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


class AnalyzerMixin:
    has_rag = False

    def get_llm(self):
        return get_llm_instance(
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
        )


class InitialAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "initial_analyzer_agent"
    name = "Initial Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(INITIAL_PROMPT_TEMPLATE_PATH)
