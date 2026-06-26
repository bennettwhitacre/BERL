from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ExplorerState:
    group_id: str | None = None
    path: tuple[tuple[str, str], ...] = ()
    group_filters: dict[str, Any] = field(default_factory=dict)
    replay_filters: dict[str, Any] = field(default_factory=dict)
    group_sort_by: str = "created"
    group_sort_dir: str = "desc"
    replay_sort_by: str = "upload-date"
    replay_sort_dir: str = "desc"
    direct_replays_only: bool = True

    @property
    def display_path(self) -> str:
        if not self.path:
            return "Home"
        return "Home / " + " / ".join(name for _, name in self.path)
