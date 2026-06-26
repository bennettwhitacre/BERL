from berl.rate_limit import RateLimiter, get_limit


def test_tier_limits() -> None:
    assert get_limit("free", "list").per_second == 2
    assert get_limit("free", "list").per_hour == 500
    assert get_limit("gc", "mutation").per_second == 16
    assert get_limit("gc", "mutation").per_hour is None


def test_wait_sleeps_when_per_second_limit_hit() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    def sleeper(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = RateLimiter("free", clock=clock, sleeper=sleeper)
    limiter.wait("list")
    limiter.wait("list")
    limiter.wait("list")

    assert sleeps == [1.0]
