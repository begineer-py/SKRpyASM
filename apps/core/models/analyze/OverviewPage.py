from django.db import models


class OverviewPage(models.Model):
    """
    Overview 分頁情報架構
    ──────────────────────────────────────
    將 Overview 收集到的情報按語義分區儲存，避免單一欄位塞入過大內容。
    每頁可有 page_breakdown（借鏡 ContentBlob）以支援 LLM 分頁讀取。

    設計理由：1:1 後 Overview 是 Target 的唯一情報中樞，
    核心高頻欄位（recon_summary 等）直接存 Overview，
    大篇幅情報（完整掃描報告、原始回應）存 OverviewPage。
    """

    SECTION_CHOICES = [
        ("RECON_SUMMARY", "偵察摘要"),
        ("SUBDOMAIN_INTEL", "子域名情報"),
        ("PORT_SERVICE", "端口服務"),
        ("URL_ENDPOINT", "URL 端點"),
        ("VULNERABILITY", "漏洞"),
        ("ATTACK_VECTOR", "攻擊向量"),
        ("TECH_STACK", "技術棧"),
        ("STRATEGIC_PLAN", "戰略計畫"),
        ("FREEFORM", "自由筆記"),
    ]

    overview = models.ForeignKey(
        "core.Overview",
        on_delete=models.CASCADE,
        related_name="pages",
        help_text="所屬的 Overview（1:1 綁定 Target）",
    )
    section_type = models.CharField(
        max_length=30,
        choices=SECTION_CHOICES,
        db_index=True,
        help_text="情報分區類型",
    )
    title = models.CharField(
        max_length=200,
        help_text="此分區的標題（供 agent 查詢時識別）",
    )
    content = models.TextField(
        help_text="此分區的完整內容",
    )
    page_breakdown = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "結構化分頁（當 content 過大時由 LLM 切分）。"
            "格式: [{title: str, content: str}, ...]"
        ),
    )
    summary = models.TextField(
        blank=True,
        default="",
        help_text="此分區的簡短摘要（agent 快速瀏覽用）",
    )
    source_agent = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="寫入此頁的 agent 識別碼",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_overview_page"
        verbose_name = "Overview 分頁"
        verbose_name_plural = "Overview 分頁"
        ordering = ["section_type", "-updated_at"]
        indexes = [
            models.Index(fields=["overview", "section_type"], name="ovpage_section_idx"),
            models.Index(fields=["updated_at"], name="ovpage_updated_idx"),
        ]

    def __str__(self):
        return f"OverviewPage[{self.id}] {self.section_type} — {self.title[:40]}"
