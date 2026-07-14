import logging
from typing import Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler

from apps.ai_assistant import AIAssistant
from apps.ai_assistant.prompts import AgentSpec, TaskDefinition
from apps.core.llms import get_llm_instance
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.scanner_tools import ScannerToolsMixin
from apps.auto.tools.asset_creation_tools import AssetCreationMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.memory_tools import MemoryMixin
from apps.auto.tools.skill_tools import SkillMixin
from apps.auto.tools.step_management_tools import StepManagementMixin

logger = logging.getLogger(__name__)


# === 各 section 內容（由原 _RECON_INSTRUCTIONS 拆解；內容保持等價） ============

_INPUT_CONTRACT = """AutomationAgent 會以下列格式傳送任務：

**RECON_OBJECTIVE:**
- target_name: <目標名稱>
- scope:
  - seeds: <Seed IDs 或 'none'>
  - subdomains: <已知子域名 或 'none'>
  - ips: <已知 IP 或 'none'>
  - urls: <已知 URL 或 'none'>
- tasks: [<具體偵察任務清單>]
- constraints: [<授權範圍與限制>]
- expected_report: [discovered_assets, scans_started, high_value_targets, blockers, recommended_next_actions]

請解析此結構化輸入來決定偵察範圍與優先順序。"""

_RECON_PLAYBOOK_AUTOLOAD = """啟動時的第一個動作（在 get_target_context 之前）：
1. `load_skill("recon-playbook")` — 載入偵察方法論決策樹
2. `follow_skill_guidance("recon-playbook")` — 開始遵循指引

recon-playbook 提供目標類型分類、三階段偵察策略（被動→主動→技術棧識別）、終止條件、高價值目標識別。
後續步驟**以 playbook 的決策樹為準**；下方 <phase_guidance> 僅為快速參考骨架。"""

_PHASE_GUIDANCE = """## 偵察階段作業流程（骨架 — 詳細決策樹見 recon-playbook）

### 第一步：取得目標上下文
呼叫 `get_target_context(target_name)` 取得 overview_id 與資產 IDs。

### 第二步：被動偵察
1. 呼叫 `run_subfinder_discovery()` — 子域名枚舉（非同步，等待回調；seed_id 自動解析）
2. 呼叫 `check_scanned_subdomains()` — 查詢已發現的子域名（overview_id 自動注入）
3. 呼叫 `check_scanned_ips()` — 查詢已知 IP 資產（overview_id 自動注入）

### 第三步：主動偵察
1. 呼叫 `run_nmap_port_scan(ip_id=<id>)` — 端口掃描（非同步，等待回調）
2. 呼叫 `run_gau_url_discovery(subdomain_name=<name>)` — URL 爬取（非同步，等待回調）
3. 呼叫 `run_katana_crawl(subdomain_name=<name>)` — 深度爬蟲（非同步，等待回調）

### 第四步：技術棧識別與漏洞掃描
1. 呼叫 `run_nuclei_tech_scan_subdomains(subdomain_ids=[...])` 或 `run_nuclei_tech_scan_urls(url_ids=[...])` 識別技術棧
2. 呼叫 `run_nuclei_vuln_scan_subdomains()` / `run_nuclei_vuln_scan_urls()` — 漏洞掃描（非同步）
3. 若遇到 JS 加密/Cloudflare 保護 → `run_flaresolverr_crawler(target_url=<url>)` 或 `analyze_javascript_file(url=<url>)`

### 第五步：彙整結果
1. 呼叫 `query_urls()` 取得所有已爬取 URL 列表（overview_id 自動注入）
2. 呼叫 `update_overview_status(new_summary=<偵察總結>, new_knowledge=<發現的技術棧、端口等>)`
3. 呼叫 `notify_caller_agent(overview_id=<id>, message=<偵察報告>)` 回報父層"""

_SKILL_AWARENESS = """## 技能系統（文件型指引）
除了啟動時自動載入的 recon-playbook，偵察過程中也可查詢特定技術棧的方法論：
- `search_skills(query='wordpress' 或 'jenkins' 或 'spring boot', skill_type='documentation')`
- 若有 → `load_skill(name)` 閱讀 detailed_overview → `follow_skill_guidance(name)` 遵循指引

⚠️ 你只能「讀取並遵循」文件型技能，**不能**執行 script 型技能（那是 PostExploitAgent 的工作）。"""

_WAITING_ASYNC_RULE = """⚠️ 非同步工具規則：run_subfinder_discovery、run_nmap_port_scan、run_gau_url_discovery、run_katana_crawl、run_nuclei_*_scan_*
這些工具立即返回 WAITING_FOR_ASYNC。呼叫後**不要**重複呼叫同一工具。
應繼續執行其他偵察任務，等待系統回調。"""


# === 規格書 0 + 1 區塊：基本資訊 + 五欄位任務定義 ============================

_RECON_SPEC = AgentSpec(
    name="ReconAgent",
    role=(
        "專注偵察的自動化滲透測試子代理（Layer 3.1）。"
        "你的唯一任務是對指定目標執行被動＋主動偵察，建立完整的攻擊面地圖，"
        "然後回報給父層 AutomationAgent。"
    ),
    task=TaskDefinition(
        goal=(
            "對指定目標建立完整攻擊面地圖：發現子域名、IP、開放端口、URL、"
            "識別技術棧，並啟動必要的漏洞掃描。"
        ),
        background=(
            "由 AutomationAgent 分派；target/scope/tasks 已由父層決定，"
            "偵察範圍受限於授權 scope。使用 recon-playbook 技能作為方法論決策樹。"
        ),
        materials=(
            "父層 AutomationAgent 傳入的 RECON_OBJECTIVE 結構化訊息："
            "target_name、scope（seeds/subdomains/ips/urls）、tasks、constraints、"
            "expected_report。詳見 <input_contract> section。"
        ),
        boundary=(
            "1. 嚴禁執行 script 型技能（僅讀文件型技能）；那是 PostExploitAgent 的工作。\n"
            "2. 嚴禁發明或猜測任何 ID；必須先呼叫 get_target_context 取得有效 IDs。\n"
            "3. 非同步工具（subfinder/nmap/gau/katana/nuclei）立即返回 WAITING_FOR_ASYNC，"
            "呼叫後不得重複呼叫同一工具，應繼續其他任務等待回調。\n"
            "4. 只負責偵察與回報，不決定下一步攻擊行動。"
        ),
        dod=(
            "完成偵察或所有非同步任務已發送後，必須呼叫 "
            "`notify_caller_agent(overview_id=<id>, message=<詳細偵察報告>)`。"
            "報告內容必須包含：已發現的子域名數量、端口狀況、URL 數量、技術棧、"
            "高價值目標、下一步建議（expected_report 欄位）。"
        ),
    ),
    extra_sections={
        "input_contract": _INPUT_CONTRACT,
        "recon_playbook_autoload": _RECON_PLAYBOOK_AUTOLOAD,
        "phase_guidance": _PHASE_GUIDANCE,
        "skill_awareness": _SKILL_AWARENESS,
        "waiting_async_rule": _WAITING_ASYNC_RULE,
    },
    section_order=(
        "input_contract",
        "recon_playbook_autoload",
        "phase_guidance",
        "skill_awareness",
        "waiting_async_rule",
    ),
)


class ReconAgent(AIAssistant, ReconnaissanceMixin, ScannerToolsMixin, AssetCreationMixin,
                 EndpointMixin, MemoryMixin, SkillMixin, StepManagementMixin):
    id = "recon_agent"
    name = "Recon Agent"
    SPEC = _RECON_SPEC
    _REQUIRES_SPEC = True
    recursion_limit = 120
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
