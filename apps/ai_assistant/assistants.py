from django_ai_assistant import AIAssistant, method_tool
from langchain_mistralai import ChatMistralAI
from langchain_community.tools import (
    ShellTool,
    FileSearchTool,
    ListDirectoryTool,
    WriteFileTool,
    ReadFileTool,
    DuckDuckGoSearchResults,
)


class PersonalManagerAgent(AIAssistant):
    id = "personal_manager_agent"
    name = "Personal Manager Agent"
    instructions = (
        "You are a personal manager agent. "
        "Your core engine is Mistral AI. Never claim to be built by OpenAI, Azure, or 'GPT-4'."
    )
    model = "mistral-small-2603"

    def get_llm(self):
        return ChatMistralAI(
            model=self.model,
            temperature=0,  # 可以調整隨機性
            # 套件會自動去讀取環境變數 MISTRAL_API_KEY
        )

    @method_tool
    def get_current_time_and_date(self) -> str:
        """Get the current time and date"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class HackerAssistantAgent(AIAssistant):
    id = "hacker_assistant_agent"
    name = "Hacker Assistant"
    instructions = (
        "You are a sophisticated Hacker Assistant capable of executing shell commands, retrieving "
        "hardware metrics, and executing raw database queries. "
        "CRITICAL RULES: "
        "1. Always read the previous conversation history BEFORE answering or using a tool. "
        "2. If the user refers to past citations, messages, or context, rely on the chat history. "
        "3. Do NOT use search tools or other tools if the answer can be synthesized from the existing conversation history. "
        "4. Your core engine is Mistral AI. Never claim to be built by OpenAI, Azure, or 'GPT-4'. You are C2 Hacker Assistant built with Mistral."
    )
    model = "mistral-small-2603"

    def get_llm(self):
        return ChatMistralAI(
            model=self.model,
            temperature=0,
        )

    def get_tools(self):
        from langchain_community.utilities import SQLDatabase
        from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
        from django.conf import settings

        db_settings = settings.DATABASES["default"]
        username = db_settings.get("USER", "postgres")
        password = db_settings.get("PASSWORD", "")
        host = db_settings.get("HOST", "localhost")
        port = db_settings.get("PORT", "5432")
        db_name = db_settings.get("NAME", "postgres")

        # Use psycopg2 driver for PostgreSQL
        db_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{db_name}"
        db = SQLDatabase.from_uri(db_uri)

        my_custom_tools = [
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            ShellTool(),
            FileSearchTool(),
            DuckDuckGoSearchResults(),
            QuerySQLDataBaseTool(db=db),
        ]
        tools = super().get_tools()
        for tool in my_custom_tools:
            tools.append(tool)
        return tools

    @method_tool
    def get_server_temperature(self) -> str:
        """Retrieve the current hardware/CPU temperature of the server."""
        import subprocess

        try:
            # First try using sensors command directly
            result = subprocess.run(
                "sensors", shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "temp" in result.stdout.lower():
                return result.stdout

            # Alternative fallback: reading thermal zone directly
            result = subprocess.run(
                "cat /sys/class/thermal/thermal_zone*/temp",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                temps = [f"{int(t)/1000}°C" for t in result.stdout.strip().split("\n")]
                return "Thermal Zones: " + ", ".join(temps)

            return "Command executed successfully but no temperature data found. Check if lm-sensors is installed."
        except Exception as e:
            return f"Unable to fetch temperature: {str(e)}"
