import logging
from celery import shared_task
from c2_core.config.logging import log_function_call
from django_ai_assistant import AIAssistant, method_tool
from django_ai_assistant.helpers.use_cases import create_thread

logger = logging.getLogger(__name__)


class PlanCreator:
    def __init__(self):
        self.assistant = AIAssistant()

    @method_tool
    def create_plan(self):
        pass


@shared_task(name="auto.tasks.create_plan")
@log_function_call()
def create_plan():
    plan_creator = PlanCreator()
    plan_creator.create_plan()
