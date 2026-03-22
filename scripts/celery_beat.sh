#!/bin/bash
# scripts/celery_beat.sh
# 啟動 Celery Beat (不使用 eventlet 猴子補丁，避免資料庫衝突)

echo "📅 啟動 Celery Beat 排程器..."
python manage.py celery beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
