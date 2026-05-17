import argparse
import json
import os
import sys
import time
from typing import Any

import requests


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")
    import django  # noqa: WPS433

    django.setup()


def _parse_headers(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    try:
        obj = json.loads(value)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--headers must be JSON: {e}")
    if not isinstance(obj, dict):
        raise SystemExit("--headers must be a JSON object")
    out: dict[str, str] = {}
    for k, v in obj.items():
        out[str(k)] = str(v)
    return out


def _create_step(overview_id: int, description: str) -> int:
    _setup_django()
    from apps.core.models import Step  # noqa: WPS433
    from apps.core.models.analyze.Step import StepNote  # noqa: WPS433

    step = Step.create_next(overview_id=overview_id, status="WAITING_FOR_ASYNC")
    StepNote.objects.create(step=step, content=description)
    return step.id


def _poll_step(step_id: int, timeout_s: int = 90) -> None:
    _setup_django()
    from apps.core.models import Step, StepLog  # noqa: WPS433

    start = time.time()
    last_status = None
    while True:
        step = Step.objects.filter(id=step_id).select_related("note_detail").first()
        if not step:
            print(f"Step#{step_id} not found")
            return
        if step.status != last_status:
            print(f"Step#{step_id} status={step.status}")
            last_status = step.status

        if step.status in {"COMPLETED", "FAILED", "ENDED"}:
            break
        if time.time() - start > timeout_s:
            print(f"Timeout waiting for Step#{step_id}")
            break
        time.sleep(1.5)

    note = getattr(step, "note_detail", None)
    if note and note.content:
        print("\n=== StepNote (tail) ===")
        print(note.content[-2000:])

    logs = list(
        StepLog.objects.filter(step_id=step_id).order_by("-created_at")[:10].values(
            "created_at",
            "level",
            "tag",
            "action_status",
            "message",
        )
    )
    if logs:
        print("\n=== StepLogs (latest 10) ===")
        for row in reversed(logs):
            msg = row["message"]
            if isinstance(msg, str) and len(msg) > 600:
                msg = msg[:600] + "... [truncated]"
            print(
                f"{row['created_at']} [{row['level']}/{row['tag']}/{row['action_status']}] {msg}"
            )


def main() -> int:
    p = argparse.ArgumentParser(
        description="Test FlareSolverr send_request endpoint (POST + session + Step logging)."
    )
    p.add_argument("--api-base", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api"))
    p.add_argument("--url", required=True)
    p.add_argument("--method", default="GET")
    p.add_argument("--body", default=None)
    p.add_argument("--content-type", default=None)
    p.add_argument("--headers", default=None, help='JSON object, e.g. "{\\"X\\":\\"1\\"}"')
    p.add_argument("--cookies", default=None)
    p.add_argument("--session-key", default=None)
    p.add_argument("--refresh-session", action="store_true")
    p.add_argument("--target-id", type=int, default=None)
    p.add_argument("--seed-id", type=int, default=None)
    p.add_argument("--overview-id", type=int, default=None, help="If set and callback_step_id is omitted, create a Step")
    p.add_argument("--callback-step-id", type=int, default=None)
    p.add_argument("--poll", action="store_true", help="Poll Step status and print StepNote/StepLog")
    args = p.parse_args()

    if not args.target_id and not args.seed_id:
        raise SystemExit("You must provide --target-id or --seed-id to pass target gate")

    callback_step_id = args.callback_step_id
    if not callback_step_id and args.overview_id:
        callback_step_id = _create_step(
            args.overview_id,
            f"Test FlareSolverr request {args.method.upper()} {args.url}",
        )
        print(f"Created Step#{callback_step_id} (WAITING_FOR_ASYNC)")

    payload: dict[str, Any] = {
        "url": args.url,
        "method": args.method.upper(),
        "headers": _parse_headers(args.headers),
        "cookies": args.cookies,
        "body": args.body,
        "content_type": args.content_type,
        "session_key": args.session_key,
        "refresh_session": bool(args.refresh_session),
        "target_id": args.target_id,
        "seed_id": args.seed_id,
        "callback_step_id": callback_step_id,
    }

    endpoint = f"{args.api_base.rstrip('/')}/flaresolverr/send_request"
    print(f"POST {endpoint}")
    resp = requests.post(endpoint, json=payload, timeout=15)
    print(f"HTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=True))
    except Exception:
        print(resp.text)

    if args.poll and callback_step_id:
        _poll_step(callback_step_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
