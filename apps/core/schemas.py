from ninja import Schema, ModelSchema, Field
from typing import Any, List, Optional
from datetime import datetime

from .models import IP
from apps.core.models import (
    ExecutionArtifact,
    ExecutionEvent,
    ExecutionGraph,
    ExecutionNode,
    ThreadEvent,
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
            "dom_snapshot",
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


class ExecutionGraphSchema(ModelSchema):
    thread_id: Optional[int] = None

    class Meta:
        model = ExecutionGraph
        fields = [
            "id",
            "assistant_id",
            "run_id",
            "title",
            "status",
            "metadata",
            "started_at",
            "updated_at",
            "completed_at",
        ]


class ExecutionNodeSchema(ModelSchema):
    graph_id: int
    parent_id: Optional[int] = None

    class Meta:
        model = ExecutionNode
        fields = [
            "id",
            "name",
            "kind",
            "status",
            "tool_call_id",
            "external_task_id",
            "wait_reason",
            "input",
            "output",
            "error",
            "metadata",
            "sequence",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class ExecutionEventSchema(ModelSchema):
    graph_id: int
    node_id: Optional[int] = None

    class Meta:
        model = ExecutionEvent
        fields = [
            "id",
            "event_type",
            "status",
            "content",
            "payload",
            "sequence",
            "created_at",
        ]


class ExecutionArtifactSchema(ModelSchema):
    graph_id: int
    node_id: Optional[int] = None
    content_blob_id: Optional[int] = None

    class Meta:
        model = ExecutionArtifact
        fields = [
            "id",
            "artifact_type",
            "name",
            "content",
            "data",
            "metadata",
            "created_at",
        ]


class ThreadEventSchema(ModelSchema):
    thread_id: int

    class Meta:
        model = ThreadEvent
        fields = [
            "id",
            "event_type",
            "node_name",
            "tool_name",
            "status",
            "content",
            "payload",
            "sequence",
            "created_at",
        ]


class ExecutionGraphDetailSchema(ExecutionGraphSchema):
    nodes: List[ExecutionNodeSchema]
    events: List[ExecutionEventSchema]
    artifacts: List[ExecutionArtifactSchema]


# 1. 單個 IP 的 Schema
class IPSchema(ModelSchema):
    class Meta:
        model = IP
        fields = ["id", "address", "version"]


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


class PentestHeaderConfigOut(Schema):
    enabled: bool
    username: str
    header_prefix: str
    updated_at: datetime


class PentestHeaderConfigUpdate(Schema):
    enabled: Optional[bool] = None
    username: Optional[str] = None
    header_prefix: Optional[str] = None


class TargetRequestConfigOut(Schema):
    target_id: int
    header_enabled: Optional[bool] = None
    header_username: Optional[str] = None
    header_prefix: Optional[str] = None
    custom_headers: dict = {}
    rps: Optional[int] = None
    max_concurrency: Optional[int] = None
    timeout: Optional[int] = None
    updated_at: datetime


class TargetRequestConfigUpdate(Schema):
    header_enabled: Optional[bool] = None
    header_username: Optional[str] = None
    header_prefix: Optional[str] = None
    custom_headers: Optional[dict] = None
    rps: Optional[int] = None
    max_concurrency: Optional[int] = None
    timeout: Optional[int] = None


class ResolvedRequestConfigOut(Schema):
    enabled: bool
    username: str
    header_prefix: str
    custom_headers: dict
    rps: Optional[int] = None
    max_concurrency: Optional[int] = None
    timeout: Optional[int] = None


class SuccessSendToAISchema(Schema):
    detail: str


# --- Nuclei 掃描請求 (全 ID 化) ---


class NucleiScanIPByIdsSchema(Schema):
    ids: List[int] = Field(..., description="IP ID 陣列 (必須是 List[int], 例如 [123])", min_length=1, max_length=10)
    tags: List[str] = Field(default=[], description="Nuclei 標籤陣列 (字串陣列)")
    execution_graph_id: Optional[int] = Field(None, description="ExecutionGraph ID")
    execution_node_id: Optional[int] = Field(None, description="ExecutionNode ID")


class NucleiScanSubdomainByIdsSchema(Schema):
    ids: List[int] = Field(
        ..., description="子域名 ID 陣列 (必須是 List[int], 例如 [123])", min_length=1, max_length=100
    )
    tags: List[str] = Field(default=[], description="Nuclei 標籤陣列 (字串陣列)")
    execution_graph_id: Optional[int] = Field(None, description="ExecutionGraph ID")
    execution_node_id: Optional[int] = Field(None, description="ExecutionNode ID")


class NucleiScanURLByIdsSchema(Schema):
    ids: List[int] = Field(..., description="URL ID 陣列 (必須是 List[int], 例如 [123])", min_length=1, max_length=10)
    tags: Optional[List[str]] = Field(default=None, description="Nuclei 標籤陣列 (字串陣列)")
    execution_graph_id: Optional[int] = Field(None, description="ExecutionGraph ID")
    execution_node_id: Optional[int] = Field(None, description="ExecutionNode ID")


class ScanIdsSchema(Schema):
    ids: List[int] = Field(..., description="ID 列表", min_length=1, max_length=10)


class URLScanIdsSchema(Schema):
    ids: List[int] = Field(..., description="URL ID 列表", min_length=1, max_length=5)


class SubBruteResultSchema(Schema):
    sub_id: int
    detail: str
    if_run: bool
    status_code: int


class FlaresolverrTriggerSchema(Schema):  # <--- 繼承 Schema
    url: str
    method: str
    seed_id: int | None = None
    target_id: int | None = None
    auto_create: bool = False
    execution_graph_id: int | None = Field(None, description="ExecutionGraph ID")
    execution_node_id: int | None = Field(None, description="ExecutionNode ID")
    body: str | None = Field(None, description="Raw request body (for POST/PUT)")
    content_type: str | None = Field(None, description="Content-Type override")
    host_header: str | None = Field(None, description="Override the Host header (vhost routing)")


class FlaresolverrResponse(Schema):  # <--- 繼承 Schema
    detail: str
    status_code: int
    if_run: bool


class AssetRef(Schema):
    id: int
    label: str


class PoCRecordOut(Schema):
    id: int
    vulnerability_id: int
    title: str
    content: str
    language: str
    result: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class PoCRecordCreate(Schema):
    title: str
    content: str
    language: str = "manual"  # curl|python|bash|http_request|manual
    result: Optional[str] = None
    is_verified: bool = False


class PoCRecordUpdate(Schema):
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    result: Optional[str] = None
    is_verified: Optional[bool] = None


class VulnerabilityOut(Schema):
    id: int
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    ip_asset: Optional[AssetRef] = None
    subdomain_asset: Optional[AssetRef] = None
    url_asset: Optional[AssetRef] = None
    source_attack_vector_id: Optional[int] = None
    overview_id: Optional[int] = None
    cve_intelligence_id: Optional[int] = None
    enrichment_status: str
    enrichment_attempted_at: Optional[datetime] = None
    tool_source: str
    template_id: str
    name: str
    severity: str
    matched_at: str
    extracted_results: Optional[Any] = None
    request_raw: Optional[str] = None
    response_raw: Optional[str] = None
    fingerprint: Optional[str] = None
    status: str
    description: Optional[str] = None
    remediation: Optional[str] = None
    pocs: List[PoCRecordOut] = []
    created_at: datetime
    updated_at: datetime
    last_seen: datetime


class VulnerabilityCreate(Schema):
    target_id: Optional[int] = None
    name: str
    severity: str  # info|low|medium|high|critical
    template_id: str = "manual"
    matched_at: str
    tool_source: str = "manual"
    description: Optional[str] = None
    remediation: Optional[str] = None
    extracted_results: Optional[Any] = None
    request_raw: Optional[str] = None
    response_raw: Optional[str] = None
    status: str = "unverified"
    ip_asset_id: Optional[int] = None
    subdomain_asset_id: Optional[int] = None
    url_asset_id: Optional[int] = None
    overview_id: Optional[int] = None
    cve_intelligence_id: Optional[int] = None


class VulnerabilityUpdate(Schema):
    target_id: Optional[int] = None
    name: Optional[str] = None
    severity: Optional[str] = None
    template_id: Optional[str] = None
    matched_at: Optional[str] = None
    description: Optional[str] = None
    remediation: Optional[str] = None
    extracted_results: Optional[Any] = None
    request_raw: Optional[str] = None
    response_raw: Optional[str] = None
    status: Optional[str] = None
    ip_asset_id: Optional[int] = None
    subdomain_asset_id: Optional[int] = None
    url_asset_id: Optional[int] = None
    overview_id: Optional[int] = None
    cve_intelligence_id: Optional[int] = None


class VulnerabilityStatusUpdate(Schema):
    status: str  # confirmed | false_positive | unverified


class VulnerabilityBatchStatusUpdate(Schema):
    ids: List[int]
    status: str


class VulnerabilityBatchDelete(Schema):
    ids: List[int]
