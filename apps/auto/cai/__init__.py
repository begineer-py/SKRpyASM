"""
apps/auto/cai/__init__.py

導出 auto app 的 CAI 工具和配置。
"""

from .platform_tools import *
from .agent_configs import *
from .ai_analysis_tools import *
from .core.tool import Tool, function_tool
from .core.session import ShellSession, run_command
