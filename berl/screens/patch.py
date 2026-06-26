from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static


class PatchGroupScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def __init__(self, group_id: str) -> None:
        super().__init__()
        self.group_id = group_id
        self.original: dict[str, object] = {}

    def compose(self) -> ComposeResult:
        yield Label(f"Patch group {self.group_id}")
        yield Select([("by-id", "by-id"), ("by-name", "by-name")], id="player-identification")
        yield Select(
            [("by-distinct-players", "by-distinct-players"), ("by-player-clusters", "by-player-clusters")],
            id="team-identification",
        )
        yield Input(placeholder="Parent group id, blank for unchanged", id="parent")
        yield Checkbox("Shared", id="shared")
        with Horizontal(id="form-actions"):
            yield Button("Save", id="save", variant="primary")
            yield Button("Cancel", id="cancel")
        yield Static("", id="patch-status", classes="status")

    def on_mount(self) -> None:
        status = self.query_one("#patch-status", Static)
        try:
            self.original = self.app.require_client().get_group(self.group_id)
            self.query_one("#player-identification", Select).value = self.original.get("player_identification", "by-id")
            self.query_one("#team-identification", Select).value = self.original.get(
                "team_identification", "by-distinct-players"
            )
            self.query_one("#shared", Checkbox).value = bool(self.original.get("shared", False))
        except Exception as exc:  # noqa: BLE001
            status.update(str(exc))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        fields = {
            "player_identification": str(self.query_one("#player-identification", Select).value),
            "team_identification": str(self.query_one("#team-identification", Select).value),
            "shared": self.query_one("#shared", Checkbox).value,
        }
        parent = self.query_one("#parent", Input).value.strip()
        if parent:
            fields["parent"] = parent
        changed = {key: value for key, value in fields.items() if self.original.get(key) != value}
        try:
            if changed:
                self.app.require_client().patch_group(self.group_id, changed)
            self.app.pop_screen()
            self.app.screen.reload()
        except Exception as exc:  # noqa: BLE001
            self.query_one("#patch-status", Static).update(str(exc))


class PatchReplayScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def __init__(self, replay_id: str) -> None:
        super().__init__()
        self.replay_id = replay_id
        self.original: dict[str, object] = {}

    def compose(self) -> ComposeResult:
        yield Label(f"Patch replay {self.replay_id}")
        yield Input(placeholder="Title", id="title")
        yield Select([("public", "public"), ("unlisted", "unlisted"), ("private", "private")], id="visibility")
        yield Input(placeholder="Group id, blank to unassign", id="group")
        with Horizontal(id="form-actions"):
            yield Button("Save", id="save", variant="primary")
            yield Button("Cancel", id="cancel")
        yield Static("", id="patch-status", classes="status")

    def on_mount(self) -> None:
        status = self.query_one("#patch-status", Static)
        try:
            self.original = self.app.require_client().get_replay(self.replay_id)
            self.query_one("#title", Input).value = str(
                self.original.get("replay_title") or self.original.get("title") or ""
            )
            self.query_one("#visibility", Select).value = self.original.get("visibility", "public")
            groups = self.original.get("groups") or []
            if groups:
                self.query_one("#group", Input).value = str(groups[0].get("id", ""))
        except Exception as exc:  # noqa: BLE001
            status.update(str(exc))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        fields = {
            "title": self.query_one("#title", Input).value.strip(),
            "visibility": str(self.query_one("#visibility", Select).value),
            "group": self.query_one("#group", Input).value.strip(),
        }
        original_title = self.original.get("replay_title") or self.original.get("title") or ""
        original_group = ""
        groups = self.original.get("groups") or []
        if groups:
            original_group = str(groups[0].get("id", ""))
        changed = {}
        if fields["title"] != original_title:
            changed["title"] = fields["title"]
        if fields["visibility"] != self.original.get("visibility"):
            changed["visibility"] = fields["visibility"]
        if fields["group"] != original_group:
            changed["group"] = fields["group"]
        try:
            if changed:
                self.app.require_client().patch_replay(self.replay_id, changed)
            self.app.pop_screen()
            self.app.screen.reload()
        except Exception as exc:  # noqa: BLE001
            self.query_one("#patch-status", Static).update(str(exc))
