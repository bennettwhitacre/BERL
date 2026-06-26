from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from berl.bulk import execute_upload


class UploadScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def compose(self) -> ComposeResult:
        defaults = self.app.config.upload_defaults
        yield Label("Upload into current path")
        yield Input(placeholder="Directory path", id="directory")
        yield Select(
            [("public", "public"), ("unlisted", "unlisted"), ("private", "private")],
            value=defaults.visibility,
            id="visibility",
        )
        yield Select(
            [("by-id", "by-id"), ("by-name", "by-name")],
            value=defaults.player_identification,
            id="player-identification",
        )
        yield Select(
            [("by-distinct-players", "by-distinct-players"), ("by-player-clusters", "by-player-clusters")],
            value=defaults.team_identification,
            id="team-identification",
        )
        yield Checkbox("Shared groups", value=defaults.shared, id="shared")
        with Horizontal(id="form-actions"):
            yield Button("Execute upload", id="execute", variant="success")
            yield Button("Cancel", id="cancel")
        yield Static("", id="upload-status", classes="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        if event.button.id != "execute":
            return

        status = self.query_one("#upload-status", Static)
        directory = Path(self.query_one("#directory", Input).value.strip())
        if not directory.is_dir():
            status.update("Directory does not exist.")
            return

        defaults = self.app.config.upload_defaults
        defaults.visibility = str(self.query_one("#visibility", Select).value)
        defaults.player_identification = str(self.query_one("#player-identification", Select).value)
        defaults.team_identification = str(self.query_one("#team-identification", Select).value)
        defaults.shared = self.query_one("#shared", Checkbox).value
        self.app.save()

        status.update("Uploading...")
        try:
            result = execute_upload(
                self.app.require_client(),
                directory,
                current_group_id=self.app.state.group_id,
                defaults=defaults,
            )
        except Exception as exc:  # noqa: BLE001
            status.update(str(exc))
            return

        self.app.pop_screen()
        self.app.screen.reload()
        self.app.screen.query_one("#status", Static).update(
            f"Upload done: {len(result.created_groups)} groups, "
            f"{len(result.uploaded_replays)} replays, {len(result.failures)} failures"
        )
