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


class ScriptExecution(models.Model):
    """
    記錄 AI 生成的臨時腳本執行歷史。
    
    與 SkillTemplate 不同：
    - SkillTemplate: 經過驗證的可重用技能，存入庫中
    - ScriptExecution: 臨時腳本執行記錄，無論是否存入庫都要追蹤
    
    用途：
    1. 追蹤所有臨時腳本，即使沒有保存到 SkillTemplate
    2. 與 Step 和 StepLog 關聯，形成完整的執行鏈
    3. 支持前端顯示「此步驟執行過哪些腳本」
    4. 支持導出攻擊向量的完整腳本清單
    5. 幫助 AI 回溯之前的腳本內容
    """
    
    # 執行的技能（可選，如果不存 SkillTemplate 就為 null）
    skill = models.ForeignKey(
        "core.SkillTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executions",
        help_text="關聯的 SkillTemplate（如果腳本已保存到庫），否則為空"
    )
    
    # 執行的步驟
    step = models.ForeignKey(
        "core.Step",
        on_delete=models.CASCADE,
        related_name="script_executions",
        help_text="觸發此次執行的 Step"
    )
    
    # 攻擊向量（可選，用於攻擊向量導出）
    attack_vector = models.ForeignKey(
        AttackVector,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="script_executions",
        help_text="關聯的攻擊向量（便於導出該向量的所有腳本）"
    )
    
    # 腳本內容（臨時腳本時直接存儲）
    script_content = models.TextField(help_text="執行的腳本代碼")
    script_language = models.CharField(
        max_length=20,
        choices=[("python", "Python"), ("bash", "Bash")],
        default="python",
        help_text="腳本語言"
    )
    
    # 執行參數
    args_string = models.TextField(blank=True, null=True, help_text="傳遞給腳本的命令行參數")
    input_json = models.JSONField(null=True, blank=True, help_text="結構化的輸入參數（JSON）")
    
    # 執行狀態
    STATUS_CHOICES = [
        ("PENDING", "待執行"),
        ("RUNNING", "執行中"),
        ("SUCCESS", "成功"),
        ("FAILED", "失敗"),
        ("TIMEOUT", "逾時"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    
    # 執行結果
    exit_code = models.IntegerField(null=True, blank=True, help_text="腳本退出碼")
    raw_output = models.TextField(blank=True, null=True, help_text="腳本的原始輸出")
    output_json = models.JSONField(null=True, blank=True, help_text="結構化的輸出（JSON），如果腳本輸出了 JSON）")
    error_message = models.TextField(blank=True, null=True, help_text="執行錯誤訊息")
    
    # 驗證狀態（輸入/輸出類型驗證）
    VALIDATION_STATUS_CHOICES = [
        ("NOT_VALIDATED", "未驗證"),
        ("INPUT_INVALID", "輸入驗證失敗"),
        ("OUTPUT_INVALID", "輸出驗證失敗"),
        ("VALIDATED", "驗證通過"),
        ("VALIDATION_ERROR", "驗證過程出錯"),
    ]
    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default="NOT_VALIDATED",
        help_text="輸入/輸出類型驗證狀態"
    )
    validation_error = models.TextField(blank=True, null=True, help_text="驗證失敗的原因")
    
    # 執行時間
    started_at = models.DateTimeField(auto_now_add=True, help_text="執行開始時間")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="執行完成時間")
    execution_duration_ms = models.IntegerField(null=True, blank=True, help_text="執行耗時（毫秒）")
    
    class Meta:
        app_label = "core"
        verbose_name = "腳本執行記錄"
        verbose_name_plural = "腳本執行歷史"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["step", "-started_at"]),
            models.Index(fields=["attack_vector", "-started_at"]),
            models.Index(fields=["skill", "-started_at"]),
            models.Index(fields=["status"]),
        ]
    
    def __str__(self):
        skill_name = self.skill.name if self.skill else "Temporary Script"
        return f"{skill_name} (Step #{self.step.id}) [{self.status}]"
    
    def get_duration(self):
        """計算執行耗時"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None