"""In-memory per-key sliding-window rate limiter, applied to the AI
endpoints (summarize/research) — matches the original app's
`express-rate-limit` config (windowMs: 60000, max: 30) exactly. Ported
verbatim from chat.folding-os.com/backend/app/core/security.py's
SlidingWindowLimiter, which is already general-purpose and dependency-free.
"""

import time

from fastapi import HTTPException, Request, status

from app.core.config import settings


class SlidingWindowLimiter:
    """Single-host app, so an in-memory limiter is sufficient; state is not
    shared across workers — acceptable here.
    """

    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, now: float | None = None) -> bool:
        ts = time.monotonic() if now is None else now
        window_start = ts - self.window
        hits = [t for t in self._hits.get(key, []) if t > window_start]
        if len(hits) >= self.limit:
            self._hits[key] = hits
            return False
        hits.append(ts)
        self._hits[key] = hits
        return True


_ai_limiter = SlidingWindowLimiter(limit=settings.ai_rate_limit_per_minute, window_seconds=60.0)


def _client_ip(request: Request) -> str:
    """Best-effort client address for rate limiting. The backend always
    sits behind the frontend's nginx (same as every sibling app), which sets
    X-Forwarded-For — request.client.host would otherwise always be the
    nginx container's own address, not the real client's.
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_ai_rate_limit(request: Request) -> None:
    if not _ai_limiter.allow(_client_ip(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many AI requests; retry in a minute")
