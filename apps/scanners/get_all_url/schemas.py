from ninja import Schema, Field
from typing import Optional
from typing_extensions import Literal


class ScanAllUrlSchema(Schema):
    # 雖然 URL 有 target_id，但如果你的前端習慣在 body 帶 id，這裡保留沒問題
    # 但邏輯上我們會優先使用 URL path 中的 target_identifier 來確保權限隔離
    name: str = Field(..., description="目標子域名或 URL 的字串名稱 (不可傳 ID)")
    subdomain_id: Optional[int] = Field(None, description="子域名 ID (優先使用)")
    scan_type: Optional[Literal["passive", "initiative"]] = None
    callback_step_id: Optional[int] = Field(None, description="回調用的 Step ID (必填，來自 create_step)")
    execution_graph_id: Optional[int] = Field(None, description="ExecutionGraph ID for async lifecycle tracking")
    execution_node_id: Optional[int] = Field(None, description="ExecutionNode ID for async lifecycle tracking")


class SuccessScanAllUrlSchema(Schema):
    name: str
    if_run: bool
