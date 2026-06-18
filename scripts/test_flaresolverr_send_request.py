import argparse
import json
import os
from typing import Any

import requests


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


def main() -> int:
    p = argparse.ArgumentParser(
        description="Test FlareSolverr send_request endpoint."
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
    args = p.parse_args()

    if not args.target_id and not args.seed_id:
        raise SystemExit("You must provide --target-id or --seed-id to pass target gate")

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
    }

    endpoint = f"{args.api_base.rstrip('/')}/flaresolverr/send_request"
    print(f"POST {endpoint}")
    resp = requests.post(endpoint, json=payload, timeout=15)
    print(f"HTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=True))
    except Exception:
        print(resp.text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
