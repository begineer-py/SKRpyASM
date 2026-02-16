from email.policy import default
from random import choices
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from c2_core.config.logging import log_function_call
import logging

logger = logging.getLogger(__name__)


class URLResult(models.Model):
    """URL 資產（單一 URL 的掃描/抓取結果）。

    這個 model 主要用來承載「某個 target 底下發現到的 URL」與其抓取結果（狀態碼、標題、內容、header 等）。
    另外也會保留：
    - 發現來源（scan/crawl/js/brute/api）
    - 抓取狀態（成功/被擋/timeout…）
    - 是否使用 flaresolverr、是否重要、是否 external redirect

    常見用途：
    - 後台查看 URL 掃描清單
    - 後續從 HTML/JS 抽取 endpoint、參數、finding
    """

    # === 關聯與歸屬 ===
    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="urls",
        null=True,
        blank=True,
        db_index=True,
        help_text="此 URL 所屬的目標（Target）。如果只先綁 subdomain，會在 signal 中自動同步 target。",
    )
    related_subdomains = models.ManyToManyField(
        "core.Subdomain",
        related_name="related_urls",
        blank=True,
        help_text="此 URL 來源/歸屬的 subdomain（可多個）。用於關聯與後續統計。",
    )

    # === 發現來源 ===
    DISCOVERY_SOURCE_CHOICES = [
        ("SCAN", "Initial Scan"),
        ("CRAWL_html", "Web Crawler (HTML)"),
        ("JS_EXT", "JS/Xurls Extraction"),
        ("BRUTE", "Directory Brute Force"),
        ("API", "External API Discovery"),
    ]
    discovery_source = models.CharField(
        max_length=20,
        choices=DISCOVERY_SOURCE_CHOICES,
        default="SCAN",
        help_text="此 URL 是透過哪種方式被發現（初始掃描、爬蟲、JS 抽取、爆破、外部 API）。",
    )

    # === 抓取狀態 ===
    CONTENT_FETCH_STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("SUCCESS_FETCHED", "SUCCESS_FETCHED"),
        ("SUCCESS_REDIRECTED_EXTERNAL", "SUCCESS_REDIRECTED_EXTERNAL"),
        ("FAILED_NO_CONTENT", "FAILED_NO_CONTENT"),
        ("FAILED_NETWORK_ERROR", "FAILED_NETWORK_ERROR"),
        ("FAILED_BLOCKED", "FAILED_BLOCKED"),
        ("FAILED_DNS_ERROR", "FAILED_DNS_ERROR"),
        ("FAILED_TIMEOUT", "FAILED_TIMEOUT"),
        ("FAILED_CLIENT_ERROR", "FAILED_CLIENT_ERROR"),
        ("FAILED_SERVER_ERROR", "FAILED_SERVER_ERROR"),
    ]
    content_fetch_status = models.CharField(
        max_length=30,
        choices=CONTENT_FETCH_STATUS_CHOICES,
        default="PENDING",
        db_index=True,
        help_text="抓取/下載內容的狀態（成功、失敗原因、是否被導向外部…）。",
    )

    # === 核心數據 ===
    url = models.URLField(
        max_length=2048,
        db_index=True,
        help_text="完整 URL（含 scheme/host/path/query）。在同一個 target 下與 url 組合唯一。",
    )
    method = models.CharField(
        max_length=10,
        default="GET",
        help_text="抓取該 URL 時使用的方法（通常為 GET）。",
    )

    status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="HTTP status code（若尚未抓取或失敗可為空）。",
    )
    title = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="HTML <title>（若不是 HTML 或未解析則為空）。",
    )
    content_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="回應內容長度（bytes），供去重/排序/判斷是否抓到內容。",
    )
    headers = models.JSONField(
        null=True,
        blank=True,
        help_text="HTTP response headers（dict/JSON）。",
    )
    raw_response = models.TextField(
        null=True,
        blank=True,
        help_text="原始回應內容（可能包含 binary/非 UTF-8 時可視情況留空或存 base64/截斷）。",
    )
    text = models.TextField(
        null=True,
        blank=True,
        help_text="回應內容的文字版本（例如 decoded text）。",
    )
    cleaned_html = models.TextField(
        null=True,
        blank=True,
        help_text="清理後的 HTML（去除噪音後，供抽取 link/form/meta 等分析）。",
    )
    raw_response_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="raw_response 的 hash（用於快速去重/比對）。",
    )

    # === 追蹤與標記 ===
    used_flaresolverr = models.BooleanField(
        default=False,
        help_text="抓取此 URL 時是否使用 FlareSolverr（通常用於繞過 JS challenge/CF）。",
    )
    is_important = models.BooleanField(
        default=False,
        db_index=True,
        help_text="人工或規則標記的重要 URL（可用於優先分析/報表）。",
    )
    is_external_redirect = models.BooleanField(
        default=False,
        db_index=True,
        help_text="此 URL 最終是否導向到 target 之外（external redirect）。",
    )
    final_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="跟隨 redirect 後的最終 URL（如有）。",
    )

    last_scan_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="最後一次產生/更新此記錄的掃描類型（純紀錄用，可選）。",
    )
    last_scan_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="最後一次產生/更新此記錄的掃描 ID（純紀錄用，可選）。",
    )
    discovered_by_scans = models.ManyToManyField(
        "core.URLScan",
        related_name="results",
        help_text="哪些 URLScan 產生或關聯了此 URLResult（可多次、多來源）。",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"[{self.status_code or '???'}] {self.url}"

    class Meta:
        unique_together = ("target", "url")
        app_label = "core"


class Form(models.Model):
    """HTML 表單（保留原始結構）。

    這裡主要存「頁面上解析出的 form 結構」以便追溯。
    若要做參數分析/去重與統計，建議使用 URLParameter（掛在 Endpoint 底下）。
    """

    # 保留此模型用於記錄 HTML 原始結構，但分析後的參數應存入 URLParameter
    which_url = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="forms",
        help_text="此表單所在的 URLResult（頁面）。",
    )
    action = models.CharField(
        max_length=2048,
        help_text="form action（可能是相對路徑或完整 URL）。",
    )
    method = models.CharField(
        max_length=10,
        help_text="form method（GET/POST…）。",
    )
    parameters = models.JSONField(
        default=dict,
        help_text="解析到的 input/select/textarea 等欄位（原始結構）。",
    )

    class Meta:
        unique_together = ("which_url", "action", "method")

    def __str__(self):
        return f"Form on {self.which_url.url} to {self.action}"


class Endpoint(models.Model):
    """
    核心資產表：API 與 頁面 的唯一性定義
    """

    target = models.ForeignKey(
        "core.Target",
        on_delete=models.CASCADE,
        related_name="endpoints",
        null=True,
        blank=True,
        help_text="此 endpoint 所屬 target。若只先綁 subdomain，會在 signal 中自動同步 target。",
    )

    related_subdomains = models.ManyToManyField(
        "core.Subdomain",
        related_name="endpoints",
        blank=True,
        help_text="此 endpoint 相關的 subdomain（可多個）。",
    )
    discovered_by_inline_js = models.ManyToManyField(
        "core.ExtractedJS",
        related_name="found_endpoints",  # <--- 加上這個，ExtractedJS 才有這個屬性
        blank=True,
        help_text="哪些內嵌 JS 區塊包含指向此 Endpoint 的 API 呼叫",
    )
    # 核心定義 (Method + Path)
    path = models.CharField(
        max_length=2048,
        db_index=True,
        help_text="endpoint path（通常是 /api/v1/...；可含 query template 視你的抽取器而定）。",
    )
    method = models.CharField(
        max_length=10,
        default="GET",
        choices=[
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
            ("PATCH", "PATCH"),
            ("OPTIONS", "OPTIONS"),
            ("HEAD", "HEAD"),
        ],
        db_index=True,
        help_text="HTTP method。此欄位搭配 path 與 target 做唯一性判定。",
    )

    # === 多對多關係：誰發現了這個 Endpoint ===

    # 1. 透過 HTML 連結或表單發現
    discovered_by_urls = models.ManyToManyField(
        URLResult,
        related_name="found_endpoints",
        blank=True,
        help_text="哪些頁面包含指向此 Endpoint 的連結或表單",
    )

    # 2. 透過 JS API Call 發現
    discovered_by_js = models.ManyToManyField(
        "core.JavascriptFile",
        related_name="found_endpoints",
        blank=True,
        help_text="哪些 JS 檔案包含指向此 Endpoint 的 API 呼叫",
    )

    # 方便查詢是哪個掃描工具建立的 (Optional)
    discovered_by_scans = models.ManyToManyField(
        "core.URLScan",
        related_name="endpoints",
        blank=True,
        help_text="哪些 URLScan 建立/更新了此 endpoint（輔助追溯）。",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        # 在同一個 Target 下，Method + Path 唯一
        unique_together = ("target", "method", "path")
        indexes = [
            models.Index(fields=["path", "method"]),
        ]
        app_label = "core"

    def __str__(self):
        return f"[{self.method}] {self.path}"


class URLParameter(models.Model):
    """
    輸入參數表：掛載於 Endpoint 下
    """

    which_endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.CASCADE,
        related_name="query_parameters",
        help_text="此參數所屬 endpoint。",
    )

    # 移除 redundant 的 method 欄位，因為 Endpoint 已經決定了 method
    # 如果真的需要針對同一 endpoint 不同 method 存參數，應該建立兩個 Endpoint 物件

    key = models.CharField(
        max_length=255,
        db_index=True,
        help_text="參數名稱（key）。",
    )
    value = models.TextField(
        null=True,
        blank=True,
        help_text="觀察到的範例值（可用於推斷型別/敏感度），不保證每次都有。",
    )  # 範例值

    source_type = models.CharField(
        max_length=20,
        choices=[
            ("form", "Form"),
            ("javascript", "JS"),
            ("querystring", "QueryString"),
        ],
        null=True,
        help_text="參數來源（表單/JS 抽取/querystring）。",
    )

    param_location = models.CharField(
        max_length=10,
        choices=[
            ("query", "Query String"),
            ("body", "Body"),  # 可以擴展為 body_form, body_json
        ],
        default="query",
        help_text="參數位置（query 或 body）。",
    )

    # Hash: 用於快速查找去重 (which_endpoint_id + key + param_location)
    param_hash = models.CharField(
        max_length=64,
        db_index=True,
        editable=False,
        help_text="由 which_endpoint + param_location + key 計算出的 sha256，用於加速查詢/比對。",
    )

    data_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="推斷出的型別（如 string/int/bool/json 等；可選）。",
    )
    line_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="若從原始檔案/內容抽取，記錄行號方便回溯（可選）。",
    )

    class Meta:
        # 重點修正：必須包含 which_endpoint，否則全域只能有一個 "id" 參數
        unique_together = ("which_endpoint", "param_location", "key")
        app_label = "core"

    def save(self, *args, **kwargs):
        # 自動計算 hash
        import hashlib

        data = f"{self.which_endpoint_id}-{self.param_location}-{self.key}"
        self.param_hash = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key} ({self.param_location})"


# 其他輔助模型 (AnalysisFinding, Link, MetaTag, Iframe, Comment, ExtractedJS, JSONObject) 保持原樣...
# 略 (請保留你原本的代碼)
# ...


class AnalysisFinding(models.Model):
    """內容分析結果（pattern 命中）。

    用於保存掃描規則（pattern）在特定 URL 的命中位置與內容片段。
    """

    which_url_result = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="findings",
        help_text="命中的 URLResult。",
    )
    pattern_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="命中的規則/模式名稱。",
    )
    line_number = models.PositiveIntegerField(
        help_text="命中行號（若有行號概念，例如對 text/cleaned_html 做 line split）。",
    )
    match_content = models.TextField(help_text="命中的文字片段。")
    match_start = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="命中起始位置（字元 index，可選）。",
    )
    match_end = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="命中結束位置（字元 index，可選）。",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("which_url_result", "pattern_name", "line_number")
        app_label = "core"

    def __str__(self):
        return f"{self.pattern_name} at line {self.line_number}"


class Link(models.Model):
    """從 HTML 抽取的超連結。"""

    which_url = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="links",
        help_text="此 link 所在的 URLResult。",
    )
    href = models.TextField(help_text="連結位址（原始 href）。")
    text = models.TextField(
        null=True,
        blank=True,
        help_text="連結文字（anchor text）。",
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.href


class MetaTag(models.Model):
    """從 HTML 抽取的 meta tag。"""

    which_url = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="meta_tags",
        help_text="此 meta tag 所在的 URLResult。",
    )
    attributes = models.JSONField(
        help_text="meta tag 的 attributes（例如 name/property/content）。"
    )

    class Meta:
        app_label = "core"

    def __str__(self):
        return str(self.attributes)


class Iframe(models.Model):
    """從 HTML 抽取的 iframe。"""

    which_url = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="iframes",
        help_text="此 iframe 所在的 URLResult。",
    )
    src = models.TextField(help_text="iframe src（原始值）。")

    class Meta:
        unique_together = ("which_url", "src")
        app_label = "core"

    def __str__(self):
        return self.src


class Comment(models.Model):
    """從 HTML 抽取的註解（<!-- -->）。"""

    which_url = models.ForeignKey(
        URLResult,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="此 comment 所在的 URLResult。",
    )
    content = models.TextField(help_text="註解內容（不含 <!-- -->）。")

    class Meta:
        app_label = "core"

    def __str__(self):
        return self.content[:50]


class JSONObject(models.Model):
    """JSON 結構抽取結果。

    可能來源：
    - HTML 中抽出的 inline JS（which_extracted_js）
    - 外部 JS 檔案（which_javascript_file）

    欄位如 path/depth/key/struct/val 主要用於表示 JSON tree 的節點資訊，方便做風險評分與回溯。
    """

    which_extracted_js = models.ForeignKey(
        "ExtractedJS",
        on_delete=models.CASCADE,
        related_name="json_objects",
        null=True,
        blank=True,
        help_text="若 JSON 來源為 inline JS block，指向 ExtractedJS。",
    )
    which_javascript_file = models.ForeignKey(
        "JavaScriptFile",
        on_delete=models.CASCADE,
        related_name="json_objects",
        null=True,
        blank=True,
        help_text="若 JSON 來源為外部 JS 檔案，指向 JavaScriptFile。",
    )
    score = models.FloatField(
        null=True,
        blank=True,
        help_text="此 JSON 節點的風險/重要性分數（可選，依你的分析器而定）。",
    )
    path = models.TextField(
        null=True,
        blank=True,
        help_text="節點在 JSON 中的路徑（例如 $.a.b[0].c）。",
    )
    depth = models.IntegerField(
        null=True,
        blank=True,
        help_text="節點深度（root=0 或 1 依你的實作）。",
    )
    key = models.TextField(
        null=True,
        blank=True,
        help_text="節點 key（若為 object）。",
    )
    struct = models.TextField(
        null=True,
        blank=True,
        help_text="節點型別/結構描述（例如 object/array/string）。",
    )
    val = models.TextField(
        null=True,
        blank=True,
        help_text="節點值（可能為截斷後的字串表示）。",
    )

    class Meta:
        app_label = "core"


# === Signals ===


@receiver(m2m_changed, sender=URLResult.related_subdomains.through)
@log_function_call()
def sync_url_target(sender, instance, action, **kwargs):
    if action == "post_add":
        if not instance.target_id:
            logger.info(f"Signal 觸發：正在為 {instance.url} 同步 Target")  # 加這行

            first_sub = instance.related_subdomains.first()
            if first_sub:
                URLResult.objects.filter(pk=instance.pk).update(target=first_sub.target)


@receiver(m2m_changed, sender=Endpoint.related_subdomains.through)
def sync_endpoint_target(sender, instance, action, **kwargs):
    if action == "post_add":
        if not instance.target_id:
            first_sub = instance.related_subdomains.first()
            if first_sub:
                Endpoint.objects.filter(pk=instance.pk).update(target=first_sub.target)
