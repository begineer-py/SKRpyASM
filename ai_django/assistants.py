from django_ai_assistant import AIAssistant, method_tool
from django.utils import timezone
class SimpleHelper(AIAssistant):
    model = "gemini-2.5-flash"
    name = "萬能小幫手"
    id = "shop_assistant"
    description = "一個可以幫你查詢時間、天氣和計算數學的萬能小幫手"
    instructions = """
    你是一個有禮貌的AI小幫手。
    1. 當使用者問時間，請用繁體中文回答。
    2. 當使用者問天氣，請用繁體中文回答。
    3. 當使用者問數學，請用繁體中文回答。
    """
    def __init__(self, **kwargs):
        kwargs.setdefault("provider", "google")
        super().__init__(**kwargs)
    @method_tool
    def get_server_time(self) -> str:
        """取得目前伺服器的確切時間"""
        return str(timezone.now())
    def run(self, message: str, thread_id=None, **kwargs):
        # 先呼叫原本的 run 拿到結果
        raw_response = super().run(message, thread_id=thread_id, **kwargs)
        
        # 幫忙清理 Google Gemini 的結構
        if isinstance(raw_response, list) and len(raw_response) > 0:
            if isinstance(raw_response[0], dict) and 'text' in raw_response[0]:
                return raw_response[0]['text']
                
        return raw_response
from django_ai_assistant.models import Thread

# 建立一個對話串
thread = Thread.objects.create()

# 傳入 thread_id，它就會記住上下文了！
