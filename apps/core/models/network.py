# core/models/network.py
# Network-related models for IP addresses and ports

from django.db import models
from simple_history.models import HistoricalRecords


class IP(models.Model):
    """IP address model representing network endpoints."""
    
    # Direct binding to Target for cascade deletion
    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="ips",
        null=True,
        blank=True,
        db_index=True,
    )
    which_seed = models.ManyToManyField(
        "core.Seed", 
        related_name="ips"
    )
    # Unified address field supporting both IPv4 and IPv6
    address = models.GenericIPAddressField(
        protocol="both",
        null=True,
        blank=True,
        db_index=True,
        help_text="IP 位址 (IPv4 或是 IPv6)"
    )
    version = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=[(4, "IPv4"), (6, "IPv6")],
        help_text="IP 版本"
    )

    # Source tracking
    last_scan_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="掃描類型 (e.g. NmapScan)"
    )
    last_scan_id = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="掃描 ID"
    )

    # Historical records and scan relationships
    history = HistoricalRecords()
    discovered_by_scans = models.ManyToManyField(
        "core.NmapScan", 
        blank=True, 
        related_name="ips_discovered"
    )

    def __str__(self):
        return f"{self.address or 'Unknown IP'}"


class Port(models.Model):
    """Port model representing network services."""
    
    ip = models.ForeignKey(
        IP, 
        on_delete=models.CASCADE, 
        related_name="ports"
    )
    discovered_by_scans = models.ManyToManyField(
        "core.NmapScan", 
        blank=True, 
        related_name="ports_updated"
    )
    port_number = models.IntegerField(db_index=True)
    protocol = models.CharField(max_length=10)
    state = models.CharField(max_length=20, db_index=True)
    service_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )
    service_version = models.CharField(
        max_length=255, 
        blank=True, 
        null=True
    )
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    last_scan_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True
    )
    last_scan_id = models.IntegerField(
        null=True, 
        blank=True
    )

    history = HistoricalRecords()

    class Meta:
        unique_together = ("ip", "port_number", "protocol")
        indexes = [models.Index(fields=["ip", "port_number"])]

    def __str__(self):
        return (
            f"Port {self.port_number}/{self.protocol} on "
            f"{self.ip.address}"
        )
