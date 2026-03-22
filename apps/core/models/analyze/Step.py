from django.db import models


class Step(models.Model):#對於一個階段性的步奏產生一個step,內部包含多個attack_vector,多個step構成一個overview
    # 戰略關聯
    overview = models.ForeignKey(
        "core.Overview",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="steps",
    )

    # 關聯到具體資產
    ip = models.ManyToManyField("core.IP", blank=True, related_name="steps")
    subdomain = models.ManyToManyField(
        "core.Subdomain", blank=True, related_name="steps"
    )
    url_result = models.ManyToManyField(
        "core.URLResult", blank=True, related_name="steps"
    )
    # 由於一次偵察並發掘漏洞的工作可能設計到不同方面,所以皆爲多對多
    parent_step = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_steps",
        help_text="父步驟。為 None 表示此 Step 是 Overview 下的頂層步驟。",
    )
    order = models.PositiveIntegerField(default=1)

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        # 等待異步工具完成回調，由 resume_step_execution 觸發喚醒
        ("WAITING_FOR_ASYNC", "Waiting for Async Callback"),
        # 被驗證無攻擊面的,沒有創立下個step的必要
        ("ENDED", "has ended"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)


class StepNote(models.Model):
    step = models.OneToOneField(
        Step, on_delete=models.CASCADE, related_name="note_detail"
    )
    content = models.TextField(
        null=True, blank=True, help_text="AI 的筆記內容或分析細節"
    )
    ai_thoughts = models.TextField(
        null=True, blank=True, help_text="AI 對於這個 Step 的推理過程"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for Step#{self.step_id}"





class Verification(models.Model):
    """
    AI 驗證模型：純 AI 判斷，無正則/子字串策略。

    驗證流程：
    1. Step 執行完成 → 取得 execution_output
    2. 將 observation_prompt（成功標準）與 execution_output 送給 AI
    3. AI 判斷是否達成成功標準，回傳 verified / confidence / reason / evidence
    4. 驗證通過 → 可自動建立 Vulnerability（若 auto_create_vulnerability=True）
    """

    attack_vector = models.ForeignKey(
        "core.AttackVector",
        on_delete=models.CASCADE,
        related_name="verifications",
        null=True,
        blank=True,
    )

    # ── AI 驗證 ────────────────────────────────────
    observation_prompt = models.TextField(
        help_text=(
            "描述「這個步驟的成功標準」，AI 會閱讀實際輸出後判斷是否達成。\n"
            "例如：'nmap 輸出中出現 80/tcp open，且 Service 版本資訊可見'"
        )
    )
    confidence_threshold = models.PositiveSmallIntegerField(
        default=75, help_text="AI 信心門檻 (0-100)，低於此值視為未通過"
    )

    # ── 執行結果 ──────────────────────────────────
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
        null=True, blank=True, help_text="Step 實際執行後的輸出（用於驗證比對）"
    )
    ai_response = models.JSONField(
        null=True, blank=True, help_text="AI 驗證時的完整回應 JSON"
    )
    confidence_score = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="AI 回傳的信心分數 (0-100)"
    )
    verified_at = models.DateTimeField(null=True, blank=True, help_text="驗證完成時間")

    # ── 自動漏洞建立 ─────────────────────────────
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
        return f"Verification[AI] for Step#{self.step_id} → {self.verdict}"
