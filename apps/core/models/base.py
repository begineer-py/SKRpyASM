# apps/core/models/base.py
# 核心基礎模型：專案（Target）與種子（Seed）管理

from django.db import models


class Target(models.Model):
    """
    目標（Target）項目，代表一個正在監控或掃描的專案、組織或客戶。
    它是系統中資產組織的最頂層容器。
    """
    
    name = models.CharField(
        max_length=255, unique=True, help_text="專案或組織的顯示名稱，如 'Google'"
    )
    description = models.TextField(
        null=True, blank=True, help_text="對該專案的詳細描述、背景資訊或備註"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="建立時間")

    class Meta:
        app_label = "core"
        verbose_name = "目標專案"
        verbose_name_plural = "目標專案"

    def __str__(self):
        return self.name


class Seed(models.Model):
    """
    種子（Seed），代表自動化掃描活動的起點。
    一個目標專案可以擁有多個不同類型的種子（網域、IP 段、特定 URL）。
    """
    
    SEED_TYPE_CHOICES = [
        ("DOMAIN", "根網域 (例如: google.com)"),
        ("IP_RANGE", "IP/CIDR 範圍 (例如: 192.168.1.0/24)"),
        ("URL", "特定網址 (例如: https://api.site.com)"),
    ]
    
    target = models.ForeignKey(
        Target, 
        on_delete=models.CASCADE, 
        related_name="seeds",
        help_text="所屬的目標專案"
    )
    value = models.CharField(
        max_length=512, 
        help_text="種子的實際值，如 'example.com' 或 '10.0.0.1/24'"
    )
    type = models.CharField(
        max_length=20, 
        choices=SEED_TYPE_CHOICES, 
        default="DOMAIN",
        help_text="種子類型"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="控制是否對此種子執行例行性掃描任務"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("target", "value")
        verbose_name = "掃描種子"
        verbose_name_plural = "掃描種子"

    def __str__(self):
        return f"[{self.get_type_display()}] {self.value}"
