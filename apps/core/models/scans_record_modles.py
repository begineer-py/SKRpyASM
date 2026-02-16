# .apps/core/models/scans_record_modles.py
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


# apps/core/models.py


class URLScan(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),  # 即使內容抓取失敗，但程式執行完畢，也算 COMPLETED
        ("FAILED", "System Failed"),  # 僅用於程式崩潰或不可控異常
    ]

    # 輸入目標：子域名或單一 URL
    target_subdomain = models.ForeignKey(
        "core.Subdomain",
        on_delete=models.CASCADE,
        related_name="scans_targeted",
        null=True,
        blank=True,
    )
    target_url = models.ForeignKey(
        "core.URLResult",
        on_delete=models.CASCADE,
        related_name="scans_targeted",
        null=True,
        blank=True,
    )

    tool = models.CharField(
        max_length=50,
        default="unknown",
        db_index=True,
    )

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    urls_found_count = models.IntegerField(default=0)
    error_message = models.TextField(
        null=True, blank=True
    )  # 用於存放 FAILED_DNS_ERROR 等詳細資訊

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        app_label = "core"

    def __str__(self):
        target = (
            self.target_subdomain.name
            if self.target_subdomain
            else f"URL:{self.target_url_id}"
        )
        return f"[{self.tool}] {self.status} on {target}"


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
