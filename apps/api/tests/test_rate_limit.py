from core.rate_limit import InMemoryRateLimiter, RateLimitConfig


def test_rate_limiter_allows_within_window():
    limiter = InMemoryRateLimiter()
    config = RateLimitConfig(max_attempts=2, window_seconds=60)

    assert limiter.allow("client:login", config)
    assert limiter.allow("client:login", config)


def test_rate_limiter_blocks_after_threshold():
    limiter = InMemoryRateLimiter()
    config = RateLimitConfig(max_attempts=1, window_seconds=60)

    assert limiter.allow("client:register", config)
    assert not limiter.allow("client:register", config)
