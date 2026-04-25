import logging
import os
from django.conf import settings
from django_ai_assistant import AIAssistant
from langchain_mistralai import ChatMistralAI

logger = logging.getLogger(__name__)

# Prompt Files
PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "ips_prompts.txt"
)
SUBDOMAIN_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "subdomains_prompts.txt"
)
URL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "urls_prompts.txt"
)
INITIAL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "initial_prompts.txt"
)


def _load_prompt(path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # Remove the literal placeholder, because the data will be sent in a distinct Thread message
            return content.replace("{$data}", "").strip()
    except FileNotFoundError:
        logger.error(f"Cannot find prompt template: {path}")
        return "You are a cybersecurity assistant. Analyze the provided asset data."


class AnalyzerMixin:
    # Use mistral-small-2603 as default since the previous pipeline uses it
    model = "mistral-small-2603"
    has_rag = False

    def get_llm(self):
        # We explicitly request JSON structured output for our agents
        return ChatMistralAI(
            model=self.model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
        )


class IPAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "ip_analyzer_agent"
    name = "IP Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(PROMPT_TEMPLATE_PATH)


class SubdomainAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "subdomain_analyzer_agent"
    name = "Subdomain Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(SUBDOMAIN_PROMPT_TEMPLATE_PATH)


class URLAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "url_analyzer_agent"
    name = "URL Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(URL_PROMPT_TEMPLATE_PATH)


class InitialAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "initial_analyzer_agent"
    name = "Initial Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(INITIAL_PROMPT_TEMPLATE_PATH)


def get_agent_for_asset_type(asset_type: str) -> AIAssistant:
    """Helper to return the correct agent instance based on short name."""
    if asset_type == "ip":
        return IPAnalyzerAgent()
    elif asset_type == "subdomain":
        return SubdomainAnalyzerAgent()
    elif asset_type == "url":
        return URLAnalyzerAgent()
    elif asset_type == "initial":
        return InitialAnalyzerAgent()
    raise ValueError(f"No agent defined for {asset_type}")
