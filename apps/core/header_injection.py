from dataclasses import dataclass
from typing import Optional


_RATE_LIMIT_DEFAULTS = {"rps": 10, "max_concurrency": 5, "timeout": 15}


@dataclass
class ResolvedRequestConfig:
    enabled: bool
    username: str
    header_prefix: str
    custom_headers: dict
    rps: Optional[int]
    max_concurrency: Optional[int]
    timeout: Optional[int]


def resolve_request_config(target_id: Optional[int] = None) -> ResolvedRequestConfig:
    from .models.pentest_config import PentestHeaderConfig

    global_cfg = PentestHeaderConfig.get_config()
    base = ResolvedRequestConfig(
        enabled=global_cfg.enabled,
        username=global_cfg.username,
        header_prefix=global_cfg.header_prefix,
        custom_headers={},
        rps=None,
        max_concurrency=None,
        timeout=None,
    )

    if target_id is None:
        return base

    from .models.target_request_config import TargetRequestConfig

    try:
        tc = TargetRequestConfig.objects.get(target_id=target_id)
    except TargetRequestConfig.DoesNotExist:
        return base

    return ResolvedRequestConfig(
        enabled=tc.header_enabled if tc.header_enabled is not None else global_cfg.enabled,
        username=tc.header_username if tc.header_username else global_cfg.username,
        header_prefix=tc.header_prefix if tc.header_prefix else global_cfg.header_prefix,
        custom_headers=tc.custom_headers or {},
        rps=tc.rps,
        max_concurrency=tc.max_concurrency,
        timeout=tc.timeout,
    )


def get_tagged_headers(
    original_headers: Optional[dict] = None,
    target_id: Optional[int] = None,
) -> dict:
    config = resolve_request_config(target_id)
    if not config.enabled:
        return original_headers or {}

    headers = dict(original_headers or {})
    prefix = config.header_prefix
    username = config.username

    original_ua = headers.pop("User-Agent", None) or headers.pop("user-agent", None)
    ua_suffix = f" - {original_ua}" if original_ua else ""
    headers["User-Agent"] = f"{prefix} - {username}{ua_suffix}"
    headers[f"X-{prefix}-Username"] = username

    if config.custom_headers:
        headers.update(config.custom_headers)

    return headers


def build_rate_limit_args(tool: str, target_id: Optional[int] = None) -> list[str]:
    cfg = resolve_request_config(target_id)

    rps = cfg.rps if cfg.rps is not None else _RATE_LIMIT_DEFAULTS["rps"]
    mc = cfg.max_concurrency if cfg.max_concurrency is not None else _RATE_LIMIT_DEFAULTS["max_concurrency"]
    to = cfg.timeout if cfg.timeout is not None else _RATE_LIMIT_DEFAULTS["timeout"]

    if cfg.rps is None and cfg.max_concurrency is None and cfg.timeout is None:
        return []

    args: list[str] = []

    if tool == "nuclei":
        args.extend(["-rl", str(rps)])
    elif tool == "ffuf":
        args.extend(["-rate", str(rps)])
        args.extend(["-t", str(mc)])
    elif tool == "httpx":
        args.extend(["-rate-limit", str(rps)])
        args.extend(["-threads", str(mc)])
        args.extend(["-timeout", str(to)])

    return args
