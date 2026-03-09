from django.db import models

class Step(models.Model):
    # 關聯到具體資產
    ip = models.ManyToManyField("core.IP", null=True, blank=True, related_name="steps")
    subdomain = models.ManyToManyField("core.Subdomain", null=True, blank=True, related_name="steps")
    url_result = models.ManyToManyField("core.URLResult", null=True, blank=True, related_name="steps")
    #由於一次偵察並發掘漏洞的工作可能設計到不同方面,所以皆爲多對多
    order = models.PositiveIntegerField(default=1)
    command_template = models.TextField(help_text="執行命令模板，如 'nmap -p {port} {ip}'")
    expectation = models.TextField(help_text="預期的結果或輸出關鍵字")
    note = models.TextField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        #被驗證無攻擊面的
        ("NO_VULNERABILITY", "No Vulnerability"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    
    created_at = models.DateTimeField(auto_now_add=True)

class Payload(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='payloads')
    content = models.TextField()
    platform = models.CharField(max_length=100)

class Method(models.Model):#實行攻擊的方法
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='methods')
    name = models.CharField(max_length=100)
    description = models.TextField()
    tool_name = models.CharField(max_length=100, null=True, blank=True)
    if_system_tool = models.BooleanField(default=False)#是否使用平臺自帶工具

class Verification(models.Model):
    """
    多策略驗證模型：支援 regex 比對、AI 判斷、人工確認。
    
    驗證流程：
    1. Step 執行完成 → 取得 execution_output
    2. 根據 verify_strategy 決定驗證方式：
       - regex:    用 pattern 對 output 做正則比對
       - contains: 用 pattern 對 output 做子字串比對
       - ai_judge: 把 output + ai_prompt 送給 AI，由 AI 判斷
       - manual:   等待人工確認
    3. 驗證通過 → 可自動建立 Vulnerability（若 auto_create_vulnerability=True）
    """

    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='verifications')

    # ── 基礎驗證（正則 / 子字串）──────────────────────
    pattern = models.TextField(
        null=True, blank=True,
        help_text="驗證用的正則表達式或子字串"
    )
    match_type = models.CharField(
        max_length=20,
        default="contains",
        help_text="比對方式：regex | contains | ai_judge | manual"
    )

    # ── AI 驗證策略 ────────────────────────────────
    VERIFY_STRATEGY_CHOICES = [
        ("regex", "正則表達式比對"),
        ("contains", "子字串比對"),
        ("ai_judge", "AI 智能判斷"),
        ("manual", "人工確認"),
    ]
    verify_strategy = models.CharField(
        max_length=20,
        choices=VERIFY_STRATEGY_CHOICES,
        default="regex",
        help_text="驗證策略類型"
    )
    ai_prompt = models.TextField(
        null=True, blank=True,
        help_text=(
            "給驗證 AI 的指令模板。可用 {output} 引用執行輸出，{command} 引用原始指令。\n"
            "例如：'以下是 nmap 掃描結果：{output}\\n請判斷是否存在匿名 FTP 登入漏洞，"
            "回覆 JSON: {\"verified\": true/false, \"confidence\": 0-100, \"reason\": \"...\"}'"
        )
    )
    confidence_threshold = models.PositiveSmallIntegerField(
        default=80,
        help_text="AI 判斷時的信心門檻 (0-100)，低於此值視為未通過"
    )

    # ── 執行結果 ──────────────────────────────────
    VERDICT_CHOICES = [
        ("PENDING", "待驗證"),
        ("PASSED", "通過"),
        ("FAILED", "未通過"),
        ("INCONCLUSIVE", "無法確定"),
    ]
    verdict = models.CharField(
        max_length=15,
        choices=VERDICT_CHOICES,
        default="PENDING",
        help_text="驗證結果"
    )
    execution_output = models.TextField(
        null=True, blank=True,
        help_text="Step 實際執行後的輸出（用於驗證比對）"
    )
    ai_response = models.JSONField(
        null=True, blank=True,
        help_text="AI 驗證時的完整回應 JSON"
    )
    confidence_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="AI 回傳的信心分數 (0-100)"
    )
    verified_at = models.DateTimeField(
        null=True, blank=True,
        help_text="驗證完成時間"
    )

    # ── 自動漏洞建立 ─────────────────────────────
    auto_create_vulnerability = models.BooleanField(
        default=False,
        help_text="驗證通過時，是否自動建立 Vulnerability 記錄"
    )
    vulnerability_severity = models.CharField(
        max_length=20,
        null=True, blank=True,
        help_text="自動建立漏洞時的嚴重程度 (info/low/medium/high/critical)"
    )
    vulnerability_name = models.CharField(
        max_length=500,
        null=True, blank=True,
        help_text="自動建立漏洞時的名稱"
    )
    created_vulnerability = models.ForeignKey(
        "core.Vulnerability",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="source_verifications",
        help_text="驗證通過後自動建立的 Vulnerability 記錄"
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Verification[{self.verify_strategy}] for Step#{self.step_id} → {self.verdict}"