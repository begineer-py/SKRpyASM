from django.db import models


class Verification(models.Model):
    """
    AI 驗證模型：純 AI 判斷，無正則/子字串策略。

    驗證流程：
    1. 執行完成後取得 execution_output
    2. 將 observation_prompt（成功標準）與 execution_output 送給 AI
    3. AI 判斷是否達成成功標準，回傳 verdict / confidence / evidence
    4. 驗證通過時可自動建立 Vulnerability
    """

    attack_vector = models.ForeignKey(
        "core.AttackVector",
        on_delete=models.CASCADE,
        related_name="verifications",
        null=True,
        blank=True,
    )

    observation_prompt = models.TextField(
        help_text=(
            "描述這次執行的成功標準，AI 會閱讀實際輸出後判斷是否達成。"
        )
    )
    confidence_threshold = models.PositiveSmallIntegerField(
        default=75, help_text="AI 信心門檻 (0-100)，低於此值視為未通過"
    )

    VERDICT_CHOICES = [
        ("PENDING", "待驗證"),
        ("PASSED", "通過"),
        ("FAILED", "未通過"),
        ("INCONCLUSIVE", "無法確定"),
    ]
    verdict = models.CharField(
        max_length=15, choices=VERDICT_CHOICES, default="PENDING", help_text="驗證結果"
    )
    execution_output = models.TextField(
        null=True, blank=True, help_text="實際執行輸出（用於驗證比對）"
    )
    ai_response = models.JSONField(
        null=True, blank=True, help_text="AI 驗證時的完整回應 JSON"
    )
    confidence_score = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="AI 回傳的信心分數 (0-100)", db_column="confidence"
    )
    verified_at = models.DateTimeField(null=True, blank=True, help_text="驗證完成時間")

    auto_create_vulnerability = models.BooleanField(
        default=False, help_text="驗證通過時，是否自動建立 Vulnerability 記錄"
    )
    vulnerability_severity = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="自動建立漏洞時的嚴重程度 (info/low/medium/high/critical)",
    )
    vulnerability_name = models.CharField(
        max_length=500, null=True, blank=True, help_text="自動建立漏洞時的名稱"
    )
    created_vulnerability = models.ForeignKey(
        "core.Vulnerability",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_verifications",
        help_text="驗證通過後自動建立的 Vulnerability 記錄",
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        av_id = self.attack_vector_id if self.attack_vector_id else "None"
        return f"Verification[AI] for Vector#{av_id} -> {self.verdict}"
