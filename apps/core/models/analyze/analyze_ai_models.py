# ./core/models/analyze_ai_models.py
from django.db import models
from django.utils import timezone


class InitialAIAnalysis(models.Model):
    """
    初步資產識別的 AI 分析檔案。
    用於粗略快速的掃描，決定是否值得進行深度分析，並提供基本屬性推斷。
    """
    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")
    subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")
    url_result = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="initial_ai_analyses")

    status = models.CharField(max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True)
    error_message = models.TextField(null=True, blank=True, help_text="如果任務失敗，記錄錯誤信息")

    summary = models.TextField(null=True, blank=True, help_text="AI 生成的關於此資產的一句話總結")
    inferred_purpose = models.TextField(null=True, blank=True, help_text="推斷的用途 (e.g., Web Server, API Endpoint)")
    worth_deep_analysis = models.BooleanField(default=False, help_text="AI 判斷是否值得進一步深度分析建立攻擊計畫")
    is_converted = models.BooleanField(default=False, help_text="是否已轉換為 Overview")
    overview = models.ForeignKey("core.Overview", on_delete=models.SET_NULL, null=True, blank=True, related_name="initial_analyses")

    raw_response = models.JSONField(null=True, blank=True, help_text="AI Provider 返回的完整原始 JSON 數據")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        target = self.ip or self.subdomain or self.url_result
        return f"Initial AI Analysis for {target} [{self.status}]"


class BaseAIAnalysis(models.Model):
    """
    所有 AI 深度分析檔案的共用基類（抽象類）。
    提取 IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis 的通用欄位。
    """
    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    # === 戰略上下文 (Continuous Strategy Context) ===
    overview = models.ForeignKey(
        "core.Overview",
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="所屬的戰略概覽 (Overview) 紀錄"
    )
    triggered_by_step = models.ForeignKey(
        "core.Step",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="觸發此次分析的前置步驟 (若是初始分析則為 Null)"
    )
    
    # === 狀態與追蹤 ===
    status = models.CharField(
        max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True
    )
    error_message = models.TextField(
        null=True, blank=True, help_text="如果任務失敗，記錄錯誤信息"
    )
    is_dispatched = models.BooleanField(
        default=False, help_text="是否已經轉換為執行 Step"
    )

    # === 統一結構化情報 ===
    summary = models.TextField(null=True, blank=True, help_text="AI 生成的關於此資產的一句話總結")
    inferred_purpose = models.TextField(null=True, blank=True, help_text="推斷的用途 (e.g., Web Server, API Endpoint)")
    potential_vulnerabilities = models.JSONField(
        null=True, blank=True, help_text="推斷的潛在漏洞列表"
    )
    recommended_actions = models.JSONField(
        null=True, blank=True, help_text="建議採取的後續行動列表"
    )
    command_actions = models.JSONField(
        null=True, blank=True, help_text="建議採取的後續命令列表"
    )

    # === 原始情報與時間戳 ===
    raw_response = models.JSONField(
        null=True, blank=True, help_text="AI Provider 返回的完整原始 JSON 數據"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class IPAIAnalysis(BaseAIAnalysis):
    """
    針對單一 IP 地址的 AI 深度分析檔案。
    """
    ip = models.ForeignKey(
        "core.IP",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )
    
    # --- 專有情報 ---
    port_analysis_summary = models.TextField(
        null=True, blank=True, help_text="對開放端口和服務的綜合分析"
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        ipv4 = self.ip.ipv4 or self.ip.ipv6
        return f"AI Analysis for {ipv4} [{self.status}]"


class SubdomainAIAnalysis(BaseAIAnalysis):
    """
    針對單一子域名的 AI 深度分析檔案。
    """
    subdomain = models.ForeignKey(
        "core.Subdomain",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )

    # --- 專有情報 ---
    business_impact = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="推斷的業務重要性 (e.g., Critical, High, Medium, Low)",
    )
    tech_stack_summary = models.TextField(
        null=True,
        blank=True,
        help_text="對其技術棧的風險分析",
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        return f"AI Analysis for {self.subdomain.name} [{self.status}]"


class URLAIAnalysis(BaseAIAnalysis):
    """
    針對單一 URL 的 AI 深度分析檔案。
    """
    url_result = models.ForeignKey(
        "core.URLResult",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )

    # --- 專有情報 ---
    extracted_entities = models.JSONField(
        null=True, blank=True, help_text="提取出的敏感實體 (emails, API keys, etc.)"
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        short_url = (
            self.url_result.url[:70] + "..."
            if len(self.url_result.url) > 70
            else self.url_result.url
        )
        return f"AI Analysis for {short_url} [{self.status}]"
