#!/usr/bin/env python3
"""
scripts/setup_ai_bootstrapper.py

註冊新的「AI 初始引導」定時任務，並刪除舊的 regex 基礎引導任務。
"""

import os
import sys
import json
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
SCHEDULER_API = f"{BASE_URL}/api/scheduler/tasks"

NEW_TASK_NAME = "High-Value AI Bootstrapper"
NEW_TASK_PATH = "analyze_ai.tasks.periodic_initial_analysis_bootstrapper"
OLD_TASK_NAME = "High-Value Recon Bootstrapper" # 假設這是原本的名稱

def main():
    print(f"🚀 開始更新 AI 引導任務...")
    
    # 1. 獲取所有任務
    try:
        resp = requests.get(SCHEDULER_API, timeout=10)
        resp.raise_for_status()
        tasks = resp.json()
    except Exception as e:
        print(f"❌ 無法連接到 Scheduler API: {e}")
        sys.exit(1)

    # 2. 查找並刪除舊任務 (如果存在)
    # 我們不確定舊任務的精確名稱，所以我們也按任務路徑查找
    old_task_path = "scheduler.tasks.trigger_high_value_bootstrap"
    for t in tasks:
        if t["task"] == old_task_path or t["name"] == OLD_TASK_NAME or "High-Value" in t["name"]:
            if t["name"] == NEW_TASK_NAME: continue # 不要刪除我們正要建立的
            
            print(f"🗑️  發現舊任務: {t['name']} (ID: {t['id']})，正在刪除...")
            try:
                del_resp = requests.delete(f"{SCHEDULER_API}/{t['id']}", timeout=10)
                if del_resp.status_code == 204:
                    print(f"✅ 舊任務已刪除。")
            except Exception as e:
                print(f"⚠️  刪除舊任務失敗: {e}")

    # 3. 建立或更新新任務
    payload = {
        "name": NEW_TASK_NAME,
        "task": NEW_TASK_PATH,
        "interval": {"every": 5, "period": "minutes"},
        "enabled": True,
        "description": "AI 驅動的高價值資產發現與初步分析引導。取代舊的 regex 邏輯。",
        "kwargs": json.dumps({}),
    }

    print(f"🆕 正在建立/更新任務: {NEW_TASK_NAME}...")
    try:
        resp = requests.post(SCHEDULER_API, json=payload, timeout=10)
        if resp.status_code == 200 or resp.status_code == 201:
            print(f"✅ 任務註冊成功！")
            print(json.dumps(resp.json(), indent=2))
        elif resp.status_code == 409:
            # 如果已存在，則嘗試更新 (雖然 post 其實已經處理了 update_or_create，但 API 可能有不同行為)
            print(f"ℹ️  任務已存在，嘗試通過 PUT 更新...")
            # 這裡我們需要知道 ID，所以重新獲取
            tasks = requests.get(SCHEDULER_API).json()
            existing = next(t for t in tasks if t["name"] == NEW_TASK_NAME)
            resp = requests.put(f"{SCHEDULER_API}/{existing['id']}", json=payload, timeout=10)
            resp.raise_for_status()
            print(f"✅ 任務更新成功！")
        else:
            print(f"❌ 任務建立失敗 (Code: {resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"❌ 建立任務時出錯: {e}")

if __name__ == "__main__":
    main()
