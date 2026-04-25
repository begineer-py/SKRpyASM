from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_assistant"

    def ready(self):
        # Import to trigger the metaclass registration
        import apps.ai_assistant.assistants  # noqa
