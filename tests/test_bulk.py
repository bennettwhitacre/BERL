from pathlib import Path
from typing import Any

from berl.bulk import collect_recursive_replay_ids, execute_upload, plan_upload, recursive_delete_group
from berl.config import UploadDefaults


class FakeClient:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.uploaded: list[dict[str, Any]] = []
        self.patched_groups: list[tuple[str, dict[str, Any]]] = []
        self.deleted_replays: list[str] = []
        self.deleted_groups: list[str] = []
        self.group_lists: dict[str, list[dict[str, str]]] = {}
        self.replay_lists: dict[str, list[dict[str, str]]] = {}

    def create_group(self, name: str, **kwargs: Any) -> dict[str, str]:
        group_id = f"group-{len(self.created) + 1}"
        self.created.append({"name": name, **kwargs, "id": group_id})
        return {"id": group_id}

    def patch_group(self, group_id: str, fields: dict[str, Any]) -> None:
        self.patched_groups.append((group_id, fields))

    def upload_replay(self, path: Path, **kwargs: Any) -> dict[str, str]:
        replay_id = f"replay-{len(self.uploaded) + 1}"
        self.uploaded.append({"path": path, **kwargs, "id": replay_id})
        return {"id": replay_id}

    def list_replays(self, group: str, count: int) -> dict[str, Any]:
        return {"list": self.replay_lists.get(group, [])}

    def list_groups(self, group: str, count: int) -> dict[str, Any]:
        return {"list": self.group_lists.get(group, [])}

    def delete_replay(self, replay_id: str) -> None:
        self.deleted_replays.append(replay_id)

    def delete_group(self, group_id: str) -> None:
        self.deleted_groups.append(group_id)


def test_plan_upload_collects_folders_and_replays(tmp_path: Path) -> None:
    (tmp_path / "series").mkdir()
    (tmp_path / "series" / "game.replay").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("skip", encoding="utf-8")

    plan = plan_upload(tmp_path)

    assert plan.folders == ((tmp_path / "series").resolve(),)
    assert plan.replays == ((tmp_path / "series" / "game.replay").resolve(),)


def test_execute_upload_creates_groups_and_uploads_to_created_group(tmp_path: Path) -> None:
    folder = tmp_path / "series"
    folder.mkdir()
    replay = folder / "game.replay"
    replay.write_bytes(b"")
    client = FakeClient()

    result = execute_upload(
        client,  # type: ignore[arg-type]
        tmp_path,
        current_group_id="root",
        defaults=UploadDefaults(shared=True),
    )

    assert client.created[0]["name"] == "series"
    assert client.created[0]["parent"] == "root"
    assert client.patched_groups == [("group-1", {"shared": True})]
    assert client.uploaded[0]["path"] == replay.resolve()
    assert client.uploaded[0]["group"] == "group-1"
    assert result.failures == []


def test_recursive_delete_deletes_replays_before_selected_group() -> None:
    client = FakeClient()
    client.replay_lists = {"root": [{"id": "r1"}], "child": [{"id": "r2"}]}
    client.group_lists = {"root": [{"id": "child"}], "child": []}

    recursive_delete_group(client, "root")  # type: ignore[arg-type]

    assert client.deleted_replays == ["r1", "r2"]
    assert client.deleted_groups == ["root"]


def test_collect_recursive_replay_ids() -> None:
    client = FakeClient()
    client.replay_lists = {"root": [{"id": "r1"}]}
    client.group_lists = {"root": []}

    assert collect_recursive_replay_ids(client, "root") == ["r1"]  # type: ignore[arg-type]
