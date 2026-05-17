import json
from typing import Any, Optional

from django.utils import timezone


def log_http_exchange(
    *,
    step_id: Optional[int],
    tool: str,
    request: dict[str, Any],
    response: dict[str, Any],
    level: str = "INFO",
) -> None:
    """Hook: persist HTTP request/response for a step.

    This is intentionally generic so other tools can reuse it.
    """

    if not step_id:
        return

    from apps.core.models import StepLog
    from apps.core.models.analyze.Step import StepNote

    # Keep StepLog structured-ish but readable.
    payload = {
        "ts": timezone.now().isoformat(),
        "tool": tool,
        "request": request,
        "response": {
            "status_code": response.get("status_code"),
            "response_url": response.get("response_url"),
            "headers": response.get("response_headers"),
            # Do not dump megabytes into DB logs.
            "body_preview": (response.get("response_text") or "")[:2000],
        },
    }

    StepLog.objects.create(
        step_id=step_id,
        level=level,
        tag="API_CALL",
        message=json.dumps(payload, ensure_ascii=True, default=str),
        action_status="SUCCESS" if (response.get("status_code") or 0) < 400 else "FAILED",
    )

    # Human-friendly StepNote append.
    note_line = (
        f"\n\n[HTTP:{tool}] {request.get('method')} {request.get('url')} -> {response.get('status_code')}\n"
        f"Request headers: {request.get('headers')}\n"
        f"Request body preview: {(request.get('body') or '')[:500]}\n"
        f"Response url: {response.get('response_url')}\n"
        f"Response body preview: {(response.get('response_text') or '')[:800]}"
    )
    # Append instead of overwrite.
    note_obj, created = StepNote.objects.get_or_create(step_id=step_id, defaults={"content": ""})
    note_obj.content = (note_obj.content or "") + note_line
    note_obj.save(update_fields=["content"])
