from django.db import models

class APIKey(models.Model):
    """
    API 金鑰模型，用於存放外部服務的認證資訊 (如 OpenAI, Hunter.io 等)。
    """
    service_name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="服務名稱 (例如: 'OPENAI', 'HUNTER')"
    )
    key_value = models.CharField(
        max_length=512, 
        help_text="API 金鑰的實際值"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="是否啟用此金鑰"
    )
    description = models.TextField(
        null=True, 
        blank=True, 
        help_text="服務描述或備註"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "API 金鑰"
        verbose_name_plural = "API 金鑰"

    def __str__(self):
        return f"{self.service_name} ({'Active' if self.is_active else 'Inactive'})"
