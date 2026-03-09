"""
apps/auto/cai/agent_configs.py

Configuration for different AI Agent roles within the auto app.
"""

from .platform_tools import (
    get_subdomains_info,
    get_ips_info,
    trigger_subfinder,
    trigger_nuclei_scan
)
# Assuming these standard tools are available in the cai package
from cai.tools.reconnaissance.generic_linux_command import generic_linux_command
from cai.tools.misc.reasoning import reasoning

# -----------------------------------------------------------------------------
# Agent Roles
# -----------------------------------------------------------------------------

RECON_AGENT_CONFIG = {
    "name": "ReconAgent",
    "instructions": (
        "You are a specialized Reconnaissance Agent. Your goal is to discover and detail target assets. "
        "Use 'get_subdomains_info' and 'get_ips_info' to understand current assets, and "
        "'trigger_subfinder' or 'trigger_nuclei_scan' (tech stack) to discover more."
    ),
    "tools": [
        get_subdomains_info,
        get_ips_info,
        trigger_subfinder,
        trigger_nuclei_scan,
        generic_linux_command,
        reasoning
    ]
}

EXPLOIT_AGENT_CONFIG = {
    "name": "ExploitAgent",
    "instructions": (
        "You are an Exploitation & Vulnerability Assessment Agent. Your goal is to identify and verify security risks. "
        "Review asset details and use 'trigger_nuclei_scan' (vulnerabilities) to probe for risks."
    ),
    "tools": [
        get_subdomains_info,
        get_ips_info,
        trigger_nuclei_scan,
        generic_linux_command,
        reasoning
    ]
}
