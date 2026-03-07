from django.db import models


class TechStack(models.Model):
    """
    技術棧明細表：記錄 Nginx, PHP, Ubuntu 等具體技術
    """

    which_url_result = models.ForeignKey(
        "URLResult",
        on_delete=models.CASCADE,
        related_name="technologies",
        null=True,
        blank=True,
    )
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
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        unique_together = ("which_url_result", "name", "version")

    def __str__(self):
        return f"{self.name} {self.version or ''}"
