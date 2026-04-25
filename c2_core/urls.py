# This code snippet is a URL configuration for a Django project called c2_core. It sets up the routing
# for different API endpoints using the Ninja framework.
"""
URL configuration for c2_core project.
"""

from django.contrib import admin  # 導入 Django 管理後台模組
from django.urls import include, path  # 導入 Django 用於 URL 路由的 path 函數
from ninja import NinjaAPI  # 導入 NinjaAPI 類，用於創建 API 實例

# 從你的 app 裡導入 router
from apps.targets.api import (
    router as targets_router,
)  # 從 targets 應用導入 API 路由器，並重命名為 targets_router
from apps.scanners.nmap_scanner.api import (
    router as nmap_router,
)  # 從 nmap_scanner 應用導入 API 路由器，並重命名為 nmap_router
from apps.flaresolverr.api import (
    router as flaresolverr_router,
)  # 從 flaresolverr 應用導入 API 路由器，並重命名為 flaresolverr_router
from apps.core.api import (
    router as core_router,
)  # 從 core 應用導入 API 路由器，並重命名為 core_router

# Unified Scanners Router
from apps.scanners.api import router as scanners_router

# 從 result_assets 應用導入 API 路由器，並重命名為 result_assets_router
from apps.scheduler.api import router as scheduler_router
from apps.analyze_ai.api import router as analyze_ai_router
from apps.http_sender.api import router as http_sender_router
from apps.api_keys.api import router as api_keys_router
from apps.auto.api import router as auto_router

# 建立 NinjaAPI 實例
api = NinjaAPI(
    title="C2 Django AI 核心 API 系統",
    version="1.1.0",
    description="整合 AI 分析與自動化滲透測試流程的 C2 平台核心 API 層。",
)

# 路由註冊
api.add_router("/targets", targets_router, tags=["Targets - 目標管理"])
api.add_router("/scanners", scanners_router)
api.add_router("/flaresolverr", flaresolverr_router, tags=["Tools - FlareSolverr 繞過"])
api.add_router("/core", core_router, tags=["Core - 系統核心層"])
api.add_router("/analyze_ai", analyze_ai_router, tags=["AI Analysis - 指揮中心"])
api.add_router("/scheduler", scheduler_router, tags=["Scheduler - 任務調度"])
api.add_router("/http_sender", http_sender_router, tags=["Tools - HTTP 發送器"])
api.add_router("/api_keys", api_keys_router, tags=["API Keys - 密鑰管理"])
api.add_router("/auto", auto_router, tags=["Legacy Auto - 舊版自動化"])
urlpatterns = [  # 定義 URL 模式列表
    path("admin/", admin.site.urls),  # 將 /admin/ 路徑映射到 Django 管理後台的 URL
    # django_ai_assistant 原生接口
    path("api/assistant/", include("django_ai_assistant.urls")),
    # 操！把所有 API 的總入口都設在 /api/
    # 這樣最乾淨，以後要加新功能也好管理
    path("api/", api.urls),  # 將 /api/ 路徑映射到 NinjaAPI 實例 api 的所有路由
]
