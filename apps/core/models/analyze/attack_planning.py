from django.db import models

ASSET_TYPE_CHOICES = [
    ("IP", "IP 位址"),
    ("SUBDOMAIN", "子域名"),
    ("URL", "URL 結果"),
    ("ENDPOINT", "端點"),
    ("PORT", "端口"),
]

AGENT_ROLE_CHOICES = [
    ("RECON", "偵察 Agent"),
    ("PENTEST", "滲透 Agent"),
    ("REPORTING", "報告 Agent"),
    ("AUTOMATION", "自動化 Agent"),
]


class AssetVectorLink(models.Model):
    """
    資產↔攻擊向量 中間表

    將任意類型資產（IP / Subdomain / URLResult / Endpoint / Port）
    與 AttackVector 深度綁定，並追蹤哪個 Agent 正在負責此資產上的此向量。
    同時記錄該資產+該向量獲得的資訊。
    """

    attack_vector = models.ForeignKey(
        "core.AttackVector",
        on_delete=models.CASCADE,
        related_name="asset_links",
    )

    ip_asset = models.ForeignKey("core.IP", on_delete=models.SET_NULL, null=True, blank=True)
    subdomain_asset = models.ForeignKey("core.Subdomain", on_delete=models.SET_NULL, null=True, blank=True)
    url_asset = models.ForeignKey("core.URLResult", on_delete=models.SET_NULL, null=True, blank=True)
    endpoint_asset = models.ForeignKey("core.Endpoint", on_delete=models.SET_NULL, null=True, blank=True)
    port_asset = models.ForeignKey("core.Port", on_delete=models.SET_NULL, null=True, blank=True)

    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        default="TARGETED",
        choices=[
            ("TARGETED", "已鎖定/未開始"),
            ("IN_PROGRESS", "進行中"),
            ("COMPLETED", "已完成"),
            ("FAILED", "失敗"),
        ],
    )

    agent_thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_vector_links",
    )
    agent_role = models.CharField(max_length=20, choices=AGENT_ROLE_CHOICES, null=True, blank=True)

    last_result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        verbose_name = "資產向量連結"
        indexes = [
            models.Index(fields=["asset_type", "status"]),
            models.Index(fields=["agent_thread"]),
        ]

    def __str__(self):
        return f"[{self.status}] {self.asset_type} ↔ AttackVector#{self.attack_vector_id}"


class AttackPlan(models.Model):
    """
    攻擊計劃表（與 Overview 解耦）

    獨立成表，不綁定在 Overview 的 plan JSONField 上。
    AI 生成時計劃可一次創立多個 Action，逐步執行。
    支援模糊計劃（指定範圍）與精確計劃（直接指定資產），且可邊做邊加。
    """

    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="attack_plans",
    )
    thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attack_plans",
    )
    objective = models.TextField()

    scope = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            '模糊範圍 + 顯式資產清單。'
            '格式: {"fuzzy": {"asset_types": ["SUBDOMAIN"], "filter": "*.example.com"}, '
            '"explicit_asset_link_ids": [12, 34]}'
        ),
    )

    status = models.CharField(
        max_length=20,
        default="DRAFT",
        choices=[
            ("DRAFT", "草稿"),
            ("ACTIVE", "執行中"),
            ("COMPLETED", "已完成"),
            ("ABANDONED", "已放棄"),
        ],
    )
    parent_plan = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_plans",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        verbose_name = "攻擊計劃"
        indexes = [
            models.Index(fields=["target", "status"]),
        ]

    def __str__(self):
        return f"AttackPlan[{self.id}] {self.status} — {self.objective[:60]}"


class Action(models.Model):
    """
    行動表

    一次行動可針對單一或多個資產，關聯一個或多個攻擊向量（類別）。
    Automation Agent 可回溯自己做過的行動及其 purpose，而非僅依賴 Overview。
    """

    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="actions",
    )
    plan = models.ForeignKey(
        "core.AttackPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    asset_links = models.ManyToManyField(
        "core.AssetVectorLink",
        blank=True,
        related_name="actions",
    )
    attack_vectors = models.ManyToManyField(
        "core.AttackVector",
        through="ActionVector",
        blank=True,
        related_name="actions",
    )

    purpose = models.JSONField(
        default=dict,
        blank=True,
        help_text="本次行動的目的（結構化）",
    )
    purpose_text = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[
            ("PENDING", "待執行"),
            ("IN_PROGRESS", "執行中"),
            ("COMPLETED", "已完成"),
            ("FAILED", "失敗"),
            ("SKIPPED", "已跳過"),
        ],
    )

    agent_thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    agent_role = models.CharField(max_length=20, choices=AGENT_ROLE_CHOICES, null=True, blank=True)

    execution_graph = models.ForeignKey(
        "core.ExecutionGraph",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )

    result_summary = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        verbose_name = "行動"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["plan", "order"]),
            models.Index(fields=["target", "status"]),
        ]

    def __str__(self):
        return f"Action[{self.id}] {self.status} — {self.purpose_text or self.purpose}"


class ActionVector(models.Model):
    """
    Action↔AttackVector through model

    記錄行動↔向量的執行細節（payload、回應等），不塞進 Target/Asset 主表。
    """

    action = models.ForeignKey(
        "core.Action",
        on_delete=models.CASCADE,
        related_name="action_vectors",
    )
    attack_vector = models.ForeignKey(
        "core.AttackVector",
        on_delete=models.CASCADE,
        related_name="action_vectors",
    )
    execution_detail = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "core"
        verbose_name = "行動向量"
        unique_together = [("action", "attack_vector")]

    def __str__(self):
        return f"Action#{self.action_id} ↔ AttackVector#{self.attack_vector_id}"


class AssetLock(models.Model):
    """
    資產鎖表 — 跨向量、資產級別的 Agent 協調鎖

    多 Agent 派發前先查此表：若資產已被持鎖，其他 Agent 不會重複介入。
    """

    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="asset_locks",
    )

    ip_asset = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True)
    subdomain_asset = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True)
    url_asset = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True)
    endpoint_asset = models.ForeignKey("core.Endpoint", on_delete=models.CASCADE, null=True, blank=True)
    port_asset = models.ForeignKey("core.Port", on_delete=models.CASCADE, null=True, blank=True)

    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)

    thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.CASCADE,
        related_name="asset_locks",
    )
    agent_role = models.CharField(max_length=20, choices=AGENT_ROLE_CHOICES)

    lock_status = models.CharField(
        max_length=20,
        default="HELD",
        choices=[
            ("HELD", "持有中"),
            ("RELEASED", "已釋放"),
            ("EXPIRED", "已過期"),
        ],
    )
    acquired_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        verbose_name = "資產鎖"
        indexes = [
            models.Index(fields=["asset_type", "lock_status"]),
            models.Index(fields=["target", "lock_status"]),
        ]

    def __str__(self):
        return f"[{self.lock_status}] {self.asset_type} by Thread#{self.thread_id}"


class AssetEdge(models.Model):
    """
    資產圖邊 — 資產間的關聯邊

    圖思想的基礎：資產為節點，資產間關聯為邊。
    邊的來源：(1) 既有關聯（Subdomain.ips, URLResult.related_subdomains 等）
    (2) 攻擊過程中發現的新關聯（discovered_by_action 記錄哪次行動發現的）
    """

    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="asset_edges",
    )

    from_asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    from_ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_from")
    from_subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_from")
    from_url = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_from")
    from_endpoint = models.ForeignKey("core.Endpoint", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_from")
    from_port = models.ForeignKey("core.Port", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_from")

    to_asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    to_ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_to")
    to_subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_to")
    to_url = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_to")
    to_endpoint = models.ForeignKey("core.Endpoint", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_to")
    to_port = models.ForeignKey("core.Port", on_delete=models.CASCADE, null=True, blank=True, related_name="edges_to")

    edge_type = models.CharField(
        max_length=30,
        choices=[
            ("RESOLVES_TO", "DNS 解析到"),
            ("HOSTS", "託管"),
            ("LINKS_TO", "連結到"),
            ("DISCOVERED_FROM", "發現自"),
            ("CUSTOM", "自訂"),
        ],
    )
    discovered_by_action = models.ForeignKey(
        "core.Action",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovered_edges",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        verbose_name = "資產圖邊"
        indexes = [
            models.Index(fields=["target", "edge_type"]),
            models.Index(fields=["from_asset_type", "to_asset_type"]),
        ]

    def __str__(self):
        return f"{self.from_asset_type}→{self.to_asset_type} ({self.edge_type})"


class WalkCursor(models.Model):
    """
    圖遍歷游標 — 追蹤 AI 在資產圖上的當前位置

    Walk 機制：AI 一次只能移動一個邊（Edge），禁止跳躍到無關資產。
    鄰接約束在 Application 層（Agent 工具層）強制：
    系統提示詞告知 Agent 計劃範圍，Agent 想碰未列出的資產時必須先建 DB 記錄。
    """

    plan = models.OneToOneField(
        "core.AttackPlan",
        on_delete=models.CASCADE,
        related_name="walk_cursor",
    )
    current_asset_link = models.ForeignKey(
        "core.AssetVectorLink",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="walk_cursors_here",
    )
    traversed_edges = models.ManyToManyField(
        "core.AssetEdge",
        blank=True,
        related_name="walked_by",
    )
    pending_edges = models.ManyToManyField(
        "core.AssetEdge",
        blank=True,
        related_name="pending_for",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        verbose_name = "圖遍歷游標"

    def __str__(self):
        return f"WalkCursor for Plan#{self.plan_id} at {self.current_asset_link_id}"
