from django.apps import AppConfig  # 從 Django 的 apps 模組導入 AppConfig 類


class TargetsConfig(
    AppConfig
):  # 定義一個名為 TargetsConfig 的應用程式配置類，繼承自 AppConfig
    default_auto_field = "django.db.models.BigAutoField"  # 設定預設的自動主鍵類型為 BigAutoField，這是一個64位整數
    name = "apps.targets"  # 設定此應用程式的名稱為 'targets'
