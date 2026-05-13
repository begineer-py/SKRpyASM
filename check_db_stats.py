import os
import sys
import django
import argparse

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings')
django.setup()

from django.db.models import Count
from apps.core.models import Overview, Seed, Step
from django_ai_assistant.models import Thread, Message
from apps.auto.assistants.planning_agent import AutomationAgent

def print_header(title):
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

def main(detailed=False):
    print_header("📊 C2 Django AI - 系統運行狀態檢測面板")

    # 1. 概覽狀態 (Overviews)
    print("\n[📍 Overviews 總覽]")
    overview_total = Overview.objects.count()
    print(f"• 總 Overview 數量: {overview_total}")
    for stat in Overview.objects.values('status').annotate(total=Count('id')).order_by('-total'):
        print(f"  - {stat['status']}: {stat['total']} 個")

    # 2. 自動化引擎與 API 工具 (AI Tools)
    print("\n[🛠️ AI 自動化可用工具]")
    try:
        agent = AutomationAgent()
        tools = agent.get_tools()
        print(f"• AutomationAgent 總計掛載了: {len(tools)} 把武器 (Tools)")
        
        tool_names = [t.name for t in tools]
        if detailed:
            print(f"  - 所有工具: {', '.join(tool_names)}")
        else:
            if len(tool_names) > 5:
                display_names = tool_names[:3] + ["..."] + tool_names[-2:]
            else:
                display_names = tool_names
            print(f"  - 特徵預覽: {', '.join(display_names)}")
    except Exception as e:
        print(f"• 無法獲取工具列表: {e}")

    # 3. 種子執行狀態 (Seeds)
    print("\n[🌱 Seeds (打點種子) 狀態]")
    seed_total = Seed.objects.count()
    print(f"• 總 Seed 數量: {seed_total}")
    try:
        for stat in Seed.objects.values('type').annotate(total=Count('id')):
            print(f"  - 類型 {stat['type']}: {stat['total']} 個")
    except Exception as e:
        pass

    # 4. AI 對話數目 (Threads / Messages)
    print("\n[💬 AI 對話與思維 (Threads & Messages)]")
    thread_total = Thread.objects.count()
    message_total = Message.objects.count()
    print(f"• 總 Threads 數量: {thread_total}")
    print(f"• 總 Messages 數量: {message_total}")
    
    try:
        for stat in Thread.objects.values('assistant_id').annotate(total=Count('id')).order_by('-total'):
            print(f"  - Agent [{stat['assistant_id']}]: {stat['total']} 個 Thread")
    except Exception:
        pass

    # 若為詳細模式，印出每個 Thread 內部的 Messages
    if detailed:
        print("\n  [🔍 Thread Messages 詳細展開]")
        threads = Thread.objects.all().order_by('-updated_at')[:2]  # 取最近的 10 個避免洗頻
        print(f"  (僅列出最近的 {len(threads)} 個對話串)")
        for t in threads:
            print(f"\n  ▶ Thread ID: {t.id} | Assistant: {t.assistant_id} | Created: {t.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            msgs = t.messages.all().order_by('created_at')
            for m in msgs:
                msg_data = m.message if isinstance(m.message, dict) else {}
                role = msg_data.get('type', 'unknown').upper()
                data = msg_data.get('data', {})
                content = str(data.get('content', ''))
                
                # Check for tool invocations
                tool_calls = data.get('tool_calls', [])
                if tool_calls:
                    tool_desc = ", ".join([f"{tc.get('name')}({tc.get('args')})" for tc in tool_calls])
                    content += f" [🛠️ CALLS TOOL: {tool_desc}]"
                
                # Check for tool message name
                if role == 'TOOL':
                    tool_name = data.get('name', 'unknown_tool')
                    content = f"[🔧 RESULT from {tool_name}] " + content
                
                content_preview = content.replace('\n', ' ')[:20000]
                if len(content) > 200:
                    content_preview += "..."
                print(f"    - [{role}]: {content_preview}")

    # 5. 具體執行步驟 (Steps)
    print("\n[👣 具體攻擊步驟 (Steps)]")
    step_total = Step.objects.count()
    print(f"• 總 Steps 數量: {step_total}")
    try:
        status_counts = Step.objects.values('status').annotate(total=Count('id')).order_by('-total')
        if status_counts:
            for stat in status_counts:
                print(f"  - {stat['status']}: {stat['total']} 個")
        else:
            print("  - 目前沒有任何攻擊步驟。")
    except Exception:
        pass

    # 6. StepNotes
    print("\n[📝 最近 StepNotes (攻擊筆記)]")
    try:
        from apps.core.models.analyze.Step import StepNote
        notes = StepNote.objects.select_related('step', 'step__overview__target').order_by('-id')[:20]
        if not notes:
            print("  - 尚無 StepNote。")
        for n in notes:
            target_name = "?"
            try:
                target_name = n.step.overview.target.name
            except Exception:
                pass
            content_preview = (n.content or "").replace('\n', ' ')[:120]
            if len(n.content or '') > 120:
                content_preview += "..."
            print(f"  Step#{n.step_id} [{n.step.status}] [{target_name}]: {content_preview}")
    except Exception as e:
        print(f"  - 無法獲取 StepNote: {e}")
    print("\n" + "="*50)
    print("  檢測完成！")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C2 Django AI DB Statistics")
    parser.add_argument("-d", "--detailed", action="store_true", help="Print detailed message history for threads.")
    args = parser.parse_args()
    
    main(detailed=args.detailed)
