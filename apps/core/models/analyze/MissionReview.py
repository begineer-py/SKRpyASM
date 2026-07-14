from django.db import models


class MissionReview(models.Model):
    """
    Mission-level PoC 審查記錄（LLM-as-judge gate）。

    攔截 Overview.status -> COMPLETED 的企圖，由 VerificationService 審查：
      - 蒐集 Overview 下所有 Vulnerability / AttackVector / 掃描覆蓋率
      - 送 LLM 評估 verdict (APPROVED/REJECTED/INCONCLUSIVE)
      - REJECTED 退回 EXECUTING 並注入駁回理由到 thread
      - INCONCLUSIVE 放行但標記 needs_human_review
      - APPROVED 正常允許 COMPLETED

    與 Verification model（per-AttackVector 微觀驗證）不同，這是 macro 層級的審查。
    """

    overview = models.ForeignKey(
        "core.Overview",
        on_delete=models.CASCADE,
        related_name="mission_reviews",
        help_text="被審查的 Overview",
    )

    VERDICT_CHOICES = [
        ("PENDING", "待審查"),
        ("APPROVED", "通過（可設 COMPLETED）"),
        ("REJECTED", "駁回（退回 EXECUTING）"),
        ("INCONCLUSIVE", "無法判定（放行但需人工介入）"),
    ]
    verdict = models.CharField(
        max_length=15, choices=VERDICT_CHOICES, default="PENDING", db_index=True
    )

    # ── 審查輸入快照（當時的證據狀態） ──────────────────────────────
    vuln_count = models.PositiveSmallIntegerField(default=0, help_text="漏洞總數")
    confirmed_vuln_count = models.PositiveSmallIntegerField(default=0, help_text="confirmed 漏洞數")
    high_severity_count = models.PositiveSmallIntegerField(default=0, help_text="high/critical 漏洞數")
    has_poc_evidence = models.BooleanField(default=False, help_text="是否有任何漏洞附 PoC 證據")
    scan_coverage_pct = models.PositiveSmallIntegerField(default=0, help_text="掃描覆蓋率 0-100")

    # ── LLM 輸出 ─────────────────────────────────────────────────
    confidence_score = models.PositiveSmallIntegerField(
        default=0, help_text="LLM 信心分數 0-100"
    )
    reasoning = models.TextField(blank=True, default="", help_text="LLM 的完整分析")
    rejection_reasons = models.JSONField(
        default=list, blank=True, help_text="具體駁回點（結構化清單）"
    )
    suggested_actions = models.JSONField(
        default=list, blank=True, help_text="建議 agent 採取的改善動作"
    )

    # ── 觸發來源 ─────────────────────────────────────────────────
    triggered_by = models.CharField(
        max_length=50,
        help_text="觸發路徑：update_overview_status / propose_next_steps",
    )
    triggered_by_agent = models.CharField(
        max_length=100, blank=True, default="", help_text="觸發審查的 agent id"
    )

    # ── 人工 review 標記 ─────────────────────────────────────────
    needs_human_review = models.BooleanField(
        default=False,
        help_text="INCONCLUSIVE 時設 True，放行 COMPLETED 但標記需人工複查",
    )

    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="審查完成時間")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "mission_review"

    def __str__(self):
        return f"MissionReview[{self.verdict}] for Overview#{self.overview_id} (conf={self.confidence_score})"
