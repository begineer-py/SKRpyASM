import logging
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class SpawnAgentsMixin:
    """
    Sub-Agent Spawning Tools Mixin
    Gives AutomationAgent the ability to launch specialized sub-agents
    (ReconAgent, PostExploitAgent, ReportingAgent) as background Celery tasks.

    Each spawned agent:
    - Runs independently in the background
    - Receives the caller's thread_id so it can report back via notify_caller_agent()
    - Has a focused system prompt and limited tool set for its phase
    """

    def _get_caller_thread_id(self) -> int | None:
        thread = getattr(self, "_thread", None)
        if thread:
            return thread.id
        return None

    @method_tool
    def spawn_recon_agent(
        self,
        target_name: str,
        objective: str = "",
    ) -> str:
        """
        [Sub-Agent] 啟動一個專注偵察的 ReconAgent 子代理在背景非同步執行。

        ReconAgent 會自動執行：子域名枚舉 (subfinder)、端口掃描 (nmap)、
        URL 爬取 (gau/katana)、技術棧識別 (nuclei)，完成後透過 notify_caller_agent 回報。

        使用時機：
        - 目標還沒有足夠的偵察資料時
        - 需要深度枚舉子域名或端口時
        - 想要在自己繼續工作的同時並行執行偵察時

        Args:
            target_name: 要偵察的目標名稱（必須已存在於資料庫）
            objective: 偵察目標說明（如 "找出所有開放的 API 端點" 或 "識別技術棧"）
        """
        try:
            from apps.auto.tasks import run_recon_agent_async

            caller_thread_id = self._get_caller_thread_id()
            message = f"對目標 '{target_name}' 執行完整偵察。"
            if objective:
                message += f"\n偵察重點：{objective}"

            run_recon_agent_async.delay(
                message=message,
                target_name=target_name,
                caller_thread_id=caller_thread_id,
            )

            return (
                f"✅ ReconAgent 已在背景啟動，目標：{target_name}。\n"
                f"偵察任務將異步執行，完成後會透過 notify_caller_agent 回報結果。\n"
                f"你可以繼續執行其他任務，無需等待。"
            )
        except Exception as e:
            logger.error(f"[SpawnAgents] spawn_recon_agent failed: {e}")
            return f"啟動 ReconAgent 失敗：{e}"

    @method_tool
    def spawn_post_exploit_agent(
        self,
        target_name: str,
        foothold_info: str = "",
    ) -> str:
        """
        [Sub-Agent] 啟動一個專注後滲透的 PostExploitAgent 子代理在背景非同步執行。

        PostExploitAgent 會自動執行：環境確認、內網信息收集、憑證搜集、橫向移動嘗試，
        完成後透過 notify_caller_agent 回報。

        使用時機：
        - 已確認取得初始訪問權限（RCE、Shell、任意命令執行）後
        - 需要執行內網橫向移動時
        - 需要收集憑證和敏感資訊時

        ⚠️ 前提條件：必須已確認存在可利用的漏洞或已獲得初始訪問。

        Args:
            target_name: 目標名稱
            foothold_info: 已獲取的立足點描述（如 "通過 RCE 漏洞在 /cmd 端點獲得命令執行" 或 "已獲得 admin shell"）
        """
        try:
            from apps.auto.tasks import run_post_exploit_agent_async

            caller_thread_id = self._get_caller_thread_id()
            message = f"對目標 '{target_name}' 執行後滲透活動。"
            if foothold_info:
                message += f"\n已確認的立足點：{foothold_info}"

            run_post_exploit_agent_async.delay(
                message=message,
                target_name=target_name,
                caller_thread_id=caller_thread_id,
            )

            return (
                f"✅ PostExploitAgent 已在背景啟動，目標：{target_name}。\n"
                f"後滲透任務將異步執行（環境確認 → 內網偵察 → 橫向移動），完成後回報。\n"
                f"你可以繼續執行其他任務，無需等待。"
            )
        except Exception as e:
            logger.error(f"[SpawnAgents] spawn_post_exploit_agent failed: {e}")
            return f"啟動 PostExploitAgent 失敗：{e}"

    @method_tool
    def spawn_reporting_agent(
        self,
        overview_id: int = None,
        target_name: str = "",
    ) -> str:
        """
        [Sub-Agent] 啟動一個專注報告生成的 ReportingAgent 子代理在背景非同步執行。

        ReportingAgent 會自動從資料庫讀取所有漏洞、步驟、偵察發現，
        整理成結構化的滲透測試報告，更新 Overview 狀態為 COMPLETED，
        並透過 notify_caller_agent 將報告回報給你。

        使用時機：
        - 所有測試階段完成後需要生成最終報告時
        - 需要整理所有發現到一份結構化文件時
        - 想要自動更新 Overview 狀態為 COMPLETED 時

        Args:
            overview_id: 要生成報告的 Overview ID（自動注入）
            target_name: 目標名稱（overview_id 和 target_name 提供其一即可）
        """
        try:
            from apps.auto.tasks import run_reporting_agent_async

            caller_thread_id = self._get_caller_thread_id()

            if not overview_id and not target_name:
                return "CRITICAL_FAILURE: 必須提供 overview_id 或 target_name 其中之一。"

            message = "生成滲透測試最終報告。"
            if target_name:
                message += f"\n目標：{target_name}"
            if overview_id:
                message += f"\nOverview ID：{overview_id}"

            run_reporting_agent_async.delay(
                message=message,
                target_name=target_name,
                overview_id=overview_id,
                caller_thread_id=caller_thread_id,
            )

            return (
                f"✅ ReportingAgent 已在背景啟動。\n"
                f"報告生成任務將異步執行，完成後會透過 notify_caller_agent 回傳完整報告。\n"
                f"你可以繼續執行其他任務，無需等待。"
            )
        except Exception as e:
            logger.error(f"[SpawnAgents] spawn_reporting_agent failed: {e}")
            return f"啟動 ReportingAgent 失敗：{e}"
