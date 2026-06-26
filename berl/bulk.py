from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from berl.api import BallchasingClient
from berl.config import UploadDefaults


@dataclass(frozen=True, slots=True)
class UploadPlan:
    root: Path
    folders: tuple[Path, ...]
    replays: tuple[Path, ...]


@dataclass(slots=True)
class BulkResult:
    created_groups: list[str] = field(default_factory=list)
    uploaded_replays: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def plan_upload(root: Path) -> UploadPlan:
    root = root.resolve()
    folders: list[Path] = []
    replays: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            folders.append(path)
        elif path.is_file() and path.suffix.lower() == ".replay":
            replays.append(path)
    return UploadPlan(root=root, folders=tuple(folders), replays=tuple(replays))


def execute_upload(
    client: BallchasingClient,
    root: Path,
    *,
    current_group_id: str | None,
    defaults: UploadDefaults,
) -> BulkResult:
    plan = plan_upload(root)
    result = BulkResult()
    group_by_folder: dict[Path, str | None] = {plan.root: current_group_id}

    for folder in plan.folders:
        parent_id = group_by_folder.get(folder.parent, current_group_id)
        try:
            created = client.create_group(
                folder.name,
                parent=parent_id,
                player_identification=defaults.player_identification,
                team_identification=defaults.team_identification,
            )
            group_id = created["id"]
            group_by_folder[folder] = group_id
            result.created_groups.append(group_id)
            if defaults.shared:
                client.patch_group(group_id, {"shared": True})
        except Exception as exc:  # noqa: BLE001 - failures are collected for the progress screen.
            group_by_folder[folder] = parent_id
            result.failures.append(f"{folder}: {exc}")

    for replay in plan.replays:
        group_id = group_by_folder.get(replay.parent, current_group_id)
        try:
            uploaded = client.upload_replay(replay, visibility=defaults.visibility, group=group_id)
            replay_id = uploaded["id"]
            if uploaded.get("_duplicate"):
                result.duplicates.append(replay_id)
            else:
                result.uploaded_replays.append(replay_id)
        except Exception as exc:  # noqa: BLE001
            result.failures.append(f"{replay}: {exc}")

    return result


def collect_recursive_replay_ids(client: BallchasingClient, group_id: str) -> list[str]:
    replay_ids: list[str] = []
    groups_to_visit = [group_id]
    visited: set[str] = set()

    while groups_to_visit:
        current = groups_to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        replays = client.list_replays(group=current, count=200).get("list", [])
        replay_ids.extend(replay["id"] for replay in replays if replay.get("id"))

        groups = client.list_groups(group=current, count=200).get("list", [])
        groups_to_visit.extend(group["id"] for group in groups if group.get("id"))

    return replay_ids


def recursive_delete_group(client: BallchasingClient, group_id: str) -> None:
    for replay_id in collect_recursive_replay_ids(client, group_id):
        client.delete_replay(replay_id)
    client.delete_group(group_id)
