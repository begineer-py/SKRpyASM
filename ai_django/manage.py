import os
import sys
from django.core.management import (
    execute_from_command_line,
)  # 從Django導入execute_from_command_line函數
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setting")
execute_from_command_line(sys.argv)  # 執行Django的管理命令，傳入命令行參數