from django.db import models
from django.utils import timezone

class Overview(models.Model):
    target = models.ForeignKey("core.Target", on_delete=models.CASCADE, null=True, blank=True, related_name="overviews")
    seed = models.ForeignKey("core.Seed", on_delete=models.CASCADE, null=True, blank=True, related_name="overviews")
    techs = models.JSONField(null=True, blank=True)
    knowledge = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "core"
        verbose_name = "階段性概覽"