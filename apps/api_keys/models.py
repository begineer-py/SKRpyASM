from django.db import models


class AgentLLMConfig(models.Model):
    """每個 Agent 的 LLM 獨立配置，可透過 API 管理，覆蓋 env var 默認值。"""

    agent_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Agent 識別碼，例如 'automation_agent'",
    )
    provider = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="LLM 提供商：openai / anthropic / mistral / deepseek / ollama",
    )
    model_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="模型名稱，例如 gpt-4o、claude-3-opus-20240229",
    )
    temperature = models.FloatField(
        null=True,
        blank=True,
        help_text="溫度 0.0–2.0；None 表示沿用全域默認值",
    )
    api_base_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="自定義 API Base URL（代理 / 私有部署用）",
    )
    api_key_ref = models.ForeignKey(
        "core.APIKey",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agent_configs",
        help_text="指向特定 APIKey 記錄；None 則回退到全域同廠商密鑰",
    )
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "api_keys"
        db_table = "api_keys_agentllmconfig"
        verbose_name = "Agent LLM 配置"
        verbose_name_plural = "Agent LLM 配置"

    def __str__(self):
        return f"{self.agent_id} ({self.provider or 'default'}/{self.model_name or 'default'})"
