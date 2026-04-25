# setting.py

# 1. 安全金鑰 (隨便打一串即可，開發測試用)
SECRET_KEY = "django-insecure-ai-demo-key"

# 2. 開啟除錯模式
DEBUG = True

# 3. 允許的連線主機
ALLOWED_HOSTS = ["*"]

# 4. 安裝的 Apps (把我們剛剛介紹的套件放進來)
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_ai_assistant",
]

# 5. 資料庫設定 (預設使用 SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
# 設定 URLconf
ROOT_URLCONF = "ai_django.urls"
