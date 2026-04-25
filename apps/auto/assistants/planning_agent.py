import logging
from django_ai_assistant import AIAssistant
from langchain_mistralai import ChatMistralAI
from apps.auto.tools.db_tools import DBToolsMixin

logger = logging.getLogger(__name__)


class AutomationAgent(AIAssistant, DBToolsMixin):
    id = "automation_agent"
    name = "Pentest Automation Agent"
    instructions = (
        "You are an expert penetration testing AI orchestrator. Your objective is to plan continuous security testing by reading the current tactical Overview and generating execution Steps. "
        "You have the capability to write to the database using your provided tools to update the target's abstract Overview or create concrete execution Steps (e.g., using nmap, nuclei, etc). "
        "You also have access to ALL the platform's internal scanning and discovery APIs as tools. Use them to trigger scans, fetch intelligence, and manage targets. "
        "Do not ask for user permission; operate autonomously based on the analysis context provided."
    )
    model = "mistral-small-2603"

    def get_llm(self):
        return ChatMistralAI(model=self.model, temperature=0)

    def get_tools(self):
        """
        組合工具集：
        1. 從父類別 (AIAssistant + DBToolsMixin) 取得 @method_tool 方法
        2. 從 CAI Factory 動態生成所有平台 API 工具（依賴 OpenAPI schema）
        """
        base_tools = super().get_tools()

        try:
            from apps.auto.cai.api_tool_factory import build_tools_from_openapi

            api_tools = build_tools_from_openapi(
                # 排除管理性/文件類端點，專注於行動類
                exclude_paths=["/api/assistant/", "/api/openapi", "/api/docs"]
            )
            logger.info(
                f"[AutomationAgent] 成功掛載 {len(api_tools)} 個平台 API 工具。"
            )
        except Exception as e:
            logger.error(f"[AutomationAgent] 無法載入平台 API 工具: {e}")
            api_tools = []

        return base_tools + api_tools

    def get_messages(self, thread_id: str):
        """
        覆寫 get_messages，為了限制規劃引擎 (Plan) 的上下文視窗大小。
        只提取最後 5 個 message，避免 token 爆炸。
        """
        messages = super().get_messages(thread_id)
        if len(messages) > 5:
            return messages[-5:]
        return messages
