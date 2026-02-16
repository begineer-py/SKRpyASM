# core/models/assets.py

from email.policy import default
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


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
    # === 新增：直接綁定 Target，確保級聯刪除 ===
    target = models.ForeignKey(
        Target,
        on_delete=models.CASCADE,
        related_name="ips",
        null=True,
        blank=True,
        db_index=True,
    )
    which_seed = models.ManyToManyField(Seed, related_name="ips")
    ipv4 = models.GenericIPAddressField(
        protocol="ipv4", null=True, blank=True, db_index=True
    )
    ipv6 = models.GenericIPAddressField(protocol="ipv6", null=True, blank=True)

    # 來源記錄
    last_scan_type = models.CharField(
        max_length=50, null=True, blank=True, help_text="掃描類型 (e.g. NmapScan)"
    )
    last_scan_id = models.IntegerField(null=True, blank=True, help_text="掃描 ID")

    # 歷史記錄
    history = HistoricalRecords()
    discovered_by_scans = models.ManyToManyField(
        "core.NmapScan", blank=True, related_name="ips_discovered"
    )

    def __str__(self):
        return f"{self.ipv4 or self.ipv6 or 'Unknown IP'}"


class Port(models.Model):
    ip = models.ForeignKey(IP, on_delete=models.CASCADE, related_name="ports")
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

    last_scan_type = models.CharField(max_length=50, null=True, blank=True)
    last_scan_id = models.IntegerField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = ("ip", "port_number", "protocol")
        indexes = [models.Index(fields=["ip", "port_number"])]

    def __str__(self):
        return (
            f"Port {self.port_number}/{self.protocol} on {self.ip.ipv4 or self.ip.ipv6}"
        )


class Subdomain(models.Model):
    # === 新增：直接綁定 Target ===
    target = models.ForeignKey(
        Target,
        on_delete=models.CASCADE,
        related_name="subdomains",
        null=True,
        blank=True,
        db_index=True,
    )
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

    last_scan_type = models.CharField(max_length=50, null=True, blank=True)
    last_scan_id = models.IntegerField(null=True, blank=True)

    # 歷史記錄
    history = HistoricalRecords(m2m_fields=[ips])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.name


# ==========================================
# 自動化信號區 (Automation Signals)
# ==========================================


# 1. Subdomain -> Seed: 自動繼承 Target
@receiver(m2m_changed, sender=Subdomain.which_seed.through)
def sync_subdomain_target(sender, instance, action, **kwargs):
    if action == "post_add":
        if not instance.target_id:
            first_seed = instance.which_seed.first()
            if first_seed:
                # 使用 update 防止觸發 save() 循環
                Subdomain.objects.filter(pk=instance.pk).update(
                    target=first_seed.target
                )


# 2. IP -> Seed: 自動繼承 Target
@receiver(m2m_changed, sender=IP.which_seed.through)
def sync_ip_target(sender, instance, action, **kwargs):
    if action == "post_add":
        if not instance.target_id:
            first_seed = instance.which_seed.first()
            if first_seed:
                IP.objects.filter(pk=instance.pk).update(target=first_seed.target)
