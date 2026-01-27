# ./core/models/scans_record_modles.py
from django.db import models


class SubfinderScan(models.Model):
    """
    記錄一次子域名枚舉任務。
    """

    STATUS_CHOICES = [
        ("PENDING", "待處理"),
        ("RUNNING", "運行中"),
        ("COMPLETED", "已完成"),
        ("FAILED", "失敗"),
    ]

    which_seed = models.ForeignKey(
        "core.Seed", on_delete=models.CASCADE, related_name="subfinder_scans"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    # 統計數據
    added_count = models.IntegerField(default=0, help_text="新發現數量")

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ["-created_at"]


class NmapScan(models.Model):
    """
    記錄一次端口掃描任務。
    注意：Nmap 通常是針對 IP 掃描的，但歸屬權還是在 Target。
    """

    STATUS_CHOICES = [
        ("PENDING", "待處理"),
        ("RUNNING", "運行中"),
        ("COMPLETED", "已完成"),
        ("FAILED", "失敗"),
    ]

    which_seed = models.ManyToManyField(
        "core.Seed", related_name="nmap_scans", blank=True
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    nmap_args = models.TextField()
    nmap_output = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "core"


class URLScan(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    # === 核心修改：輸入目標 (Input) ===
    # 情境 1: 針對子域名進行被動與主動發現 (例如 gau, katana -u subdomain)
    target_subdomain = models.ForeignKey(
        "core.Subdomain",
        on_delete=models.CASCADE,  # 如果子域名沒了，針對它的掃描記錄也沒意義
        related_name="scans_targeted",
        null=True,
        blank=True,
    )

    # 情境 2: 針對單一 URL 進行深度爬取或驗證 (例如 flaresolverr, 爬蟲遞歸)
    target_url = models.ForeignKey(
        "core.URLResult",
        on_delete=models.CASCADE,  # 如果 URL 沒了，針對它的掃描記錄也沒意義
        related_name="scans_targeted",
        null=True,
        blank=True,
    )

    # === 輔助欄位 ===
    tool = models.CharField(
        max_length=50, default="unknown", help_text="使用的工具 (e.g. gau, katana)"
    )

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    # 統計數據 (可選，方便以後畫圖)
    urls_found_count = models.IntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        app_label = "core"

    def __str__(self):
        if self.target_subdomain:
            return f"[{self.tool}] Scan on Subdomain: {self.target_subdomain.name}"
        elif self.target_url:
            return f"[{self.tool}] Scan on URL: {self.target_url.id}"
        return f"[{self.tool}] Orphan Scan {self.id}"


class NucleiScan(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )
    ip_asset = models.ForeignKey(
        "core.IP",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="nuclei_scans",
    )
    subdomain_asset = models.ForeignKey(
        "core.Subdomain",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="nuclei_scans",
    )
    url_asset = models.ForeignKey(
        "core.URLResult",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="nuclei_scans",
    )
    template_ids = models.JSONField(default=list, blank=True)
    severity_filter = models.CharField(max_length=10, blank=True)
    output_file = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
