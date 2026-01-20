# core/models/assets.py

from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords


class Target(models.Model):
    name = models.CharField(
        max_length=255, unique=True, help_text="專案名稱，如 'Google'"
    )
    description = models.TextField(null=True, blank=True, help_text="專案描述與備註")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.name


class SubdomainSeed(models.Model):
    subdomain = models.ForeignKey(
        "Subdomain", on_delete=models.CASCADE, related_name="seed_links"
    )
    seed = models.ForeignKey("Seed", on_delete=models.CASCADE, related_name="sub_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("subdomain", "seed")


class Seed(models.Model):
    SEED_TYPE_CHOICES = [
        ("DOMAIN", "Root Domain (e.g., google.com)"),
        ("IP_RANGE", "IP/CIDR (e.g., 192.168.1.0/24)"),
        ("URL", "Specific URL (e.g., https://api.site.com)"),
    ]
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="seeds")
    value = models.CharField(max_length=512, help_text="種子內容，如 google.com")
    type = models.CharField(max_length=20, choices=SEED_TYPE_CHOICES, default="DOMAIN")
    is_active = models.BooleanField(default=True, help_text="是否啟用此種子進行掃描")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("target", "value")

    def __str__(self):
        return f"[{self.type}] {self.value}"


class IP(models.Model):
    which_seed = models.ManyToManyField(Seed, related_name="ips")
    ipv4 = models.GenericIPAddressField(
        protocol="ipv4", null=True, blank=True, db_index=True
    )
    ipv6 = models.GenericIPAddressField(protocol="ipv6", null=True, blank=True)

    # === 新增：簡單的來源記錄欄位 ===
    last_scan_type = models.CharField(
        max_length=50, null=True, blank=True, help_text="掃描類型 (e.g. NmapScan)"
    )
    last_scan_id = models.IntegerField(null=True, blank=True, help_text="掃描 ID")

    # === 歷史記錄：零配置，開箱即用 ===
    history = HistoricalRecords()
    discovered_by_scans = models.ManyToManyField(
        "core.NmapScan", blank=True, related_name="ips_discovered"
    )

    def __str__(self):
        return f"{self.ipv4 or self.ipv6 or 'Unknown IP'}"


class Port(models.Model):
    ip = models.ForeignKey(IP, on_delete=models.CASCADE, related_name="ports")
    # 注意：這個 discovered_by_scans 多對多關係可以保留，作為輔助查詢，但歷史追蹤主要靠 last_scan_*
    discovered_by_scans = models.ManyToManyField(
        "core.NmapScan", blank=True, related_name="ports_updated"
    )
    port_number = models.IntegerField(db_index=True)
    protocol = models.CharField(max_length=10)
    state = models.CharField(max_length=20, db_index=True)
    service_name = models.CharField(max_length=100, blank=True, null=True)
    service_version = models.CharField(max_length=255, blank=True, null=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    # === 新增：簡單的來源記錄欄位 ===
    last_scan_type = models.CharField(max_length=50, null=True, blank=True)
    last_scan_id = models.IntegerField(null=True, blank=True)

    # === 歷史記錄 ===
    history = HistoricalRecords()

    class Meta:
        unique_together = ("ip", "port_number", "protocol")
        indexes = [models.Index(fields=["ip", "port_number"])]

    def __str__(self):
        return (
            f"Port {self.port_number}/{self.protocol} on {self.ip.ipv4 or self.ip.ipv6}"
        )


class Subdomain(models.Model):
    which_seed = models.ManyToManyField(
        "core.Seed", related_name="subdomains", through="SubdomainSeed"
    )
    discovered_by_scans = models.ManyToManyField(
        "core.SubfinderScan", blank=True, related_name="updated_subdomains"
    )
    sources_text = models.TextField(
        blank=True, help_text="Comma-separated list of sources"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    ips = models.ManyToManyField(IP, related_name="subdomains", blank=True)
    name = models.CharField(max_length=255, db_index=True)
    dns_records = models.JSONField(null=True, blank=True)
    cname = models.TextField(blank=True, null=True)
    is_resolvable = models.BooleanField(default=True)
    is_cdn = models.BooleanField(default=False)
    is_waf = models.BooleanField(default=False)
    waf_name = models.TextField(null=True)
    cdn_name = models.TextField(null=True)

    # === 新增：簡單的來源記錄欄位 ===
    last_scan_type = models.CharField(max_length=50, null=True, blank=True)
    last_scan_id = models.IntegerField(null=True, blank=True)

    # === 歷史記錄 ===
    # m2m_fields=[ips] 是新版功能，如果你是 3.11.0 且不報錯可以用；報錯就刪掉這行
    history = HistoricalRecords(m2m_fields=[ips])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.name


class URLResult(models.Model):
    # === 變更：刪除 which_subdomain，改為 related_subdomains (M2M) ===
    related_subdomains = models.ManyToManyField(
        "core.Subdomain", related_name="related_urls", blank=True
    )

    # === 其他欄位保持不變 ===
    content_fetch_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "PENDING"),
            ("SUCCESS_FETCHED", "SUCCESS_FETCHED"),
            ("FAILED_NO_CONTENT", "FAILED_NO_CONTENT"),
            ("FAILED_NETWORK_ERROR", "FAILED_NETWORK_ERROR"),
            ("FAILED_BLOCKED", "FAILED_BLOCKED"),
        ],
        default="PENDING",
        db_index=True,
    )
    discovered_by_scans = models.ManyToManyField("core.URLScan", related_name="results")
    url = models.URLField(max_length=2048, db_index=True, unique=True)
    status_code = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=512, null=True, blank=True)
    content_length = models.PositiveIntegerField(null=True, blank=True)
    headers = models.JSONField(null=True, blank=True)
    raw_response = models.TextField(null=True, blank=True)
    is_important = models.BooleanField(default=False, db_index=True)
    used_flaresolverr = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    final_url = models.URLField(max_length=2048, db_index=True, null=True, blank=True)
    is_external_redirect = models.BooleanField(default=False, db_index=True)

    # 來源記錄
    last_scan_type = models.CharField(max_length=50, null=True, blank=True)
    last_scan_id = models.IntegerField(null=True, blank=True)
    raw_response_hash = models.CharField(
        max_length=64, null=True, blank=True, db_index=True
    )
    # 歷史記錄
    history = HistoricalRecords()

    def __str__(self):
        return f"[{self.status_code}] {self.url}"


# ... (Form, JavaScriptFile 等其他子模型保持不變，無需歷史記錄) ...
class Form(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="forms"
    )
    action = models.CharField(max_length=2048)
    method = models.CharField(max_length=10)
    parameters = models.JSONField(default=dict)

    class Meta:
        unique_together = ("which_url", "action", "method")

    def __str__(self):
        return f"Form on {self.which_url.url} to {self.action}"


class JavaScriptFile(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="js_files"
    )
    src = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.src or "Inline JS"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(src__isnull=False) | Q(content__isnull=False),
                name="js_src_or_content_not_null",
            ),
            models.UniqueConstraint(
                fields=["which_url", "src"],
                condition=Q(src__isnull=False),
                name="unique_js_src_per_url",
            ),
        ]


class Endpoint(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="endpoints"
    )
    path = models.CharField(max_length=2048)
    source = models.CharField(max_length=50)

    class Meta:
        unique_together = ("which_url", "path")

    def __str__(self):
        return self.path


class AnalysisFinding(models.Model):
    which_url_result = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="findings"
    )
    pattern_name = models.CharField(max_length=100, db_index=True)
    line_number = models.PositiveIntegerField()
    match_content = models.TextField()
    match_start = models.PositiveIntegerField(null=True, blank=True)
    match_end = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("which_url_result", "pattern_name", "line_number")

    def __str__(self):
        return f"{self.pattern_name} at line {self.line_number}"


class Link(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="links"
    )
    href = models.TextField()
    text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.href


class MetaTag(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="meta_tags"
    )
    attributes = models.JSONField()

    def __str__(self):
        return str(self.attributes)


class Iframe(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="iframes"
    )
    src = models.TextField()

    class Meta:
        unique_together = ("which_url", "src")

    def __str__(self):
        return self.src


class Comment(models.Model):
    which_url = models.ForeignKey(
        URLResult, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()

    def __str__(self):
        return self.content[:50]


# core/models/assets.py


class TechStack(models.Model):
    """
    技術棧明細表：記錄 Nginx, PHP, Ubuntu 等具體技術
    """

    # 關聯到 URLResult (當前層級)
    which_url_result = models.ForeignKey(
        "URLResult",
        on_delete=models.CASCADE,
        related_name="technologies",
        null=True,
        blank=True,
    )
    # 也可以關聯到 Subdomain，方便全局查詢
    subdomain = models.ForeignKey(
        "Subdomain",
        on_delete=models.CASCADE,
        related_name="technologies",
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=100, db_index=True, help_text="技術名稱，如 PHP, Nginx"
    )
    version = models.CharField(
        max_length=100, null=True, blank=True, help_text="版本號"
    )
    categories = models.JSONField(
        default=list, help_text="分類，如 ['Web servers', 'Reverse proxies']"
    )

    # 擴展信息
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        unique_together = ("which_url_result", "name", "version")  # 防止重複記錄

    def __str__(self):
        return f"{self.name} {self.version or ''}"
