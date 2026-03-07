# core/models/domain.py
# Domain-related models for subdomains and their relationships

from django.db import models
from simple_history.models import HistoricalRecords


class SubdomainSeed(models.Model):
    """Through model for Subdomain-Seed many-to-many relationship."""
    
    subdomain = models.ForeignKey(
        "Subdomain", 
        on_delete=models.CASCADE, 
        related_name="seed_links"
    )
    seed = models.ForeignKey(
        "core.Seed", 
        on_delete=models.CASCADE, 
        related_name="sub_links"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("subdomain", "seed")


class Subdomain(models.Model):
    """Subdomain model representing discovered domain names."""
    
    # Direct binding to Target for cascade deletion
    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="subdomains",
        null=True,
        blank=True,
        db_index=True,
    )
    
    # Relationships
    which_seed = models.ManyToManyField(
        "core.Seed", 
        related_name="subdomains", 
        through="SubdomainSeed"
    )
    discovered_by_scans = models.ManyToManyField(
        "core.SubfinderScan", 
        blank=True, 
        related_name="updated_subdomains"
    )
    ips = models.ManyToManyField(
        "network.IP", 
        related_name="subdomains", 
        blank=True
    )
    
    # Basic information
    name = models.CharField(max_length=255, db_index=True)
    sources_text = models.TextField(
        blank=True, 
        help_text="Comma-separated list of sources"
    )
    
    # Status and timing
    is_active = models.BooleanField(default=True, db_index=True)
    is_resolvable = models.BooleanField(default=True)
    is_tech_analyzed = models.BooleanField(default=False)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # DNS information
    dns_records = models.JSONField(null=True, blank=True)
    cname = models.TextField(blank=True, null=True)
    
    # Protection information
    is_cdn = models.BooleanField(default=False)
    is_waf = models.BooleanField(default=False)
    waf_name = models.TextField(null=True)
    cdn_name = models.TextField(null=True)
    
    # Scan tracking
    last_scan_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True
    )
    last_scan_id = models.IntegerField(
        null=True, 
        blank=True
    )

    # Historical records
    history = HistoricalRecords(m2m_fields=[ips])

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.name
