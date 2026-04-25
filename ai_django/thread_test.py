import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setting")
django.setup()
from django_ai_assistant.models import Thread
from assistants import SimpleHelper

# 建立一個對話串
thread = Thread.objects.create()

# 傳入 thread_id，它就會記住上下文了！
assistant = SimpleHelper()
response1 = assistant.run("我叫小明", thread_id=thread.id)
response2 = assistant.run("我剛剛說我叫什麼？", thread_id=thread.id)  # 它會回答小明
print(response1)
print(response2)
