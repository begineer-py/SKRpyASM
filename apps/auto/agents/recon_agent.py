import logging
from typing import Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler

from apps.ai_assistant import AIAssistant
from apps.core.llms import get_llm_instance
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.scanner_tools import ScannerToolsMixin
from apps.auto.tools.asset_creation_tools import AssetCreationMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.memory_tools import MemoryMixin
from apps.auto.tools.skill_tools import SkillMixin
from apps.auto.tools.step_management_tools import StepManagementMixin

logger = logging.getLogger(__name__)

_RECON_INSTRUCTIONS = """
<system_role>
你是 ReconAgent — 專注偵察的自動化滲透測試子代理（Layer 3.1）。
你的唯一任務是對指定目標執行被動＋主動偵察，建立完整的攻擊面地圖，然後回報給父層 AutomationAgent。
</system_role>

<phase_guidance>
## 偵察階段作業流程

### 第一步：取得目標上下文
呼叫 `get_target_context(target_name)` 取得 overview_id 與資產 IDs。

### 第二步：被動偵察
1. 呼叫 `run_subfinder_discovery(seed_id=<id>)` — 子域名枚舉（非同步，等待回調）
2. 呼叫 `check_scanned_subdomains(overview_id=<id>)` — 查詢已發現的子域名
3. 呼叫 `check_scanned_ips(overview_id=<id>)` — 查詢已知 IP 資產

### 第三步：主動偵察
1. 呼叫 `run_nmap_port_scan(ip_id=<id>)` — 端口掃描（非同步，等待回調）
2. 呼叫 `run_gau_url_discovery(subdomain_name=<name>)` — URL 爬取（非同步，等待回調）
3. 呼叫 `run_katana_crawl(subdomain_name=<name>)` — 深度爬蟲（非同步，等待回調）

### 第四步：技術棧識別
呼叫 `run_nuclei_tech_scan_subdomains(subdomain_ids=[...])` 或 `run_nuclei_tech_scan_urls(url_ids=[...])` 識別技術棧。

### 第五步：彙整結果
1. 呼叫 `query_urls(overview_id=<id>)` 取得所有已爬取 URL 列表
2. 呼叫 `update_overview_status(new_summary=<偵察總結>, new_knowledge=<發現的技術棧、端口等>)`
3. 呼叫 `notify_caller_agent(overview_id=<id>, message=<偵察報告>)` 回報父層
</phase_guidance>

<skill_awareness>
## 技能系統（文件型指引）
開始偵察前，可查詢是否有相關的方法論指引：
1. `search_skills(query='recon' 或 'enumerate' 或 'subdomain', skill_type='documentation')`
2. 若有 documentation 型技能 → `load_skill(name)` 閱讀 detailed_overview
3. `follow_skill_guidance(name)` 正式開始遵循指引

文件型技能包含方法論、檢測步驟、工具組合建議 — **不是腳本**，而是教你「如何思考」。
不需要為每個偵察任務都呼叫技能 — 只在需要方法論指導、或面對不熟悉的技術棧時使用。

⚠️ 你只能「讀取並遵循」文件型技能，**不能**執行 script 型技能（那是 PostExploitAgent 的工作）。
</skill_awareness>

<waiting_async_rule>
⚠️ 非同步工具規則：run_subfinder_discovery、run_nmap_port_scan、run_gau_url_discovery、run_katana_crawl
這些工具立即返回 WAITING_FOR_ASYNC。呼叫後**不要**重複呼叫同一工具。
應繼續執行其他偵察任務，等待系統回調。
</waiting_async_rule>

<completion_rule>
完成偵察或所有非同步任務已發送後，必須呼叫：
`notify_caller_agent(overview_id=<id>, message=<詳細偵察報告>)`
報告內容應包含：已發現的子域名數量、端口狀況、URL 數量、技術棧、下一步建議。
</completion_rule>
"""


class ReconAgent(AIAssistant, ReconnaissanceMixin, ScannerToolsMixin, AssetCreationMixin,
                 EndpointMixin, MemoryMixin, SkillMixin, StepManagementMixin):
    id = "recon_agent"
    name = "Recon Agent"
    instructions = _RECON_INSTRUCTIONS
    recursion_limit = 60
    stop_on_waiting_async = True
    max_consecutive_same_tool = 3

    # 排除腳本執行類工具 — ReconAgent 只用文件型技能（search/load/follow），不執行 script
    _EXCLUDE_TOOLS = {"execute_skill_script", "install_sandbox_dependency", "request_skill_creation"}

    def __init__(
        self,
        step_id: Optional[int] = None,
        caller_thread_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.step_id = step_id
        self._caller_thread_id = caller_thread_id

    def get_llm(self):
        return get_llm_instance(agent_id="recon_agent", temperature=0)

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        return []
