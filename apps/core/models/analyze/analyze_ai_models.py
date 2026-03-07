# ./core/models/analyze_ai_models.py
from django.db import models
from django.utils import timezone


class IPAIAnalysis(models.Model):
    """
    針對單一 IP 地址的 AI 深度分析檔案。
    """

    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    ip = models.ForeignKey(
        "core.IP",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )
    status = models.CharField(
        max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True
    )
    error_message = models.TextField(
        null=True, blank=True, help_text="如果任務失敗，記錄錯誤信息"
    )

    # --- 統一結構化情報 ---
    summary = models.TextField(
        null=True, blank=True, help_text="AI 生成的關於此 IP 的一句話總結"
    )
    inferred_purpose = models.TextField(
        null=True,
        blank=True,
        help_text="推斷的服務器用途 (e.g., Web Server, Mail Server, C2)",
    )
    risk_score = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="綜合風險評分 (0-100)"
    )
    potential_vulnerabilities = models.JSONField(  # <--- 新增 & 統一
        null=True, blank=True, help_text="基於開放端口和服務推斷的潛在漏洞列表"
    )
    recommended_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續行動列表"
    )
    command_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續命令列表"
    )

    # --- 專有情報 ---
    port_analysis_summary = models.TextField(
        null=True, blank=True, help_text="對開放端口和服務的綜合分析"
    )

    # --- 原始情報 ---
    raw_response = models.JSONField(
        null=True, blank=True, help_text="AI Provider 返回的完整原始 JSON 數據"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        ipv4 = self.ip.ipv4 or self.ip.ipv6
        return f"AI Analysis for {ipv4} [{self.status}]"


class SubdomainAIAnalysis(models.Model):
    """
    針對單一子域名的 AI 深度分析檔案。
    """

    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    subdomain = models.ForeignKey(
        "core.Subdomain",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )
    status = models.CharField(
        max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True
    )
    error_message = models.TextField(
        null=True, blank=True, help_text="如果任務失敗，記錄錯誤信息"
    )

    # --- 統一結構化情報 ---
    summary = models.TextField(
        null=True, blank=True, help_text="AI 生成的關於此子域名用途和重要性的總結"
    )
    inferred_purpose = models.TextField(
        null=True,
        blank=True,
        help_text="推斷的子域名用途 (e.g., Main Website, API Endpoint, Staging Environment, Blog)",
    )
    risk_score = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="綜合風險評分 (0-100)"
    )
    potential_vulnerabilities = models.JSONField(  # <--- 命名統一
        null=True, blank=True, help_text="基於其屬性推斷的潛在攻擊向量/漏洞列表"
    )
    recommended_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續行動列表"
    )
    command_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續命令列表"
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
        help_text="對其技術棧的風險分析 (e.g., 'Runs outdated WordPress')",
    )

    # --- 原始情報 ---
    raw_response = models.JSONField(
        null=True, blank=True, help_text="AI Provider 返回的完整原始 JSON 數據"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"AI Analysis for {self.subdomain.name} [{self.status}]"


class URLAIAnalysis(models.Model):
    """
    針對單一 URL 的 AI 深度分析檔案。
    """

    ANALYSIS_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    url_result = models.ForeignKey(
        "core.URLResult",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )
    status = models.CharField(
        max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="PENDING", db_index=True
    )
    error_message = models.TextField(
        null=True, blank=True, help_text="如果任務失敗，記錄錯誤信息"
    )

    # --- 統一結構化情報 ---
    summary = models.TextField(  # <--- 命名統一 (原 content_summary)
        null=True, blank=True, help_text="AI 生成的頁面內容摘要"
    )

    inferred_purpose = models.CharField(  # <--- 命名統一 (原 inferred_functionality)
        max_length=255,
        null=True,
        blank=True,
        help_text="推斷的頁面功能 (e.g., Login Panel, API Documentation, Blog Post)",
    )
    risk_score = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="綜合風險評分 (0-100)"
    )
    potential_vulnerabilities = models.JSONField(
        null=True, blank=True, help_text="基於內容和技術棧推斷的潛在漏洞列表"
    )
    recommended_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續行動列表"
    )
    command_actions = models.JSONField(  # <--- 類型升級為 JSONField
        null=True, blank=True, help_text="建議採取的後續命令列表"
    )

    # --- 專有情報 ---
    extracted_entities = models.JSONField(
        null=True, blank=True, help_text="提取出的敏感實體 (emails, API keys, etc.)"
    )

    # --- 原始情報 ---
    raw_response = models.JSONField(
        null=True, blank=True, help_text="AI Provider 返回的完整原始 JSON 數據"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        short_url = (
            self.url_result.url[:70] + "..."
            if len(self.url_result.url) > 70
            else self.url_result.url
        )
        return f"AI Analysis for {short_url} [{self.status}]"
