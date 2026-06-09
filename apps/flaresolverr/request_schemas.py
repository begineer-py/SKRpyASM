from ninja import Schema, Field
from typing import Optional, Dict


class FlareSolverrSendRequestSchema(Schema):
    url: str
    method: str = Field("GET", description="HTTP method, e.g. GET/POST")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Request headers")
    cookies: Optional[str] = Field(default=None, description="Cookie string k=v; k2=v2")
    body: Optional[str] = Field(default=None, description="Raw request body")
    content_type: Optional[str] = Field(default=None, description="Content-Type override")
    host_header: Optional[str] = Field(default=None, description="Override the Host header (for vhost routing)")
    session_key: Optional[str] = Field(
        default=None,
        description="Logical session key. If set, the system will reuse a FlareSolverr browser session.",
    )
    refresh_session: bool = Field(
        default=False,
        description="Force create a new FlareSolverr session for this session_key.",
    )
    target_id: int | None = None
    seed_id: int | None = None
    callback_step_id: int | None = Field(None, description="Step ID for async callback/logging")
    execution_graph_id: int | None = Field(None, description="ExecutionGraph ID for async lifecycle tracking")
    execution_node_id: int | None = Field(None, description="ExecutionNode ID for async lifecycle tracking")


class FlareSolverrSendRequestResponse(Schema):
    detail: str
    status_code: int
    if_run: bool
