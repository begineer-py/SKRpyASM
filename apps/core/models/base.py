# core/models/base.py
# Base models for project and seed management

from django.db import models


class Target(models.Model):
    """Target represents a project or organization being monitored."""
    
    name = models.CharField(
        max_length=255, unique=True, help_text="專案名稱，如 'Google'"
    )
    description = models.TextField(
        null=True, blank=True, help_text="專案描述與備註"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.name


class Seed(models.Model):
    """Seed represents the starting point for scanning activities."""
    
    SEED_TYPE_CHOICES = [
        ("DOMAIN", "Root Domain (e.g., google.com)"),
        ("IP_RANGE", "IP/CIDR (e.g., 192.168.1.0/24)"),
        ("URL", "Specific URL (e.g., https://api.site.com)"),
    ]
    
    target = models.ForeignKey(
        Target, 
        on_delete=models.CASCADE, 
        related_name="seeds"
    )
    value = models.CharField(
        max_length=512, 
        help_text="種子內容，如 google.com"
    )
    type = models.CharField(
        max_length=20, 
        choices=SEED_TYPE_CHOICES, 
        default="DOMAIN"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="是否啟用此種子進行掃描"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("target", "value")

    def __str__(self):
        return f"[{self.type}] {self.value}"
