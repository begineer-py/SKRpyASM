from ninja import Schema, Field
from typing import Optional


class KatanaScanSchema(Schema):
    name: str = Field(..., description="目標子域名字串 (e.g. 'example.com')")
    subdomain_id: Optional[int] = Field(None, description="子域名 ID (優先使用)")
    depth: int = Field(3, description="爬取深度 (預設 3)")
    js_crawl: bool = Field(True, description="是否解析 JS 中的 URL (預設 True)")
    callback_step_id: Optional[int] = Field(None, description="回調用的 Step ID")
    execution_graph_id: Optional[int] = Field(None, description="ExecutionGraph ID for async lifecycle tracking")
    execution_node_id: Optional[int] = Field(None, description="ExecutionNode ID for async lifecycle tracking")


class KatanaScanSuccessSchema(Schema):
    name: str
    if_run: bool
