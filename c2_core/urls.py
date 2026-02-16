# This code snippet is a URL configuration for a Django project called c2_core. It sets up the routing
# for different API endpoints using the Ninja framework.
"""
URL configuration for c2_core project.
"""

from django.contrib import admin  # 導入 Django 管理後台模組
from django.urls import path  # 導入 Django 用於 URL 路由的 path 函數
from ninja import NinjaAPI  # 導入 NinjaAPI 類，用於創建 API 實例

# 從你的 app 裡導入 router
from apps.targets.api import (
    router as targets_router,
)  # 從 targets 應用導入 API 路由器，並重命名為 targets_router
from apps.nmap_scanner.api import (
    router as nmap_router,
)  # 從 nmap_scanner 應用導入 API 路由器，並重命名為 nmap_router
from apps.flaresolverr.api import (
    router as flaresolverr_router,
)  # 從 flaresolverr 應用導入 API 路由器，並重命名為 flaresolverr_router
from apps.core.api import (
    router as core_router,
)  # 從 core 應用導入 API 路由器，並重命名為 core_router

# 從 result_assets 應用導入 API 路由器，並重命名為 result_assets_router
from apps.subfinder.api import router as subdoamain
from apps.get_all_url.api import router as get_all_url_router
from apps.scheduler.api import router as scheduler_router
from apps.analyze_ai.api import router as analyze_ai_router
from apps.nuclei_scanner.api import router as nuclei_scanner_router

# 建立 NinjaAPI 實例
api = NinjaAPI(  # 創建一個 NinjaAPI 實例
    title="C2 Platform API",
    version="1.0.0",
    description="一個幹爆強的 C2 平台 API",  # 設定 API 的標題、版本和描述
)

# 媽的，在 API 裡面，把 targets 的地盤劃在 /targets/
# 這樣才對！
api.add_router(
    "/targets", targets_router
)  # 將 targets 應用的路由添加到 /targets/ 路徑下
api.add_router("/nmap", nmap_router)  # 將 nmap_scanner 應用的路由添加到 /nmap/ 路徑下
api.add_router(
    "/flaresolverr", flaresolverr_router
)  # 將 flaresolverr 應用的路由添加到 /flaresolverr/ 路徑下
api.add_router("/core", core_router)  # 將 core 應用的路由添加到 /core/ 路徑下
api.add_router("/subfinder", subdoamain)
api.add_router("/get_all_url", get_all_url_router)
# 之後有別的 app，就繼續加
# api.add_router("/scanners/", scanners_router)
api.add_router("/analyze_ai", analyze_ai_router)
api.add_router("/scheduler", scheduler_router, tags=["Scheduler"])
api.add_router("/nuclei", nuclei_scanner_router, tags=["Nuclei"])
urlpatterns = [  # 定義 URL 模式列表
    path("admin/", admin.site.urls),  # 將 /admin/ 路徑映射到 Django 管理後台的 URL
    # 操！把所有 API 的總入口都設在 /api/
    # 這樣最乾淨，以後要加新功能也好管理
    path("api/", api.urls),  # 將 /api/ 路徑映射到 NinjaAPI 實例 api 的所有路由
]
