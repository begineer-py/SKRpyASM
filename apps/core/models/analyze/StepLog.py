from django.db import models, transaction
from django.utils import timezone


class StepLog(models.Model):
    """
    細粒度執行日誌：記錄 Step 執行過程中的每個動作和事件。
    
    一對多關係：Step (1) ←→ (Many) StepLog
    
    用途：
    - 記錄 AI 執行的每個動作（execute_skill、run_command、curl 等）
    - 捕捉中間結果和思考過程
    - 支援實時推送到前端（SSE）
    - 便於重現和調試 AI 的執行流程
    """
    
    # 關聯到 Step
    step = models.ForeignKey(
        "core.Step",
        on_delete=models.CASCADE,
        related_name="logs",
        db_index=True,
        help_text="所屬的 Step"
    )
    
    # 日誌等級
    LEVEL_CHOICES = [
        ("INFO", "Info"),
        ("DEBUG", "Debug"),
        ("WARN", "Warning"),
        ("ERROR", "Error"),
        ("AI_THOUGHT", "AI Thought Process"),
        ("ACTION", "Action Started"),
        ("RESULT", "Action Result"),
    ]
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="INFO",
        help_text="日誌等級"
    )
    
    # 日誌分類標籤
    TAG_CHOICES = [
        ("SKILL_EXEC", "Skill Execution"),
        ("COMMAND", "Shell Command"),
        ("API_CALL", "API Call"),
        ("SCAN", "Scanning Tool"),
        ("PARSE", "Result Parsing"),
        ("DECISION", "Decision Making"),
        ("ERROR_HANDLING", "Error Handling"),
        ("STATE_UPDATE", "State Update"),
        ("CHECKPOINT", "Checkpoint"),
    ]
    tag = models.CharField(
        max_length=30,
        choices=TAG_CHOICES,
        default="CHECKPOINT",
        help_text="日誌分類標籤"
    )
    
    # 日誌內容
    message = models.TextField(
        help_text="詳細的日誌訊息（可包含命令、輸出、錯誤棧跡等）"
    )
    
    # 執行狀態（用於 ACTION 和 RESULT 日誌）
    action_status = models.CharField(
        max_length=50,
        choices=[
            ("STARTED", "Started"),
            ("IN_PROGRESS", "In Progress"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
            ("PARTIAL", "Partial Success"),
            ("SKIPPED", "Skipped"),
        ],
        null=True,
        blank=True,
        help_text="動作的執行狀態"
    )
    
    # 關鍵指標（可選的結構化數據）
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="執行耗時（毫秒）"
    )
    
    # 時間戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="日誌建立時間"
    )
    
    # 序列號（便於排序和實時推送）
    sequence = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="此 Step 內的日誌序列號"
    )
    
    class Meta:
        ordering = ['step', 'sequence', 'created_at']
        indexes = [
            models.Index(fields=['step', 'created_at']),
            models.Index(fields=['step', 'level']),
            models.Index(fields=['step', 'tag']),
        ]
    
    def __str__(self):
        return f"Log#{self.id} (Step#{self.step_id}) [{self.level}] {self.message[:50]}"
    
    def save(self, *args, **kwargs):
        # 使用 select_for_update 防止並發下序列號重複
        if not self.sequence:
            with transaction.atomic():
                last_seq = StepLog.objects.select_for_update().filter(
                    step=self.step
                ).aggregate(models.Max('sequence'))['sequence__max'] or 0
                self.sequence = last_seq + 1

        super().save(*args, **kwargs)
