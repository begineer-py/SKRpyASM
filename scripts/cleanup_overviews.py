import os
import sys
import django

# 將專案根目錄加入 PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")
django.setup()

from apps.core.models import Target, Overview

def cleanup():
    targets = Target.objects.all()
    total_deleted = 0
    total_marked_completed = 0

    for target in targets:
        overviews = list(Overview.objects.filter(target=target).order_by('-id'))
        if len(overviews) <= 1:
            continue
        
        print(f"Target: {target.name} (ID: {target.id}) 共有 {len(overviews)} 個 Overviews")
        
        # 找出要保留為主要 active 的 Overview
        # 條件：擁有最多步驟的，若步驟數一樣則取最新的
        best_ov = None
        max_steps = -1
        for ov in overviews:
            step_count = ov.steps.count()
            if step_count > max_steps:
                max_steps = step_count
                best_ov = ov
                
        for ov in overviews:
            if ov == best_ov:
                print(f"  ✅ 保留 Overview ID {ov.id} (狀態: {ov.status}, 步驟數: {ov.steps.count()}) 作為主要紀錄")
                continue
                
            step_count = ov.steps.count()
            if step_count == 0:
                print(f"  🗑️ 刪除空的 Overview ID {ov.id} (狀態: {ov.status})")
                ov.delete()
                total_deleted += 1
            else:
                if ov.status in ['PLANNING', 'EXECUTING']:
                    print(f"  ⏸️ 將舊有且包含步驟的 Overview ID {ov.id} 狀態設為 COMPLETED (避免干擾, 步驟數: {step_count})")
                    ov.status = 'COMPLETED'
                    ov.save(update_fields=['status'])
                    total_marked_completed += 1
                else:
                    print(f"  ℹ️ 保留已結束的 Overview ID {ov.id} (狀態: {ov.status}, 步驟數: {step_count})")

    print("\n" + "="*40)
    print(f"清理完成！\n總共刪除空的 Overviews: {total_deleted}\n總共將多餘的 Active Overviews 標記為 COMPLETED: {total_marked_completed}")
    print("="*40)

if __name__ == "__main__":
    cleanup()
