#!/usr/bin/env python3
"""
scripts/setup_auto_scheduler.py

向 Scheduler API 註冊「自動滲透啟動」定時任務。
─────────────────────────────────────────────
用途:
  在系統初始化或更新後，透過呼叫 Django Scheduler API 自動建立
  `trigger_auto_pentest_from_analysis` 定時任務。

使用方式:
  python scripts/setup_auto_scheduler.py

環境變數可覆寫預設值:
  BASE_URL          — Django 服務根網址 (預設: http://localhost:8000)
  INTERVAL_MINUTES  — 定時間隔（分鐘） (預設: 5)
  TASK_NAME         — 定時任務顯示名稱  (預設: Auto Pentest - 分析轉換觸發器)
  BATCH_SIZE        — 每次批次處理筆數  (預設: 5)
  AUTO_REUSE        — 任務已存在時自動更新 (預設: true)
"""

import os
import sys
import json
import requests

# ─────────────────────────────────
# 設定
# ─────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "1"))
TASK_NAME = os.environ.get("TASK_NAME", "Auto Pentest - 分析轉換觸發器")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "5"))
AUTO_REUSE = os.environ.get("AUTO_REUSE", "true").lower() != "false"

SCHEDULER_API = f"{BASE_URL}/api/scheduler/tasks"
CELERY_TASK_PATH = "scheduler.tasks.trigger_auto_pentest_from_analysis"


def print_section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main():
    print_section("🚀 Auto Pentest 排程任務註冊")
    print(f"  API 目標     : {SCHEDULER_API}")
    print(f"  任務名稱     : {TASK_NAME}")
    print(f"  Celery 任務  : {CELERY_TASK_PATH}")
    print(f"  執行間隔     : 每 {INTERVAL_MINUTES} 分鐘")
    print(f"  批次大小     : {BATCH_SIZE} 筆")

    # 1. 先查詢是否已存在同名任務
    try:
        list_resp = requests.get(SCHEDULER_API, timeout=10)
        list_resp.raise_for_status()
        existing_tasks = list_resp.json()
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 錯誤: 無法連接到 {BASE_URL}，請確認 Django 伺服器正在運行。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: 查詢現有任務失敗: {e}")
        sys.exit(1)

    existing = next((t for t in existing_tasks if t["name"] == TASK_NAME), None)

    if existing:
        print(f"\n⚠️  發現同名任務 (ID: {existing['id']})，{'將進行更新' if AUTO_REUSE else '跳過建立'}。")
        if not AUTO_REUSE:
            print("   提示: 設定 AUTO_REUSE=true 可自動更新現有任務。")
            sys.exit(0)

        # 更新現有任務
        update_url = f"{SCHEDULER_API}/{existing['id']}"
        update_payload = {
            "interval": {"every": INTERVAL_MINUTES, "period": "minutes"},
            "enabled": True,
            "kwargs": json.dumps({"batch_size": BATCH_SIZE}),
        }
        try:
            resp = requests.put(update_url, json=update_payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            print(f"\n✅ 任務更新成功!")
            print(f"   ID       : {result.get('id')}")
            print(f"   名稱     : {result.get('name')}")
            print(f"   啟用狀態 : {'✔ 啟用' if result.get('enabled') else '✘ 停用'}")
            print(f"   執行間隔 : 每 {result.get('interval', {}).get('every')} 分鐘")
        except Exception as e:
            print(f"\n❌ 任務更新失敗: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"   回應: {e.response.text}")
            sys.exit(1)
    else:
        # 建立新任務
        create_payload = {
            "name": TASK_NAME,
            "task": CELERY_TASK_PATH,
            "interval": {"every": INTERVAL_MINUTES, "period": "minutes"},
            "enabled": True,
            "description": (
                "自動掃描已完成的 AI 分析記錄（IP/Subdomain/URL），"
                "建立 Step 鏈並踢動第一步啟動自主滲透循環。"
            ),
            "kwargs": json.dumps({"batch_size": BATCH_SIZE}),
        }

        try:
            resp = requests.post(SCHEDULER_API, json=create_payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            print(f"\n✅ 定時任務建立成功!")
            print(f"   ID       : {result.get('id')}")
            print(f"   名稱     : {result.get('name')}")
            print(f"   啟用狀態 : {'✔ 啟用' if result.get('enabled') else '✘ 停用'}")
            print(f"   執行間隔 : 每 {result.get('interval', {}).get('every')} 分鐘")
        except Exception as e:
            print(f"\n❌ 任務建立失敗: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"   回應: {e.response.text}")
            sys.exit(1)

    print_section("🎯 完成")
    print("  接下來請確認 Celery Beat 正在運行：")
    print("  celery -A c2_core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler")
    print("")


if __name__ == "__main__":
    main()
