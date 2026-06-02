from django.db import models
from django.contrib.postgres.indexes import GinIndex


class CVEIntelligence(models.Model):
    """
    CVE 情報記錄，整合多個資料來源（NVD、CISA KEV、EPSS、OSV）
    """
    # 核心識別
    cve_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="CVE 編號，例如 CVE-2024-12345"
    )

    # 漏洞詳情
    description = models.TextField(help_text="CVE 描述")
    severity = models.CharField(
        max_length=20,
        db_index=True,
        help_text="嚴重性等級：CRITICAL, HIGH, MEDIUM, LOW"
    )
    cvss_score = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        help_text="CVSS 分數 (0.0-10.0)"
    )
    cvss_vector = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="CVSS 向量字串"
    )

    # 受影響產品
    affected_products = models.JSONField(
        default=list,
        help_text='受影響的產品清單，格式：[{"vendor": "apache", "product": "struts", "versions": ["2.5.0-2.5.30"]}]'
    )

    # 威脅情報
    exploit_available = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否有公開的 exploit 可用"
    )
    exploited_in_wild = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否已在野外被利用"
    )
    cisa_kev = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否在 CISA Known Exploited Vulnerability 清單中"
    )
    epss_score = models.FloatField(
        null=True,
        blank=True,
        help_text="EPSS 分數：30 天內被利用的機率 (0.0-1.0)"
    )

    # 參考資料
    references = models.JSONField(
        default=list,
        help_text="參考連結清單，包含 advisories、patches、exploits"
    )
    cwe_ids = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="CWE 弱點分類 ID 清單，例如 [\"CWE-79\", \"CWE-502\"]"
    )
    published_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="CVE 發布日期"
    )
    last_modified_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="CVE 最後修改日期"
    )

    # 資料來源追蹤
    data_sources = models.JSONField(
        default=dict,
        help_text='資料來源詳情，格式：{"nvd": {...}, "cisa": {...}, "epss": {...}}'
    )

    # 本地追蹤
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_checked = models.DateTimeField(
        auto_now=True,
        help_text="最後一次檢查更新的時間"
    )

    class Meta:
        app_label = "core"
        verbose_name = "CVE Intelligence"
        verbose_name_plural = "CVE Intelligence Records"
        ordering = ["-cvss_score", "-published_date"]
        indexes = [
            models.Index(fields=["cve_id"]),
            models.Index(fields=["severity", "cvss_score"]),
            models.Index(fields=["cisa_kev", "exploited_in_wild"]),
            models.Index(fields=["published_date"]),
            GinIndex(fields=["affected_products"], name="cve_affected_products_gin"),
            GinIndex(fields=["data_sources"], name="cve_data_sources_gin"),
        ]

    def __str__(self):
        return f"{self.cve_id} ({self.severity}, CVSS: {self.cvss_score or 'N/A'})"

    @property
    def is_critical(self):
        """是否為關鍵漏洞（CISA KEV 或 CVSS >= 9.0）"""
        return self.cisa_kev or (self.cvss_score and self.cvss_score >= 9.0)

    @property
    def risk_score(self):
        """
        綜合風險分數（0-100）
        考慮 CVSS、EPSS、CISA KEV、exploit 可用性
        """
        score = 0

        # CVSS 貢獻 (0-50)
        if self.cvss_score:
            score += (self.cvss_score / 10.0) * 50

        # EPSS 貢獻 (0-20)
        if self.epss_score:
            score += self.epss_score * 20

        # CISA KEV 加成 (+20)
        if self.cisa_kev:
            score += 20

        # Exploit 可用性加成 (+10)
        if self.exploit_available:
            score += 10

        return min(100, score)


class TechStackCVEMapping(models.Model):
    """
    將發現的 TechStack 對應到相關 CVE
    用於追蹤哪些目標的技術棧受到哪些 CVE 影響
    """
    techstack = models.ForeignKey(
        "core.TechStack",
        on_delete=models.CASCADE,
        related_name="cve_mappings",
        help_text="關聯的技術棧記錄"
    )

    cve_intelligence = models.ForeignKey(
        "core.CVEIntelligence",
        on_delete=models.CASCADE,
        related_name="techstack_mappings",
        help_text="關聯的 CVE 情報記錄"
    )

    # 匹配元資料
    version_match = models.CharField(
        max_length=20,
        default="unknown",
        help_text="版本匹配類型：exact（精確匹配）, range（範圍匹配）, unknown（未知）"
    )
    confidence = models.FloatField(
        default=1.0,
        help_text="匹配信心度 (0.0-1.0)"
    )

    # 發現追蹤
    discovered_at = models.DateTimeField(
        auto_now_add=True,
        help_text="發現此 CVE 關聯的時間"
    )
    notified = models.BooleanField(
        default=False,
        help_text="是否已通知相關人員"
    )

    class Meta:
        app_label = "core"
        verbose_name = "TechStack CVE Mapping"
        verbose_name_plural = "TechStack CVE Mappings"
        unique_together = ("techstack", "cve_intelligence")
        indexes = [
            models.Index(fields=["techstack", "confidence"]),
            models.Index(fields=["notified", "discovered_at"]),
        ]

    def __str__(self):
        return f"{self.techstack} → {self.cve_intelligence.cve_id}"
