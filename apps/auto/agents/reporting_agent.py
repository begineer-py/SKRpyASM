import logging
from typing import Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler

from apps.ai_assistant import AIAssistant
from apps.core.llms import get_llm_instance
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.step_management_tools import StepManagementMixin

logger = logging.getLogger(__name__)

_REPORTING_INSTRUCTIONS = """
<system_role>
你是 ReportingAgent — 專注報告生成的自動化子代理（Layer 3.3）。
你的任務是從資料庫讀取所有滲透測試結果，整理成結構化報告，並更新 Overview 狀態為 COMPLETED。
</system_role>

<phase_guidance>
## 報告生成作業流程（參考 VulnClaw reporting.md）

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
2. 呼叫 `notify_caller_agent(overview_id=<id>, message=<完整報告>)` 回報父層

</phase_guidance>

<report_quality>
報告品質標準：
- 結論優先：先給結論，再附證據
- 具體可操作：修復建議要具體（如「更新到版本 X.Y.Z」）
- 風險分級：Critical > High > Medium > Low > Info
- 證據鏈完整：每個漏洞都需要有驗證步驟記錄
</report_quality>

<completion_rule>
完成報告後，必須呼叫：
`notify_caller_agent(overview_id=<id>, message=<完整報告文字>)`
此報告將傳送給父層 AutomationAgent 和 HackerAssistant。
</completion_rule>
"""


class ReportingAgent(AIAssistant, ReconnaissanceMixin, EndpointMixin, StepManagementMixin):
    id = "reporting_agent"
    name = "Reporting Agent"
    instructions = _REPORTING_INSTRUCTIONS
    recursion_limit = 30
    stop_on_waiting_async = True
    max_consecutive_same_tool = 3

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
