from django.db import models


class AttackVector(models.Model):
    """
    攻擊向量與攻擊面狀態 (Tactical Attack Vector)
    ──────────────────────────────────────
    核心職責:
      1. 追蹤單一細分漏洞點（Entry Point）的狀態
      2. 紀錄驗證歷史與利用可能性
      3. 關聯到發掘它的 Step
    """

    overview = models.ForeignKey(
        "core.Overview", on_delete=models.CASCADE, related_name="attack_vectors"
    )

    name = models.CharField(
        max_length=500, help_text="向量名稱，如 'Reflected XSS on /api/user'"
    )
    description = models.TextField(null=True, blank=True)

    VECTOR_TYPE_CHOICES = [
        ("WEB_VULN", "Web 漏洞 (OWASP)"),
        ("NETWORK_EXPOSURE", "網絡服務曝露"),
        ("AUTH_BYPASS", "權限繞過/認證缺陷"),
        ("INFO_LEAK", "信息洩漏"),
        ("CONFIG_ISSUE", "配置錯誤"),
        ("OTHER", "其他"),
    ]
    vector_type = models.CharField(
        max_length=30, choices=VECTOR_TYPE_CHOICES, default="OTHER"
    )

    # 狀態管理
    STATUS_CHOICES = [
        ("IDENTIFIED", "已發現/未嘗試"),
        ("TESTING", "正在測試中"),
        ("EXPLOITABLE", "確認可利用 (Positive)"),
        ("EXHAUSTED", "已嘗試無果 (Negative)"),
        ("MITIGATED", "已修復/緩解"),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="IDENTIFIED"
    )

    risk_score = models.PositiveSmallIntegerField(
        default=0, help_text="該向量的風險評分 (0-100)"
    )
    evidence = models.TextField(
        null=True, blank=True, help_text="可利用性的具體證據/Payload"
    )

    discovery_step = models.ForeignKey(
        "core.Step",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovered_vectors",
        help_text="發現此向量的步驟",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()

    class Meta:
        app_label = "core"
        verbose_name = "攻擊向量"

    def __str__(self):
        return f"[{self.status}] {self.name} ({self.vector_type})"

class Payload(models.Model):
    attack_vector = models.ForeignKey(
        AttackVector, on_delete=models.CASCADE, related_name="payloads"
    )
    content = models.TextField()
    PLATFORM_CHOICES = [
        ("linux", "Linux"),
        ("windows", "Windows"),
        ("macos", "macOS"),
        ("web", "Web (Browser)"),
        ("universal", "Universal"),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="universal")

class CommandTemplate(models.Model):
    attack_vector = models.ForeignKey(AttackVector, on_delete=models.CASCADE, related_name="command_templates")
    name = models.CharField(max_length=100)
    description = models.TextField()
    tool_name = models.CharField(max_length=100, null=True, blank=True)
    if_system_tool = models.BooleanField(default=False, help_text="是否使用平臺自帶工具")
    command = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class CommandExecution(models.Model):
    """
    記錄 CommandTemplate 每次實際執行的結果。
    解决原來 reslut 單一欄位被覆寫的問題。
    """
    STATUS_CHOICES = [
        ("PENDING", "待執行"),
        ("RUNNING", "執行中"),
        ("SUCCESS", "成功"),
        ("FAILED", "失敗"),
    ]
    template = models.ForeignKey(
        CommandTemplate,
        on_delete=models.CASCADE,
        related_name="executions",
        help_text="執行的命令模板",
    )
    triggered_by_step = models.ForeignKey(
        "core.Step",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="command_executions",
        help_text="觸發此次執行的 Step",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    result = models.TextField(null=True, blank=True, help_text="執行輸出結果")
    error_message = models.TextField(null=True, blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution of {self.template.name} [{self.status}]"