from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable


Tier = str
Bucket = str


@dataclass(frozen=True, slots=True)
class Limit:
    per_second: int
    per_hour: int | None = None


LIST_LIMITS: dict[Tier, Limit] = {
    "free": Limit(2, 500),
    "gold": Limit(2, 1000),
    "diamond": Limit(4, 2000),
    "champion": Limit(8, None),
    "gc": Limit(16, None),
}

MUTATION_LIMITS: dict[Tier, Limit] = {
    "free": Limit(2, 1000),
    "gold": Limit(2, 2000),
    "diamond": Limit(4, 5000),
    "champion": Limit(8, None),
    "gc": Limit(16, None),
}


def normalize_tier(tier: str) -> Tier:
    normalized = tier.strip().lower().replace(" ", "-")
    aliases = {
        "all-others": "free",
        "gc-patrons": "gc",
        "champion-patrons": "champion",
        "diamond-patrons": "diamond",
        "gold-patrons": "gold",
    }
    return aliases.get(normalized, normalized if normalized in LIST_LIMITS else "free")


def get_limit(tier: str, bucket: Bucket) -> Limit:
    limits = LIST_LIMITS if bucket == "list" else MUTATION_LIMITS
    return limits[normalize_tier(tier)]


@dataclass
class RateLimiter:
    tier: str = "free"
    clock: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep
    _events: dict[Bucket, list[float]] = field(default_factory=lambda: {"list": [], "mutation": []})

    def wait(self, bucket: Bucket) -> None:
        limit = get_limit(self.tier, bucket)
        now = self.clock()
        events = [event for event in self._events.setdefault(bucket, []) if now - event < 3600]

        recent = [event for event in events if now - event < 1]
        if len(recent) >= limit.per_second:
            delay = 1 - (now - recent[0])
            if delay > 0:
                self.sleeper(delay)
                now = self.clock()
                events = [event for event in events if now - event < 3600]

        if limit.per_hour is not None and len(events) >= limit.per_hour:
            delay = 3600 - (now - events[0])
            if delay > 0:
                self.sleeper(delay)
                now = self.clock()
                events = [event for event in events if now - event < 3600]

        events.append(now)
        self._events[bucket] = events
