import importlib.util
from importlib import import_module

from django.apps import AppConfig, apps


class AIAssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_assistant"

    def ready(self):
        # Register compression middleware signals
        from . import compression_middleware
        compression_middleware.register_compression_signals()
        
        # import all assistants.py files in all other apps to register the assistants:
        # We look for both 'assistants' and 'ai_assistants' modules
        for app in apps.get_app_configs():
            for module_name in ["assistants", "ai_assistants"]:
                try:
                    import_module(f"{app.name}.{module_name}")
                except ModuleNotFoundError:
                    # If the module exists but there is an error in it, we want to raise the error:
                    try:
                        if importlib.util.find_spec(f"{app.name}.{module_name}"):
                            raise
                    except ModuleNotFoundError:
                        pass
