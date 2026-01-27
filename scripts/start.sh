#!/bin/bash
#專門給服務器用的，開三個獨立視窗 以避免一個個執行命令打錯
#請在Linux環境下使用

echo "操，準備開幹... 目標：Linux 環境，開三個獨立視窗"

# 1. 在一個新的終端機視窗裡，啟動前端開發伺服器
echo "正在新視窗中啟動 Frontend..."
x-terminal-emulator -e "bash -c 'echo \"--- 正在運行 Frontend (npm run dev) ---\"; cd frontend && npm run dev; exec bash'" &

# 2. 再開一個新的終端機視窗，啟動 Celery worker
echo "正在新視窗中啟動 Celery..."
x-terminal-emulator -e "bash -c 'echo \"--- 正在運行 Celery Worker ---\"; celery -A c2_core worker -P eventlet -l info; exec bash'" &

# 3. 在目前的終端機視窗裡，直接啟動 Django
#    這樣省得再開一個，而且這個主視窗也得有點事幹
echo "在目前視窗啟動 Django... 看好 Log"
python manage.py runserver 8000

# 當你手動 Ctrl+C 結束 Django 後，腳本會執行到這裡
echo "Django 伺服器已關閉。別忘了手動關掉另外兩個視窗。"#