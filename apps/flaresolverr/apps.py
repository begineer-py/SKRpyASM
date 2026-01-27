from django.apps import AppConfig  # 從 Django 的 apps 模組導入 AppConfig 類


class FlaresolverrConfig(
    AppConfig
):  # 定義一個名為 FlaresolverrConfig 的應用程式配置類，繼承自 AppConfig
    default_auto_field = "django.db.models.BigAutoField"  # 設定預設的自動主鍵欄位類型為 BigAutoField，適用於新的 Django 專案
    name = "apps.flaresolverr"  # 設定應用程式的名稱為 "flaresolverr"
