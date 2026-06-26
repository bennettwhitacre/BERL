from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Label, Static

from berl.bulk import recursive_delete_group


class DeleteGroupScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def __init__(self, group_id: str, name: str) -> None:
        super().__init__()
        self.group_id = group_id
        self.group_name = name
        self.armed = False

    def compose(self) -> ComposeResult:
        yield Label(f"Delete group: {self.group_name}")
        yield Checkbox("Recursive delete replays in this group and subgroups", id="recursive")
        with Horizontal(id="form-actions"):
            yield Button("Confirm", id="confirm", variant="error")
            yield Button("Cancel", id="cancel")
        yield Static("Click confirm once to arm deletion, then click again to execute.", id="delete-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        if not self.armed:
            self.armed = True
            self.query_one("#delete-status", Static).update("Deletion armed. Click Confirm again to permanently delete.")
            return
        try:
            if self.query_one("#recursive", Checkbox).value:
                recursive_delete_group(self.app.require_client(), self.group_id)
            else:
                self.app.require_client().delete_group(self.group_id)
            self.app.pop_screen()
            self.app.screen.reload()
        except Exception as exc:  # noqa: BLE001
            self.query_one("#delete-status", Static).update(str(exc))


class DeleteReplayScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def __init__(self, replay_id: str, title: str) -> None:
        super().__init__()
        self.replay_id = replay_id
        self.title = title
        self.armed = False

    def compose(self) -> ComposeResult:
        yield Label(f"Delete replay: {self.title}")
        with Horizontal(id="form-actions"):
            yield Button("Confirm", id="confirm", variant="error")
            yield Button("Cancel", id="cancel")
        yield Static("Click confirm once to arm deletion, then click again to execute.", id="delete-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        if not self.armed:
            self.armed = True
            self.query_one("#delete-status", Static).update("Deletion armed. Click Confirm again to permanently delete.")
            return
        try:
            self.app.require_client().delete_replay(self.replay_id)
            self.app.pop_screen()
            self.app.screen.reload()
        except Exception as exc:  # noqa: BLE001
            self.query_one("#delete-status", Static).update(str(exc))
