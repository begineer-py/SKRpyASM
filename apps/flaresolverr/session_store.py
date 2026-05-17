import os
import logging
from dataclasses import dataclass
from typing import Optional

import redis
from django.conf import settings


logger = logging.getLogger(__name__)


def _redis_url() -> str:
    # Prefer explicit env; fall back to Celery broker.
    url = os.getenv("REDIS_URL")
    if url:
        return url
    broker = getattr(settings, "CELERY_BROKER_URL", "")
    return broker if broker.startswith("redis://") else "redis://localhost:6379/0"


@dataclass(frozen=True)
class FlareSolverrSession:
    session_id: str


class FlareSolverrSessionStore:
    """Tiny Redis-backed store for FlareSolverr session ids.

    We keep only a session id and refresh TTL on access.
    """

    def __init__(self, namespace: str = "fs", ttl_seconds: int = 50):
        self._namespace = namespace
        self._ttl = int(ttl_seconds)
        self._r = redis.Redis.from_url(_redis_url(), decode_responses=True)

    def _key(self, session_key: str) -> str:
        return f"{self._namespace}:session:{session_key}"

    def get(self, session_key: str) -> Optional[FlareSolverrSession]:
        try:
            sid = self._r.get(self._key(session_key))
            if not sid:
                return None
            # Refresh TTL on access.
            self._r.expire(self._key(session_key), self._ttl)
            return FlareSolverrSession(session_id=sid)
        except Exception as e:
            logger.warning(f"Failed to read session from redis: {e}")
            return None

    def set(self, session_key: str, session_id: str) -> None:
        try:
            self._r.set(self._key(session_key), session_id, ex=self._ttl)
        except Exception as e:
            logger.warning(f"Failed to write session to redis: {e}")

    def delete(self, session_key: str) -> None:
        try:
            self._r.delete(self._key(session_key))
        except Exception as e:
            logger.warning(f"Failed to delete session from redis: {e}")
