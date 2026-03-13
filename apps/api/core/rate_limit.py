from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class RateLimitConfig:
    max_attempts: int
    window_seconds: int


class InMemoryRateLimiter:
    """Simple process-local sliding-window rate limiter.

    This is intentionally lightweight for API edge-protection in single-instance
    deployments and local development.
    """

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, config: RateLimitConfig) -> bool:
        now = monotonic()
        window_start = now - config.window_seconds

        with self._lock:
            attempts = self._events[key]

            while attempts and attempts[0] < window_start:
                attempts.popleft()

            if len(attempts) >= config.max_attempts:
                return False

            attempts.append(now)
            return True


rate_limiter = InMemoryRateLimiter()
