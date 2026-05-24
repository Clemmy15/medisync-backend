"""In-memory sliding-window rate limiter (per IP + route group)."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _Bucket:
    timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """
    Thread-safe in-memory rate limiter.

    For multi-worker production, replace with Redis (e.g. slowapi + redis backend).
    """

    def __init__(self) -> None:
        self._buckets: dict[str, _Bucket] = defaultdict(_Bucket)
        self._lock = Lock()

    def is_allowed(self, key: str, *, limit: int, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets[key]
            bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]
            if len(bucket.timestamps) >= limit:
                return False
            bucket.timestamps.append(now)
            return True

    def remaining(self, key: str, *, limit: int, window_seconds: int = 60) -> int:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets[key]
            active = [t for t in bucket.timestamps if t > cutoff]
            return max(0, limit - len(active))


_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter
