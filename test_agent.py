import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings')
django.setup()

import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('httpcore').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.INFO)

from django_ai_assistant.models import Thread
from django_ai_assistant.helpers.assistants import AIAssistant

print("STARTING TEST...")
sys.stdout.flush()

thread = Thread.objects.get(id=106)
assistant_cls = AIAssistant.get_cls(thread.assistant_id)
assistant = assistant_cls(thread=thread)

try:
    res = assistant.run('Please start pentesting AIS3', thread=thread)
    print("RESULT:", res)
except Exception as e:
    import traceback
    traceback.print_exc()

