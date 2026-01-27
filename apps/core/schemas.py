from ninja import Schema, ModelSchema, Field
from typing import List, Optional

from .models import IP
from apps.core.models import (
    URLResult,
    Form,
    JavaScriptFile,
    AnalysisFinding,
    Link,
    Comment,
    MetaTag,
    Iframe,
)


# --- 附屬品 Schema (白名單模式，只保留核心數據) ---
# 這些都沒問題，保持原樣
class LinkSchema(ModelSchema):
    class Meta:
        model = Link
        fields = ["id", "href", "text"]


class CommentSchema(ModelSchema):
    class Meta:
        model = Comment
        fields = ["id", "content"]


class MetaTagSchema(ModelSchema):
    class Meta:
        model = MetaTag
        fields = ["id", "attributes"]


class IframeSchema(ModelSchema):
    class Meta:
        model = Iframe
        fields = ["id", "src"]


class FormSchema(ModelSchema):
    class Meta:
        model = Form
        fields = ["id", "action", "method", "parameters"]


class AnalysisFindingSchema(ModelSchema):
    class Meta:
        model = AnalysisFinding
        fields = [
            "id",
            "pattern_name",
            "line_number",
            "match_content",
            "match_start",
            "match_end",
        ]


class JavaScriptFileSchema(ModelSchema):
    class Meta:
        model = JavaScriptFile
        fields = ["id", "src", "content"]


# --- 核心情報 Schema (組裝所有附屬品) ---


class URLResultSchema(ModelSchema):
    # 這些嵌套定義都沒錯
    forms: List[FormSchema]
    js_files: List[JavaScriptFileSchema]
    findings: List[AnalysisFindingSchema]
    links: List[LinkSchema]
    comments: List[CommentSchema]
    meta_tags: List[MetaTagSchema]
    iframes: List[IframeSchema]

    # resolver 也沒錯
    subdomain_name: Optional[str] = None

    class Meta:
        model = URLResult
        # 定義你要從 URLResult 模型本身獲取哪些欄位
        fields = [
            "id",
            "url",
            "status_code",
            "title",
            "content_length",
            "is_important",
            "created_at",
            "final_url",
            "is_external_redirect",
            # 注意：這裡不要加 "which_scan_task"，因為我們已經把它刪了
        ]


# --- 頂層戰報總結 Schema (保持不變) ---
class URLResultSetSchema(Schema):
    target_id: int
    target_domain: str
    count: int
    results: List[URLResultSchema]


# --- 其他輔助 Schema ---
class ErrorSchema(Schema):
    detail: str


# 1. 單個 IP 的 Schema
class IPSchema(ModelSchema):
    class Meta:
        model = IP
        fields = ["id", "ipv4", "ipv6"]


# 2. IP 列表的包裝盒
class IPResultSetSchema(Schema):
    target_id: int
    target_domain: str
    count: int
    results: List[IPSchema]


class get_ip_by_subdomains(Schema):
    target_id: int
    target_domain: str
    ip: IPSchema


class SuccessSendIPSchema(Schema):  # 定義 TargetSchema 類別
    ips: List[str] = Field(..., description="IP 列表", min_length=1, max_length=10)


class SuccessSendSubdomainSchema(Schema):  # 定義 TargetSchema 類別
    subdomains: List[str] = Field(
        ..., description="子域名列表", min_length=1, max_length=10
    )


class SuccessSendURLSchema(Schema):  # 定義 TargetSchema 類別
    urls: List[str] = Field(..., description="URL 列表", min_length=1, max_length=5)


class nucleiSuccessSendIPSchema(Schema):
    ips: List[str] = Field(..., description="IP 列表", min_length=1, max_length=10)
    tags: List[str] = Field(default=[], description="Nuclei 掃描標籤，決定掃描範圍")


class nucleiSuccessSendHostSchema(Schema):
    hosts: List[str] = Field(..., description="主機列表", min_length=1, max_length=10)
    tags: List[str] = Field(default=[], description="Nuclei 掃描標籤，決定掃描範圍")


class nucleiSuccessSendURLSchema(Schema):
    urls: List[str] = Field(
        ..., description="Nuclei 扫描结果 URL 列表", min_length=1, max_length=5
    )
    tags: List[str] = Field(default=[], description="Nuclei 掃描標籤，決定掃描範圍")


class SuccessSendToAISchema(Schema):  # 定義 TargetSchema 類別
    detail: str
