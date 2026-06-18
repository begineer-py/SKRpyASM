from django.db import models


class PoCRecord(models.Model):
    """
    漏洞的 POC（Proof of Concept）驗證記錄。
    一個漏洞可以有多個 POC（不同語言/不同 payload）。
    """

    VULN_POC_LANGUAGE_CHOICES = [
        ("curl", "cURL 命令"),
        ("python", "Python 腳本"),
        ("bash", "Bash 腳本"),
        ("http_request", "原始 HTTP 請求"),
        ("manual", "手動步驟說明"),
    ]

    vulnerability = models.ForeignKey(
        "core.Vulnerability",
        on_delete=models.CASCADE,
        related_name="pocs",
        help_text="所屬的漏洞",
    )
    title = models.CharField(
        max_length=255, help_text="POC 標題，如 'RCE via CVE-2024-XXXX'"
    )
    content = models.TextField(help_text="POC 腳本/payload/步驟內容")
    language = models.CharField(
        max_length=20,
        default="manual",
        choices=VULN_POC_LANGUAGE_CHOICES,
        help_text="POC 語言/類型",
    )
    result = models.TextField(
        null=True, blank=True, help_text="執行結果（選填，可為輸出或觀察）"
    )
    is_verified = models.BooleanField(
        default=False, help_text="是否已成功驗證此 POC"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "POC 記錄"
        verbose_name_plural = "POC 記錄"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_language_display()})"
