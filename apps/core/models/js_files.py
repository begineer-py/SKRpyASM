from django.db import models
import hashlib


class ExtractedJS(models.Model):
    """從 HTML 內嵌 script 抽取的 JS block。"""

    which_url = models.OneToOneField(
        "core.URLResult", on_delete=models.CASCADE, related_name="extracted_js_blocks"
    )
    content = models.TextField(help_text="抽取到的 JS 原始內容。")
    content_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_analyzed = models.BooleanField(
        default=False,
        help_text="是否已完成針對此 JS block 的分析（抽 endpoint/json 等）。",
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        return f"JS from {self.which_url.url} at {self.created_at}"

    def save(self, *args, **kwargs):
        # 只有當 content 有值時才計算 hash
        # 這樣即使後續 content 被清空，hash 依然會留在資料庫作為指紋
        if self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

        super().save(*args, **kwargs)


class JavaScriptFile(models.Model):
    """JavaScript 資產。

    用來追蹤某個 target 相關的 JS 檔案（外部 src 或收集到的內容）。
    後續可以從 JS 內容抽取 endpoint、參數或 JSON 結構。
    """

    related_pages = models.ManyToManyField(
        "core.URLResult",
        related_name="javascript_files",
        blank=True,
        help_text="哪些頁面引用/載入了此 JS（script src 或相關關聯）。",
    )
    src = models.URLField(
        max_length=2048,
        db_index=True,
        null=True,
        help_text="JS 檔案 URL（script src）。若為 inline/無 src 可為空。",
    )
    content_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[
            ("PENDING", "待下載"),
            ("DOWNLOADED", "已下載"),
            ("ANALYZED", "已分析"),
            ("FAILED", "失敗"),
        ],
        db_index=True,
        help_text="下載/分析流程狀態。",
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="JS 檔案內容（下載成功後保存）。",
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="下載失敗重試次數。",
    )
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text="最後一次失敗原因（exception/message）。",
    )

    is_analyzed = models.BooleanField(
        default=False,
        help_text="是否已完成靜態分析/抽取（endpoint/param/json 等）。",
    )

    class Meta:
        app_label = "core"

    def save(self, *args, **kwargs):
        # 只有當 content 有值時才計算 hash
        # 這樣即使後續 content 被清空，hash 依然會留在資料庫作為指紋
        if self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if self.content and self.status == "PENDING":
            self.status = "DOWNLOADED"

        super().save(*args, **kwargs)
