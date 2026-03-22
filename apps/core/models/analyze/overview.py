from django.db import models
from django.utils import timezone


class Overview(models.Model):
    """
    階段性概覽 (Strategic Overview)
    ──────────────────────────────────────
    核心職責:
      1. 作為資產群組（IP/Subdomain/URL）的戰略主體
      2. 儲存 AI 目前對該目標的「知識」與「技術棧」
      3. 紀錄當前的「攻擊計畫 (Plan)」與「執行狀態」
    """
    target = models.ForeignKey("core.Target", on_delete=models.CASCADE, null=True, blank=True, related_name="overviews")
    seed = models.ForeignKey("core.Seed", on_delete=models.CASCADE, null=True, blank=True, related_name="overviews")

    # 關聯資產 (多對多，支援交叉關聯)
    ips = models.ManyToManyField("core.IP", blank=True, related_name="overviews")
    subdomains = models.ManyToManyField("core.Subdomain", blank=True, related_name="overviews")
    url_results = models.ManyToManyField("core.URLResult", blank=True, related_name="overviews")

    # 戰略情報
    summary = models.TextField(null=True, blank=True, help_text="目前目標的筆記")
    techs = models.JSONField(null=True, blank=True, help_text="偵測到的技術棧")
    knowledge = models.JSONField(null=True, blank=True, help_text="當前對目標的認知快照")
    plan = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "AI 擬定的結構化計畫。格式: "
            "{objectives: [{id, description, priority, status}], reasoning: str, generated_at: iso8601}"
        ),
    )

    # 狀態管理
    STATUS_CHOICES = [
        ("PLANNING", "戰略規劃中"),
        ("EXECUTING", "執行任務中"),
        ("STALLED", "受阻/待人工"),
        ("COMPLETED", "已達成階段目標"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PLANNING")
    risk_score = models.PositiveSmallIntegerField(default=0, help_text="綜合風險評分 (0-100)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    business_impact = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="推斷的業務重要性 (e.g., Critical, High, Medium, Low)",
    )
    class Meta:
        app_label = "core"
        verbose_name = "階段性概覽"

    def __str__(self):
        return f"Overview[{self.id}] - {self.status} (Risk: {self.risk_score})"