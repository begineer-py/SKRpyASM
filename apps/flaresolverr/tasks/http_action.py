import logging
import os
from urllib.parse import urlparse

from celery import shared_task

from c2_core.config.logging import log_function_call
from apps.flaresolverr.session_store import FlareSolverrSessionStore
from apps.flaresolverr.hooks import log_http_exchange
from apps.core.header_injection import get_tagged_headers
from apps.flaresolverr.spider_utils.send_flaresolverr import (
    call_flaresolverr_api,
    create_flaresolverr_session,
    destroy_flaresolverr_session,
)


logger = logging.getLogger(__name__)


def _session_key_default(url: str) -> str:
    # Default to hostname to maximize reuse without cross-domain mixing.
    host = urlparse(url).hostname or "unknown"
    return f"host:{host}"


@shared_task(bind=True)
@log_function_call()
def perform_flaresolverr_request(
    self,
    *,
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    cookies: str = "",
    body: str | None = None,
    content_type: str | None = None,
    host_header: str | None = None,
    session_key: str | None = None,
    refresh_session: bool = False,
    callback_step_id: int | None = None,
    execution_graph_id: int | None = None,
    execution_node_id: int | None = None,
):
    """Send a single HTTP request via FlareSolverr, with optional session reuse.

    We persist request/response via hook for traceability.
    """
    try:
        flaresolverr_url = os.getenv("FLARESOLVERR_URL") or "http://127.0.0.1:8191"
        store = FlareSolverrSessionStore()

        headers = headers or {}
        session_key = session_key or _session_key_default(url)

        session_id = None
        if refresh_session:
            existing = store.get(session_key)
            if existing:
                destroy_flaresolverr_session(flaresolverr_url=flaresolverr_url, session=existing.session_id)
                store.delete(session_key)

        existing = store.get(session_key)
        if existing:
            session_id = existing.session_id
        else:
            session_id = create_flaresolverr_session(flaresolverr_url=flaresolverr_url)
            if session_id:
                store.set(session_key, session_id)

        # Execute request.
        tagged_headers = get_tagged_headers(headers)
        response = call_flaresolverr_api(
            url,
            method,
            tagged_headers,
            cookies or "",
            flaresolverr_url,
            1,
            body=body,
            content_type=content_type,
            host_header=host_header,
            session=session_id,
        )

        # call_flaresolverr_api returns a translated dict.
        if response is None:
            response = {
                "status_code": 0,
                "response_text": "",
                "response_headers": {},
                "response_url": url,
            }

        log_http_exchange(
            step_id=callback_step_id,
            execution_graph_id=execution_graph_id,
            execution_node_id=execution_node_id,
            tool="flaresolverr",
            request={
                "url": url,
                "method": method.upper(),
                "headers": headers,
                "cookies": cookies,
                "body": body,
                "content_type": content_type,
                "host_header": host_header,
                "session_key": session_key,
                "session_id": session_id,
            },
            response=response,
            level="INFO",
        )

        result = {
            "ok": True,
            "status_code": response.get("status_code"),
            "response_url": response.get("response_url"),
        }
        _complete_execution_node(execution_node_id, content=f"FlareSolverr request 完成: {url}", output=result)
        return result
    except Exception as exc:
        _fail_execution_node(
            execution_node_id,
            content=f"FlareSolverr request 失敗: {url}: {exc}",
            error={"error_type": type(exc).__name__, "message": str(exc)},
        )
        raise


def _complete_execution_node(execution_node_id: int | None, *, content: str, output: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.complete_node_by_id(execution_node_id, output=output, content=content)


def _fail_execution_node(execution_node_id: int | None, *, content: str, error: dict | None = None) -> None:
    if not execution_node_id:
        return
    from apps.core.services import ExecutionService

    ExecutionService.fail_node_by_id(execution_node_id, content=content, error=error)
