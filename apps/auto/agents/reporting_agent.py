import logging
from typing import Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler

from apps.ai_assistant import AIAssistant
from apps.ai_assistant.prompts import AgentSpec, TaskDefinition
from apps.core.llms import get_llm_instance
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.step_management_tools import StepManagementMixin
from apps.auto.assistants.workflow_prompts import WORKFLOW_ROUTING_TABLE

logger = logging.getLogger(__name__)


# === 各 section 內容（由原 _REPORTING_INSTRUCTIONS 拆解；內容保持等價） ========

_INPUT_CONTRACT = """AutomationAgent 會以下列格式傳送任務：

**REPORTING_REQUEST:**
- include: [steps, vulnerabilities, attack_vectors, assets, evidence, remediation]
- target_focus: <目標名稱或 overview_id>
- expected_output: [executive_summary, scope, confirmed_findings, evidence, risk_score, remediation, final_status]

請依此結構產出報告。"""

_PHASE_GUIDANCE = """## 報告生成作業流程

### 第一步：收集所有發現
1. 呼叫 `get_target_context(target_name)` 取得 overview_id
2. 呼叫 `query_steps(overview_id=<id>)` 取得所有 execution graph/node 狀態
3. 呼叫 `get_url_intelligence(url_id=<id>)` 查詢關鍵 URL 的詳細資訊（選擇性）

### 第二步：整理漏洞清單
從步驟歷史和資料庫中收集：
- 確認的漏洞（Vulnerabilities）
- 攻擊向量（AttackVectors）
- 偵察發現（subdomains、ports、URLs、tech stack）

### 第三步：生成結構化報告
使用 `update_overview_status` 更新以下欄位：

**summary（執行摘要）**：
```
## 滲透測試報告摘要
- 目標：<target_name>
- 發現高危漏洞：<count> 個
- 風險評分：<score>/100

### 關鍵發現
1. <漏洞名稱> — <嚴重等級> — <位置>
2. ...

### 技術棧
<已識別的技術棧>

### 修復建議
<優先建議>
```

**knowledge（結構化數據）**：
```json
{
  "report_generated": true,
  "total_vulnerabilities": <count>,
  "critical": <count>,
  "high": <count>,
  "attack_surface": "<subdomains>個子域名, <urls>個URL",
  "key_findings": ["<finding1>", "<finding2>"]
}
```

### 第四步：標記完成
1. 呼叫 `update_overview_status(new_status="COMPLETED", new_risk_score=<final_score>)`
2. 呼叫 `notify_caller_agent(overview_id=<id>, message=<完整報告>)` 回報父層"""

# WORKFLOW_ROUTING_TABLE 已含 <workflow_routing> 外層 tag，剝離避免框架二次包裝
_ROUTING_TABLE_INNER = WORKFLOW_ROUTING_TABLE.strip()
_ROUTING_TABLE_INNER = _ROUTING_TABLE_INNER[
    len("<workflow_routing>"):-len("</workflow_routing>")
].strip()

_REPORT_QUALITY = """報告品質標準：
- 結論優先：先給結論，再附證據
- 具體可操作：修復建議要具體（如「更新到版本 X.Y.Z」）
- 風險分級：Critical > High > Medium > Low > Info
- 證據鏈完整：每個漏洞都需要有驗證步驟記錄"""


# === 規格書 0 + 1 區塊：基本資訊 + 五欄位任務定義 ============================

_REPORTING_SPEC = AgentSpec(
    name="ReportingAgent",
    role=(
        "專注報告生成的自動化子代理（Layer 3.3）。"
        "你的任務是從資料庫讀取所有滲透測試結果，整理成結構化報告，"
        "並更新 Overview 狀態為 COMPLETED。"
    ),
    task=TaskDefinition(
        goal=(
            "從資料庫讀取所有滲透測試結果（漏洞、攻擊向量、資產、證據），"
            "整理成結構化報告，計算風險評分，並將 Overview 標記為 COMPLETED。"
        ),
        background=(
            "由 AutomationAgent 分派；通常在偵察與後滲透階段完成後呼叫。"
            "ReportingAgent 是唯一直接標記 Overview 為 COMPLETED 的角色。"
        ),
        materials=(
            "父層 AutomationAgent 傳入的 REPORTING_REQUEST 結構化訊息："
            "include（要收錄的項目）、target_focus、expected_output。"
            "實際資料來自資料庫（query_steps、get_url_intelligence 等）。"
            "詳見 <input_contract> section。"
        ),
        boundary=(
            "1. 嚴禁發明或猜測任何 ID；必須先呼叫 get_target_context 取得有效 IDs。\n"
            "2. 嚴禁呼叫 record_vulnerability（已排除此工具）；只負責讀取與報告。\n"
            "3. 嚴禁執行新的攻擊／掃描；只彙整既有結果。\n"
            "4. 報告必須含證據鏈，每個漏洞都需要有驗證步驟記錄。"
        ),
        dod=(
            "完成報告後，必須："
            "(1) 呼叫 update_overview_status(new_status=\"COMPLETED\", new_risk_score=<final_score>)，"
            "(2) 呼叫 notify_caller_agent(overview_id=<id>, message=<完整報告文字>)。"
            "報告將傳送給父層 AutomationAgent 和 HackerAssistant。"
        ),
    ),
    extra_sections={
        "input_contract": _INPUT_CONTRACT,
        "phase_guidance": _PHASE_GUIDANCE,
        "workflow_routing": _ROUTING_TABLE_INNER,
        "report_quality": _REPORT_QUALITY,
    },
    section_order=(
        "input_contract",
        "phase_guidance",
        "workflow_routing",
        "report_quality",
    ),
)


class ReportingAgent(AIAssistant, ReconnaissanceMixin, EndpointMixin, StepManagementMixin):
    id = "reporting_agent"
    name = "Reporting Agent"
    SPEC = _REPORTING_SPEC
    _REQUIRES_SPEC = True
    recursion_limit = 100
    stop_on_waiting_async = True
    max_consecutive_same_tool = 3

    # ReportingAgent 只負責讀取與報告，不應建立漏洞記錄
    _EXCLUDE_TOOLS = {"record_vulnerability"}

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
        return get_llm_instance(agent_id="reporting_agent", temperature=0)

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        return []
