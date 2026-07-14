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
    target = models.OneToOneField(
        "core.Target",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="overview",
        help_text="1:1 綁定 Target — 每個目標只有一個 Overview 作為情報中樞",
    )
    seed = models.ForeignKey("core.Seed", on_delete=models.CASCADE, null=True, blank=True, related_name="overviews")

    # 關聯資產（多對多 — 標記為「高價值 / 當前關注」的資產，非全部資產）
    ips = models.ManyToManyField("core.IP", blank=True, related_name="highlighted_in_overview")
    subdomains = models.ManyToManyField("core.Subdomain", blank=True, related_name="highlighted_in_overview")
    url_results = models.ManyToManyField("core.URLResult", blank=True, related_name="highlighted_in_overview")

    # 戰略情報（核心高頻欄位 — 1:1 後 Overview 為 Target 唯一情報中樞）
    summary = models.TextField(null=True, blank=True, help_text="目前目標的筆記")
    techs = models.JSONField(null=True, blank=True, help_text="偵測到的技術棧（舊欄位，將逐步淘汰，改用 tech_stack）")
    knowledge = models.JSONField(null=True, blank=True, help_text="當前對目標的認知快照")

    # 核心情報欄位（新增 — 高頻存取，Agent 與子代理直接讀寫）
    recon_summary = models.TextField(
        null=True, blank=True,
        help_text="偵察階段摘要（子域名數量、開放端口、技術棧等高層次總結）",
    )
    tech_stack = models.JSONField(
        null=True, blank=True,
        help_text="偵測到的技術棧快照（結構化，取代 techs）",
    )
    subdomain_intel = models.JSONField(
        null=True, blank=True,
        help_text="子域名情報快照（高價值子域名、解析狀態等）",
    )
    port_service = models.JSONField(
        null=True, blank=True,
        help_text="開放端口與服務快照",
    )
    vuln_intel = models.JSONField(
        null=True, blank=True,
        help_text="確認漏洞情報快照（嚴重度、位置、狀態）",
    )

    # 狀態管理
    STATUS_CHOICES = [
        ("PLANNING", "戰略規劃中"),
        ("EXECUTING", "執行任務中"),
        ("STALLED", "受阻/待人工"),
        ("COMPLETED", "已達成階段目標"),
        ("NEEDS_GUIDANCE", "待指導/升級"),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PLANNING")
    risk_score = models.PositiveSmallIntegerField(default=0, help_text="綜合風險評分 (0-100)")
    rescue_count = models.PositiveSmallIntegerField(
        default=0,
        help_text=(
            "Watchdog 累計救援次數。到達 RESCUE_THRESHOLD_STALLED (3) 時自動轉 STALLED，"
            "到達 RESCUE_THRESHOLD_NEEDS_GUIDANCE (5) 時自動轉 NEEDS_GUIDANCE。"
        ),
    )
    thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="overviews",
        db_column="thread_id",
        help_text="筆記本 Overview 的 AI 對話 Thread (for push-callback)",
    )
    parent_thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_overviews",
        db_column="parent_thread_id",
        help_text="建立此任務的上層節點/Caller Thread (for async completion callback)",
    )

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

    @property
    def plan(self):
        return None

    @plan.setter
    def plan(self, value):
        pass