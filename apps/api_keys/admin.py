from django.contrib import admin
from apps.core.models.api_key import APIKey
from apps.api_keys.models import AgentLLMConfig

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("service_name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("service_name", "description")


@admin.register(AgentLLMConfig)
class AgentLLMConfigAdmin(admin.ModelAdmin):
    list_display = ("agent_id", "provider", "model_name", "temperature", "is_active", "updated_at")
    list_filter = ("provider", "is_active")
    search_fields = ("agent_id", "description")
    raw_id_fields = ("api_key_ref",)
