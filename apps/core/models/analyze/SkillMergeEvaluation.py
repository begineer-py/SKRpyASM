from django.db import models


class SkillMergeEvaluation(models.Model):
    """
    技能合併評估記錄
    
    由 SkillMergeEvaluator Agent 定期評估 tag 重疊的技能對。
    若判定不可合併，記錄原因，後續不再重複檢查同一對技能。
    
    去重策略：一律以 (較小ID, 較大ID) 存儲，確保 A↔B 與 B↔A 只佔一條記錄。
    """

    skill_a = models.ForeignKey(
        "core.SkillTemplate",
        on_delete=models.CASCADE,
        related_name="merge_evals_as_a",
        help_text="技能 A（ID 較小者）",
    )

    skill_b = models.ForeignKey(
        "core.SkillTemplate",
        on_delete=models.CASCADE,
        related_name="merge_evals_as_b",
        help_text="技能 B（ID 較大者）",
    )

    MERGE_STRATEGY_CHOICES = [
        ("NOT_RECOMMENDED", "不建議合併"),
        ("CONCAT", "串聯 — 合併 instructions 與 tags，保留各自 script"),
        ("UNION", "Union — 合併 schema 與全部內容"),
        ("LATEST_ONLY", "取最新 — 保留版本較新的技能"),
        ("SMART_MERGE", "智能合併 — 自動融合 script 與 instructions"),
        ("A_MERGES_INTO_B", "A 併入 B — A 的功能是 B 的子集"),
        ("B_MERGES_INTO_A", "B 併入 A — B 的功能是 A 的子集"),
    ]
    merge_strategy = models.CharField(
        max_length=30,
        choices=MERGE_STRATEGY_CHOICES,
        null=True,
        blank=True,
        help_text="建議的合併策略",
    )

    is_mergeable = models.BooleanField(
        null=True,
        help_text="null=待評估, True=可合併, False=不建議合併",
    )

    reasoning = models.TextField(
        null=True,
        blank=True,
        help_text="Agent 評估推理過程",
    )

    merged_into = models.ForeignKey(
        "core.SkillTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="merged_from_evaluations",
        help_text="如果已執行合併，指向合併後產生的新技能",
    )

    evaluated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="本次評估時間",
    )

    class Meta:
        db_table = "core_skill_merge_evaluation"
        verbose_name = "Skill 合併評估"
        verbose_name_plural = "Skill 合併評估記錄"
        unique_together = ("skill_a", "skill_b")
        ordering = ["-evaluated_at"]
        indexes = [
            models.Index(fields=["is_mergeable"]),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.skill_a_id and self.skill_b_id:
            if self.skill_a_id == self.skill_b_id:
                raise ValidationError("skill_a and skill_b must be different skills.")
            if self.skill_a_id > self.skill_b_id:
                self.skill_a_id, self.skill_b_id = self.skill_b_id, self.skill_a_id

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MergeEval({self.skill_a.name} ↔ {self.skill_b.name}) [{self.is_mergeable}]"
