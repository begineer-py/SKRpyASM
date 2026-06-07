# apps/core/models/scans_record_models.py
from django.db import models


class ScanRecord(models.Model):
    """
    抽象基底 Model：所有掃描記錄共用的生命週期欄位。
    繼承此類的 Model 自動獲得：
      - STATUS_CHOICES (PENDING/RUNNING/COMPLETED/FAILED)
      - status, started_at, completed_at, error_message, created_at
    子類別可覆寫 STATUS_CHOICES 或 status 欄位以自訂標籤/索引。
    """

    STATUS_CHOICES = [
        ("PENDING", "待處理"),
        ("RUNNING", "運行中"),
        ("COMPLETED", "已完成"),
        ("FAILED", "失敗"),
    ]

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "core"


class AmassScan(ScanRecord):
    which_seed = models.ForeignKey(
        "core.Seed", on_delete=models.CASCADE, related_name="amass_scans"
    )
    which_target = models.ForeignKey(
        "core.target", on_delete=models.CASCADE, related_name="amass_scans"
    )
    added_count = models.IntegerField(default=0, help_text="新發現數量")

    class Meta:
        app_label = "core"
        ordering = ["-created_at"]


class SubfinderScan(ScanRecord):
    """記錄一次子域名枚舉任務。"""

    which_seed = models.ForeignKey(
        "core.Seed", on_delete=models.CASCADE, related_name="subfinder_scans"
    )
    added_count = models.IntegerField(default=0, help_text="新發現數量")

    class Meta:
        app_label = "core"
        ordering = ["-created_at"]


class NmapScan(ScanRecord):
    """記錄一次端口掃描任務。"""

    which_seed = models.ManyToManyField(
        "core.Seed", related_name="nmap_scans", blank=True
    )
    nmap_args = models.TextField()
    nmap_output = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "core"


class URLScan(ScanRecord):
    # URLScan 使用英文標籤，語義上 COMPLETED/FAILED 有特殊含義，故覆寫
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),  # 即使內容抓取失敗，但程式執行完畢，也算 COMPLETED
        ("FAILED", "System Failed"),  # 僅用於程式崩潰或不可控異常
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

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
    tool = models.CharField(max_length=50, default="unknown", db_index=True)
    urls_found_count = models.IntegerField(default=0)

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


class NucleiScan(ScanRecord):
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

    class Meta:
        app_label = "core"


class SubBrute(ScanRecord):
    """記錄一次子域名暴力枚舉任務。"""

    which_sub = models.ForeignKey(
        "core.Subdomain", on_delete=models.CASCADE, related_name="SubBrute"
    )
    added_count = models.IntegerField(default=0, help_text="新發現數量")

    class Meta:
        app_label = "core"
        ordering = ["-created_at"]
