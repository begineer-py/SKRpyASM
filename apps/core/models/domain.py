# apps/core/models/domain.py
# 網域相關模型：子域名資產與關聯

from django.db import models
from simple_history.models import HistoricalRecords


class SubdomainSeed(models.Model):
    """
    子域名與種子之間的多對多關聯中間表（Through Model）。
    紀錄一個子域名是從哪些掃描起點（Seed）發現的。
    """
    
    subdomain = models.ForeignKey(
        "core.Subdomain", 
        on_delete=models.CASCADE, 
        related_name="seed_links",
        help_text="關聯的子域名記錄"
    )
    seed = models.ForeignKey(
        "core.Seed", 
        on_delete=models.CASCADE, 
        related_name="sub_links",
        help_text="來源種子"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        unique_together = ("subdomain", "seed")
        verbose_name = "子域名-種子關聯"
        verbose_name_plural = "子域名-種子關聯"


class Subdomain(models.Model):
    """
    子域名資產模型。儲存所有由掃描任務發現的域名資訊。
    """
    
    # 直接綁定到目標項目，以便於進行聯動刪除
    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="subdomains",
        null=True,
        blank=True,
        db_index=True,
        help_text="歸屬的目標專案"
    )
    
    # 關聯資訊
    which_seed = models.ManyToManyField(
        "core.Seed", 
        related_name="subdomains", 
        through="SubdomainSeed",
        help_text="發現此子域名的所有種子"
    )
    discovered_by_scans = models.ManyToManyField(
        "core.SubfinderScan", 
        blank=True, 
        related_name="updated_subdomains",
        help_text="參與發現/更新此域名記錄的掃描任務"
    )
    ips = models.ManyToManyField(
        "core.IP", 
        related_name="subdomains", 
        blank=True,
        help_text="此域名解析到的 IP 地址"
    )
    
    # 基本資訊
    name = models.CharField(max_length=255, db_index=True, help_text="域名，例如 'www.google.com'")
    sources_text = models.TextField(
        blank=True, 
        help_text="提供該域名的來源清單（逗號分隔），如: 'Baidu,Subfinder,Amass'"
    )
    
    # 狀態與時間紀錄
    is_active = models.BooleanField(default=True, db_index=True, help_text="目前是否仍可發現該域名（存活狀態）")
    is_resolvable = models.BooleanField(default=True, help_text="DNS 是否可成功解析")
    is_tech_analyzed = models.BooleanField(default=False, help_text="是否已完成技術棧分析")
    first_seen = models.DateTimeField(auto_now_add=True, help_text="首次發現時間")
    last_seen = models.DateTimeField(auto_now=True, help_text="最後一次發現時間")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # DNS 詳細資訊
    dns_records = models.JSONField(null=True, blank=True, help_text="詳細的 DNS 解析記錄（A, AAAA, MX, TXT 等）")
    cname = models.TextField(blank=True, null=True, help_text="CNAME 解析路徑")
    
    # 防護與基礎設施資訊
    is_cdn = models.BooleanField(default=False, help_text="是否使用了 CDN")
    is_waf = models.BooleanField(default=False, help_text="是否受 WAF 保護")
    waf_name = models.TextField(null=True, help_text="識別出的 WAF 名稱")
    cdn_name = models.TextField(null=True, help_text="識別出的 CDN 名稱")
    
    # 最後掃描追蹤
    last_scan_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="最後一次處理此记录的掃描類型名稱"
    )
    last_scan_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text="最後一次掃描的任務 ID"
    )

    # 歷史追蹤
    history = HistoricalRecords(m2m_fields=[ips])

    class Meta:
        app_label = "core"
        verbose_name = "子域名資產"
        verbose_name_plural = "子域名資產"

    def __str__(self):
        return self.name
