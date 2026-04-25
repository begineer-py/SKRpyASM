# c2_core/apps.py

from django.apps import AppConfig
import sys

import os
from c2_core.config.config import Dedug_config


class C2CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "c2_core"

    def ready(self):
        print("🚀 C2-CORE 應用準備就緒...")

        # --- 初始化日誌系統 ---
        print("  [*] 日誌系統初始化中...")
        from .config.logging import LogConfig

        LogConfig.setup_enhanced_logging()
        print("  [✅] 日誌系統初始化完成。")


