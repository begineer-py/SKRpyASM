# agent_user_test.py
import os
import django

# 1. 啟動 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setting")
django.setup()

from django.contrib.auth.models import User
from django_ai_assistant import AIAssistant, method_tool
from django_ai_assistant.helpers.use_cases import create_thread

# ==========================================
# 步驟 A：準備一個 Django 使用者
# ==========================================
# 我們在資料庫裡抓一個使用者，沒有的話就建一個叫 "super_hacker"
my_user, created = User.objects.get_or_create(username="super_hacker")


# ==========================================
# 步驟 B：定義主 Agent (持有 User)
# ==========================================
class PersonalManagerAgent(AIAssistant):
    id = "personal_manager"
    name = "貼身總管"
    instructions = "你是使用者的專屬貼身管家。你可以讀取並修改主人的系統資料。請用簡潔的繁體中文回答。"
    model = "gemini-2.5-flash"

    def __init__(self, **kwargs):
        kwargs.setdefault("provider", "google")
        super().__init__(**kwargs)

    # 工具 1：讀取主人的資料
    @method_tool
    def get_my_info(self) -> str:
        """取得目前主人的帳號與信箱資訊"""
        # 【核心概念】：AI 直接存取它持有的 self._user
        if self._user:
            email = self._user.email or "尚未設定信箱"
            return f"主人帳號: {self._user.username}, 信箱: {email}"
        return "系統錯誤：AI 尚未綁定主人。"

    # 工具 2：修改主人的資料
    @method_tool
    def update_my_email(self, new_email: str) -> str:
        """更新目前主人的 Email"""
        # 【安全機制】：只更新 self._user 的資料，絕不碰其他人！
        if self._user:
            self._user.email = new_email
            self._user.save()
            return f"報告！已成功將主人的信箱更新為 {new_email}。"
        return "更新失敗。"


# ==========================================
# 步驟 C：實戰測試
# ==========================================

# 1. 建立一個對話串，並把這場對話歸屬於這個 user (解決你說的「沒名字」問題)
thread = create_thread(
    name="更新個人資料", user=my_user, assistant_id="personal_manager"
)
print(f"建立新對話！名稱: '{thread.name}', 擁有者: {thread.created_by.username}\n")

# 2. 喚醒主 Agent，並且把 user 託付給它（主 Agent 持有 User）
agent = PersonalManagerAgent(user=my_user)

# 測試 1：AI 認不認識主人？
print("👤 提問：我是誰？我的信箱是什麼？")
response1 = agent.run("我是誰？我的信箱是什麼？", thread_id=thread.id)
print(f"🤖 AI回答：{response1}\n")

# 測試 2：讓 AI 去改資料庫
print("👤 提問：幫我把信箱設定成 boss@django.com")
response2 = agent.run("幫我把信箱設定成 boss@django.com", thread_id=thread.id)
print(f"🤖 AI回答：{response2}\n")

# 測試 3：驗證 Django 資料庫是不是真的被 AI 改了！
my_user.refresh_from_db()
print("=========================================")
print(f"🔎 [系統驗證] 目前資料庫真實 Email：{my_user.email}")
print("=========================================")
