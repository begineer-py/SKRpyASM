from django.apps import AppConfig


class AnalyzeAiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analyze_ai"

    def ready(self):
        import apps.analyze_ai.assistants  # noqa
