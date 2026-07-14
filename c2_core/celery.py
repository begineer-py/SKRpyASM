# c2_core/celery.py

import os
from dotenv import load_dotenv  # 載入 .env 檔（本地 venv 模式用；預設不覆蓋既有變數，故 compose environment: 優先）
from celery import Celery
from django.conf import settings
from celery.signals import setup_logging # <--- 1. 引入日誌訊號

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")

app = Celery("c2_core")

# --- 核心配置 ---
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.task_serializer = settings.CELERY_TASK_SERIALIZER
app.conf.result_serializer = settings.CELERY_RESULT_SERIALIZER
app.conf.accept_content = settings.CELERY_ACCEPT_CONTENT
app.conf.timezone = settings.CELERY_TIMEZONE

# 操！把這行加進來，命令 Celery Beat 去讀取資料庫裡的作戰計劃
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
app.conf.task_acks_late = settings.CELERY_TASK_ACKS_LATE
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = settings.CELERY_WORKER_PREFETCH_MULTIPLIER

# 這一行會自動發現所有 app 下的 tasks.py 文件
app.autodiscover_tasks()


# ─── 2. 操！把這段加進來，強制 Celery 聽話使用 settings.py 的 LOGGING 配置 ───
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)