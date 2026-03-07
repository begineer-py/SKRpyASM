from django.db import models
from django.utils import timezone

class AnalyzeData(models.Model):
    """
    用於存儲人工或 AI 協作輸入的分析資訊，與自動生成的 AI 分析不同。
    """
    
    ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="manual_notes")
    subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="manual_notes")
    url_result = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="manual_notes")
    
    # 核心欄位：人工或 AI 輸入的內容
    content = models.TextField(help_text="人工或 AI 輸入的協作分析資訊、備註或特殊發現。")
    
    # 來源標記
    is_from_ai = models.BooleanField(default=False, help_text="此條資訊是否由 AI 產生（例如 AI 助手注入的手工條目）。")
    author = models.CharField(max_length=255, null=True, blank=True, help_text="記錄輸入者名稱（或是 AI Agent 名稱）。")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "協作分析數據"
        verbose_name_plural = "協作分析數據"
        app_label = "core"

    def __str__(self):
        source = self.author or ("AI" if self.is_from_ai else "Unknown")
        return f"Note by {source} at {self.created_at}"