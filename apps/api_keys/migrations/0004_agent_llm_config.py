import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api_keys", "0003_move_apikey_to_core"),
        ("core", "0012_cve_cwe_ids_nullable"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentLLMConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "agent_id",
                    models.CharField(
                        help_text="Agent 識別碼，例如 'automation_agent'",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        blank=True,
                        help_text="LLM 提供商：openai / anthropic / mistral / deepseek / ollama",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "model_name",
                    models.CharField(
                        blank=True,
                        help_text="模型名稱，例如 gpt-4o、claude-3-opus-20240229",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "temperature",
                    models.FloatField(
                        blank=True,
                        help_text="溫度 0.0–2.0；None 表示沿用全域默認值",
                        null=True,
                    ),
                ),
                (
                    "api_base_url",
                    models.CharField(
                        blank=True,
                        help_text="自定義 API Base URL（代理 / 私有部署用）",
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "api_key_ref",
                    models.ForeignKey(
                        blank=True,
                        help_text="指向特定 APIKey 記錄；None 則回退到全域同廠商密鑰",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_configs",
                        to="core.apikey",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "description",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Agent LLM 配置",
                "verbose_name_plural": "Agent LLM 配置",
                "db_table": "api_keys_agentllmconfig",
            },
        ),
    ]
