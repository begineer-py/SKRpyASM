from django.db import models


class SkillVerification(models.Model):
    """
    技能驗證歷史記錄
    
    由 SkillVerifier Agent 每次執行驗證時產生，記錄驗證過程、測試輸入、Agent 推理與結果。
    用於追蹤技能的穩定性、判斷何時可晉升為 ROBUST、以及發現退化。
    """

    skill = models.ForeignKey(
        "core.SkillTemplate",
        on_delete=models.CASCADE,
        related_name="verifications",
        help_text="被驗證的技能",
    )

    VERDICT_CHOICES = [
        ("PENDING", "待驗證"),
        ("PASSED", "通過 — 輸出符合預期"),
        ("FAILED", "失敗 — 輸出不符合預期"),
        ("INCONCLUSIVE", "無法確定 — Agent 無法明確判斷"),
        ("ERROR", "系統錯誤 — 執行過程發生異常"),
    ]
    verdict = models.CharField(
        max_length=20,
        choices=VERDICT_CHOICES,
        default="PENDING",
        help_text="驗證裁決",
    )

    confidence_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Agent 對驗證結果的信心程度 (0-100)",
    )

    test_input_used = models.JSONField(
        null=True,
        blank=True,
        help_text="Agent 構造並使用的測試輸入（JSON）",
    )

    raw_output = models.TextField(
        null=True,
        blank=True,
        help_text="執行腳本後的原始輸出",
    )

    agent_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Agent 的評估推理過程（詳細說明為什麼通過/失敗）",
    )

    execution_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="腳本執行耗時（毫秒）",
    )

    executed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="驗證執行時間",
    )

    class Meta:
        db_table = "core_skill_verification"
        verbose_name = "Skill 驗證記錄"
        verbose_name_plural = "Skill 驗證歷史"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["skill", "-executed_at"]),
            models.Index(fields=["verdict"]),
        ]

    def __str__(self):
        return f"Verification#{self.id} [{self.verdict}] for {self.skill.name}"
