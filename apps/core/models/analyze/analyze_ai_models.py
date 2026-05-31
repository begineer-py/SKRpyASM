from django.db import models


class InitialAIAnalysis(models.Model):
    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")#關聯到的資產
    subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")#關聯到的資產
    url_result = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")

    status = models.CharField(max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True)
    error_message = models.TextField(null=True, blank=True)

    summary = models.TextField(null=True, blank=True)
    inferred_purpose = models.TextField(null=True, blank=True)
    worth_deep_analysis = models.BooleanField(default=False)
    risk_score = models.PositiveSmallIntegerField(default=0)
    is_converted = models.BooleanField(default=False)
    overview = models.ForeignKey("core.Overview", on_delete=models.SET_NULL, null=True, blank=True, related_name="initial_analyses")

    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        target = self.ip or self.subdomain or self.url_result
        return f"Initial AI Analysis for {target} [{self.status}]"
