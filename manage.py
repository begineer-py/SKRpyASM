import os  # 導入os模組，提供與操作系統交互的功能
import sys  # 導入sys模組，提供訪問系統特定參數和函數的功能

from dotenv import load_dotenv  # 載入 .env 檔（本地 venv 模式用；Docker 模式由 compose environment: 區塊優先）

# 預設不覆蓋既有環境變數，確保 Docker 注入的 environment: 優先於 .env 檔，再優先於 settings.py 預設值
load_dotenv()


def main():  # 定義主函數，用於執行管理任務
    """Run administrative tasks."""  # 函數的文檔字符串，說明函數的功能
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "c2_core.settings"
    )  # 設置DJANGO_SETTINGS_MODULE環境變量，指定Django項目的設置文件
    try:  # 開始一個try-except塊，用於處理可能的導入錯誤
        from django.core.management import (
            execute_from_command_line,
        )  # 從Django導入execute_from_command_line函數
    except ImportError as exc:  # 捕獲ImportError異常，如果Django沒有正確安裝或配置
        raise ImportError(  # 重新拋出一個更詳細的ImportError
            "Couldn't import Django. Are you sure it's installed and "  # 錯誤消息第一部分
            "available on your PYTHONPATH environment variable? Did you "  # 錯誤消息第二部分
            "forget to activate a virtual environment?"  # 錯誤消息第三部分
        ) from exc  # 指明這個錯誤是從原始異常鏈接而來
    execute_from_command_line(sys.argv)  # 執行Django的管理命令，傳入命令行參數


if __name__ == "__main__":  # 判斷當前腳本是否作為主程序運行
    main()  # 調用main函數執行管理任務
