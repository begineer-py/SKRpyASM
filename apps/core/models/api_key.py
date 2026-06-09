import base64
import logging

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = getattr(settings, "API_KEY_ENCRYPTION_KEY", None)
    if not key:
        from django.core.management import call_command
        logger.warning("API_KEY_ENCRYPTION_KEY not set; API keys stored without encryption until key is configured.")
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


class APIKey(models.Model):
    """
    API 金鑰模型，用於存放外部服務的認證資訊 (如 OpenAI, Hunter.io 等)。
    key_value 在資料庫中以 Fernet 加密存儲，讀取時自動解密。
    """

    service_name = models.CharField(
        max_length=100,
        help_text="服務名稱 (例如: 'shodan', 'OPENAI', 'HUNTER' - 可重複以支援多個金鑰輪轉)"
    )
    key_value = models.TextField(
        help_text="加密後的 API 金鑰"
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
        app_label = "core"
        db_table = "api_keys_apikey"
        verbose_name = "API 金鑰"
        verbose_name_plural = "API 金鑰"

    def set_key(self, plaintext: str) -> None:
        f = _get_fernet()
        if f:
            self.key_value = f.encrypt(plaintext.encode()).decode()
        else:
            self.key_value = base64.b64encode(plaintext.encode()).decode()

    def get_key(self) -> str:
        f = _get_fernet()
        try:
            if f:
                return f.decrypt(self.key_value.encode()).decode()
            return base64.b64decode(self.key_value.encode()).decode()
        except Exception:
            return self.key_value

    def save(self, *args, **kwargs):
        if not self.pk and self.key_value and not self.key_value.startswith("gAAA"):
            try:
                base64.b64decode(self.key_value)
            except Exception:
                self.set_key(self.key_value)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service_name} ({'Active' if self.is_active else 'Inactive'})"
