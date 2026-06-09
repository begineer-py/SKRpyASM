from django.db import models


class ContentBlob(models.Model):
    """
    長期記憶儲存表 (Long-term Memory Store)
    ────────────────────────────────────────
    儲存過長的工具回傳內容 (e.g. 8 萬字的 Django Stack Trace / HTML 源碼)。
    AI 短期記憶只會拿到 blob_id + ai_summary，不會被全文塞爆。

    存入時自動產生 ai_summary，避免每次都要重新分析一次。
    """
    # 內容來源標籤
    SOURCE_CHOICES = [
        ('curl', 'Shell/Curl Output'),
        ('crawler', 'Flaresolverr Crawler'),
        ('nuclei', 'Nuclei Report'),
        ('other', 'Other'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    source_url = models.URLField(null=True, blank=True, help_text="來源網址")

    # 核心存儲
    raw_content = models.TextField(help_text="完整原始內容")
    content_size = models.IntegerField(default=0, help_text="字元數")
    ai_summary = models.TextField(
        null=True, blank=True,
        help_text="AI 第一次存入時自動產生的大意總結，避免重複分析"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_content_blob'
        ordering = ['-created_at']
        verbose_name = "內容長期記憶"
        verbose_name_plural = "內容長期記憶庫"

    def __str__(self):
        src = self.source_url or self.source_type
        return f"Blob[{self.id}] ({self.content_size} chars) from {src}"
