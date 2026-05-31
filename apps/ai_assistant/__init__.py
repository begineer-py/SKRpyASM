from importlib import metadata

from apps.ai_assistant.helpers.assistants import (
    AIAssistant,
)
from apps.ai_assistant.langchain.tools import (
    BaseModel,
    BaseTool,
    Field,
    StructuredTool,
    Tool,
    method_tool,
    tool,
)


PACKAGE_NAME = __package__ or "django-ai-assistant"

try:
    VERSION = __version__ = metadata.version(PACKAGE_NAME)
except metadata.PackageNotFoundError:
    # Package is not installed, use a default version
    VERSION = __version__ = "dev"


__all__ = [
    "AIAssistant",
    "BaseModel",
    "BaseTool",
    "Field",
    "StructuredTool",
    "Tool",
    "method_tool",
    "tool",
    "PACKAGE_NAME",
    "VERSION",
]
