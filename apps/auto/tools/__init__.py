"""
apps/auto/tools/__init__.py

導出所有自動化工具，供 AI Agent 調用。
"""

from .graphql import query_graphql, mutate_graphql
from .graphql_docs import get_graphql_schema_info
from .system_api import (
    list_targets,
    create_target,
    list_seeds,
    add_seed,
    trigger_subfinder_recon,
    trigger_nuclei_vulnerability_scan,
    trigger_nmap_scan,
    list_scheduled_tasks,
    create_scheduled_task,
    trigger_gau_url_discovery,
    trigger_crawler_flaresolverr,
    trigger_endpoint_fuzzing
)
