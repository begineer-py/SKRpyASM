from django.apps import AppConfig  # 從 Django 的 apps 模組導入 AppConfig 類


class NmapScannerConfig(
    AppConfig
):  # 定義一個名為 NmapScannerConfig 的應用程式配置類，繼承自 AppConfig
    default_auto_field = "django.db.models.BigAutoField"  # 設定此應用程式中模型預設的主鍵欄位類型為 BigAutoField
    name = "apps.nmap_scanner"  # 指定此應用程式的名稱為 "nmap_scanner"
