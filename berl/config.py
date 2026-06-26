from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(".berl")
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass(slots=True)
class UploadDefaults:
    visibility: str = "public"
    player_identification: str = "by-id"
    team_identification: str = "by-distinct-players"
    shared: bool = False


@dataclass(slots=True)
class AppConfig:
    api_token: str = ""
    subscription_tier: str = "free"
    upload_defaults: UploadDefaults = field(default_factory=UploadDefaults)


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()

    data = json.loads(path.read_text(encoding="utf-8"))
    defaults = data.get("upload_defaults") or {}
    return AppConfig(
        api_token=str(data.get("api_token") or ""),
        subscription_tier=str(data.get("subscription_tier") or "free"),
        upload_defaults=UploadDefaults(
            visibility=str(defaults.get("visibility") or "public"),
            player_identification=str(defaults.get("player_identification") or "by-id"),
            team_identification=str(defaults.get("team_identification") or "by-distinct-players"),
            shared=bool(defaults.get("shared", False)),
        ),
    )


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = asdict(config)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
