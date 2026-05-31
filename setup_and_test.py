import os
import django
import sys
import time

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")
django.setup()

from apps.core.models import Target, Seed, Overview, Subdomain, IP, Step
from apps.core.models.url_assets import URLResult
from apps.core.models.analyze.Step import StepNote
from apps.core.models.ai_models import Thread, Message
from apps.ai_assistant.helpers.use_cases import create_thread
from apps.auto.tasks import preprocess_data, auto_execute_plan
from django.contrib.auth import get_user_model

def cleanup_all():
    print("=== CLEANING UP ALL DATA ===")
    
    # 1. 清理對話與消息 (Threads and Messages)
    print(f"Deleting {Message.objects.count()} Messages...")
    Message.objects.all().delete()
    print(f"Deleting {Thread.objects.count()} Threads...")
    Thread.objects.all().delete()
    
    # 2. 清理概覽與步驟 (Overviews and Steps)
    print(f"Deleting {StepNote.objects.count()} StepNotes...")
    StepNote.objects.all().delete()
    print(f"Deleting {Step.objects.count()} Steps...")
    Step.objects.all().delete()
    print(f"Deleting {Overview.objects.count()} Overviews...")
    Overview.objects.all().delete()
    
    # 3. 清理資產 (Assets: URLResults, Subdomains, IPs, Seeds)
    print(f"Deleting {URLResult.objects.count()} URLResults...")
    URLResult.objects.all().delete()
    print(f"Deleting {Subdomain.objects.count()} Subdomains...")
    Subdomain.objects.all().delete()
    print(f"Deleting {IP.objects.count()} IPs...")
    IP.objects.all().delete()
    print(f"Deleting {Seed.objects.count()} Seeds...")
    Seed.objects.all().delete()
    
    # 4. 清理 Target
    print(f"Deleting {Target.objects.count()} Targets...")
    Target.objects.all().delete()
    print("=== CLEANUP COMPLETED ===\n")

def run_setup_and_test():
    # 執行清理
    cleanup_all()
    
    print("=== SETTING UP TEST DATA ===")
    target_url = "https://vuln-f9wi.onrender.com/"
    target_name = "Vuln-Lab"
    
    # 建立 Target
    target, created = Target.objects.get_or_create(
        name=target_name, 
        defaults={"description": f"Automated Pentest for {target_url}"}
    )
    
    # 建立 URL 種子
    seed, _ = Seed.objects.get_or_create(
        target=target, 
        type="URL", 
        value=target_url
    )
    print(f"Created Target: {target.name} (ID: {target.id})")
    print(f"Created Seed: {seed.value} (Type: {seed.type})")

    # 1. 執行初步分析 (建立 Overview)
    # preprocess_data 會掃描所有 Target 並為其建立 Overview
    print("\n1. Running preprocess_data (Initial Analysis)...")
    preprocess_data()
    
    overview = Overview.objects.filter(target=target).first()
    if not overview:
        print("FAILED: Overview not created by preprocess_data.")
        return
    print(f"   - Overview created (ID: {overview.id}, Status: {overview.status})")

    # 2. 啟動任務 (將狀態改為 EXECUTING 並綁定 Thread)
    print("\n2. Activating task (PLANNING -> EXECUTING)...")
    overview.status = "EXECUTING"
    
    # 確保有 superuser 用於建立 Thread
    User = get_user_model()
    system_user = User.objects.filter(is_superuser=True).first()
    if not system_user:
        system_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("   - Created new superuser 'admin'")

    # 建立 Thread 並綁定
    thread = create_thread(
        name=f"Pentest-{target_name}",
        assistant_id="automation_agent",
        user=system_user
    )
    overview.thread = thread
    overview.save(update_fields=['status', 'thread'])
    print(f"   - Status updated to EXECUTING. Thread bound: {thread.id}")

    # 3. 執行自動化滲透任務
    print("\n3. Running auto_execute_plan (Automation Layer)...")
    try:
        # auto_execute_plan 會查找 EXECUTING 的 overview 並執行
        auto_execute_plan()
        print("   - auto_execute_plan completed.")
    except Exception as e:
        print(f"   - auto_execute_plan FAILED: {e}")

    # 4. 驗證結果
    overview.refresh_from_db()
    steps = overview.steps.all()
    print(f"\n=== FINAL TEST RESULTS ===")
    print(f"Target: {target.name}")
    print(f"Overview Status: {overview.status}")
    print(f"Generated Steps: {steps.count()}")
    for s in steps:
        print(f" - Step[{s.id}] {s.operation_type} | Status: {s.status}")

    print("\n=== SETUP AND TEST COMPLETED ===")

if __name__ == "__main__":
    run_setup_and_test()
