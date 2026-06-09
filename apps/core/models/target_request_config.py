from django.db import models


class TargetRequestConfig(models.Model):
    target = models.OneToOneField(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="request_config",
        verbose_name="所屬目標",
    )
    header_enabled = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name="啟用標籤注入",
        help_text="None = 繼承全域設定，True/False = 強制覆蓋",
    )
    header_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default=None,
        verbose_name="使用者名稱",
        help_text="留空 = 繼承全域設定",
    )
    header_prefix = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=None,
        verbose_name="標頭前綴",
        help_text="留空 = 繼承全域設定",
    )
    custom_headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="自訂額外 Headers",
        help_text='JSON 格式，例如 {"X-Custom": "value"}',
    )
    rps = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="每秒請求數 (RPS)",
        help_text="None = 繼承全域設定",
    )
    max_concurrency = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="最大並發數",
        help_text="None = 繼承全域設定",
    )
    timeout = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="請求超時（秒）",
        help_text="None = 繼承全域設定",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "目標請求設定"
        verbose_name_plural = "目標請求設定"

    def __str__(self):
        return f"RequestConfig(Target={self.target_id})"
