from django.db import models


class SubAgentDispatch(models.Model):
    """
    子代理派發追蹤
    ──────────────────────────────────────
    解決「AutomationAgent 派發子代理後,結果無法結構化回流」的問題。

    核心問題（改造前）：
      spawn_recon_agent → Celery task → notify_caller_agent
      但 notify_caller_agent 依賴 overview.parent_thread_id 路由，
      而 parent_thread_id 可能指向 HackerAssistant（被 bind_to_target 設定），
      導致子代理回報跳過 AutomationAgent。

    解決方案：
      SubAgentDispatch 記錄「誰派發了哪個子代理」，notify_caller_agent
      優先依此表路由到「直屬派發者」（AutomationAgent），而非 overview.parent_thread_id。
    """

    DISPATCH_AGENT_CHOICES = [
        ("recon_agent", "Recon Agent"),
        ("post_exploit_agent", "Post-Exploit Agent"),
        ("reporting_agent", "Reporting Agent"),
    ]

    STATUS_CHOICES = [
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    action = models.ForeignKey(
        "core.Action",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatches",
        help_text="關聯的 Action（若子代理被派發來執行特定行動）",
    )
    overview = models.ForeignKey(
        "core.Overview",
        on_delete=models.CASCADE,
        related_name="dispatches",
        help_text="派發此任務時所屬的 Overview",
    )
    dispatcher_agent = models.CharField(
        max_length=50,
        default="automation_agent",
        help_text="派發者 agent 識別碼",
    )
    dispatcher_thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatches_sent",
        help_text="派發者的 Thread（通常是 AutomationAgent 的 sub_thread）",
    )
    sub_agent_type = models.CharField(
        max_length=50,
        choices=DISPATCH_AGENT_CHOICES,
        help_text="子代理類型",
    )
    sub_thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatches_received",
        help_text="子代理的 Thread",
    )
    objective = models.TextField(
        blank=True,
        default="",
        help_text="派發時賦予子代理的任務目標",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="RUNNING",
        db_index=True,
    )
    result_summary = models.TextField(
        blank=True,
        default="",
        help_text="子代理回報的結果摘要（notify_caller_agent 寫入）",
    )
    synthesized = models.BooleanField(
        default=False,
        db_index=True,
        help_text="AutomationAgent 是否已消化此回報（auto_execute_plan 喚醒後標記）",
    )
    dispatched_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        db_table = "core_subagent_dispatch"
        verbose_name = "子代理派發"
        verbose_name_plural = "子代理派發"
        ordering = ["-dispatched_at"]
        indexes = [
            models.Index(fields=["overview", "status"], name="subdispatch_status_idx"),
            models.Index(fields=["synthesized"], name="subdispatch_synth_idx"),
        ]

    def __str__(self):
        return f"Dispatch[{self.id}] {self.sub_agent_type} → Overview#{self.overview_id} ({self.status})"
