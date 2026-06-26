from __future__ import annotations

from dataclasses import replace
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Select, Static

from berl.models import ExplorerState
from berl.screens.delete import DeleteGroupScreen, DeleteReplayScreen
from berl.screens.filters import GroupFilterScreen, ReplayFilterScreen
from berl.screens.patch import PatchGroupScreen, PatchReplayScreen
from berl.screens.token import TokenScreen
from berl.screens.upload import UploadScreen


class ExplorerScreen(Screen[None]):
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("h", "home", "Home"),
        ("backspace", "up", "Up"),
        ("enter", "open_group", "Open group"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Button("<", id="back")
            yield Button(">", id="forward")
            yield Button("Up", id="up")
            yield Button("Refresh", id="refresh")
            yield Button("Home", id="home")
            yield Label("Home", id="path")
            yield Select(
                [
                    ("Free", "free"),
                    ("Gold", "gold"),
                    ("Diamond", "diamond"),
                    ("Champion", "champion"),
                    ("GC", "gc"),
                ],
                value=self.app.config.subscription_tier,
                id="tier",
            )
            yield Button("API token", id="api-token")
        with Horizontal(id="action-bar"):
            yield Button("Upload here", id="upload", variant="success")
            yield Button("Group filters", id="group-filters")
            yield Button("Replay filters", id="replay-filters")
        with Container(id="main-columns"):
            with Vertical(classes="column"):
                yield Label("Groups")
                yield DataTable(id="groups")
                with Horizontal():
                    yield Button("Open group", id="open-group", variant="primary")
                    yield Button("Patch group", id="patch-group")
                    yield Button("Delete group", id="delete-group", variant="error")
            with Vertical(classes="column"):
                yield Label("Replays")
                yield DataTable(id="replays")
                with Horizontal():
                    yield Button("Patch replay", id="patch-replay")
                    yield Button("Delete replay", id="delete-replay", variant="error")
        yield Static("", id="status", classes="status")
        yield Footer()

    def on_mount(self) -> None:
        self.groups: list[dict[str, Any]] = []
        self.replays: list[dict[str, Any]] = []
        self.reload()
        self.query_one("#groups", DataTable).focus()

    def action_refresh(self) -> None:
        self.reload()

    def action_home(self) -> None:
        self.app.go_home()

    def action_up(self) -> None:
        self.go_up()

    def action_open_group(self) -> None:
        focused = self.focused
        if isinstance(focused, DataTable) and focused.id == "replays":
            return
        self.open_selected_group()

    def reload(self) -> None:
        self.query_one("#path", Label).update(self.app.state.display_path)
        status = self.query_one("#status", Static)
        status.update("Loading...")
        try:
            client = self.app.require_client()
            state = self.app.state
            group_params = {
                "count": 200,
                "sort-by": state.group_sort_by,
                "sort-dir": state.group_sort_dir,
                **state.group_filters,
            }
            replay_params = {
                "count": 200,
                "sort-by": state.replay_sort_by,
                "sort-dir": state.replay_sort_dir,
                **state.replay_filters,
            }
            if state.group_id:
                group_params["group"] = state.group_id
                replay_params["group"] = state.group_id

            self.groups = client.list_groups(**group_params).get("list", [])
            self.replays = client.list_replays(**replay_params).get("list", [])
            self._fill_groups()
            self._fill_replays()
            status.update(f"{len(self.groups)} groups, {len(self.replays)} replays")
        except Exception as exc:  # noqa: BLE001
            status.update(str(exc))

    def _fill_groups(self) -> None:
        table = self.query_one("#groups", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_columns("Name", "Direct", "Indirect", "Created")
        for group in self.groups:
            table.add_row(
                group.get("name", ""),
                str(group.get("direct_replays", "")),
                str(group.get("indirect_replays", "")),
                group.get("created", ""),
            )

    def _fill_replays(self) -> None:
        table = self.query_one("#replays", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_columns("Title", "Visibility", "Playlist", "Created")
        for replay in self.replays:
            table.add_row(
                replay.get("replay_title") or replay.get("title") or "",
                replay.get("visibility", ""),
                replay.get("playlist_name") or replay.get("playlist_id") or "",
                replay.get("created", ""),
            )

    def selected_group(self) -> dict[str, Any] | None:
        table = self.query_one("#groups", DataTable)
        row = table.cursor_row
        return self.groups[row] if 0 <= row < len(self.groups) else None

    def selected_replay(self) -> dict[str, Any] | None:
        table = self.query_one("#replays", DataTable)
        row = table.cursor_row
        return self.replays[row] if 0 <= row < len(self.replays) else None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "groups":
            return
        self.open_selected_group()

    def open_selected_group(self) -> None:
        group = self.selected_group()
        if not group or not group.get("id"):
            return
        path = (*self.app.state.path, (group["id"], group.get("name", group["id"])))
        self.app.go_to_state(ExplorerState(group_id=group["id"], path=path))

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tier" or event.value is Select.BLANK:
            return
        self.app.config.subscription_tier = str(event.value)
        if self.app.client and hasattr(self.app.client, "limiter"):
            self.app.client.limiter.tier = str(event.value)
        self.app.save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back":
            self.app.go_back()
        elif button_id == "forward":
            self.app.go_forward()
        elif button_id == "up":
            self.go_up()
        elif button_id == "refresh":
            self.reload()
        elif button_id == "home":
            self.app.go_home()
        elif button_id == "api-token":
            self.app.push_screen(TokenScreen())
        elif button_id == "upload":
            self.app.push_screen(UploadScreen())
        elif button_id == "group-filters":
            self.app.push_screen(GroupFilterScreen())
        elif button_id == "replay-filters":
            self.app.push_screen(ReplayFilterScreen())
        elif button_id == "open-group":
            self.open_selected_group()
        elif button_id == "patch-group":
            group = self.selected_group()
            if group:
                self.app.push_screen(PatchGroupScreen(group["id"]))
        elif button_id == "delete-group":
            group = self.selected_group()
            if group:
                self.app.push_screen(DeleteGroupScreen(group["id"], group.get("name", group["id"])))
        elif button_id == "patch-replay":
            replay = self.selected_replay()
            if replay:
                self.app.push_screen(PatchReplayScreen(replay["id"]))
        elif button_id == "delete-replay":
            replay = self.selected_replay()
            if replay:
                self.app.push_screen(DeleteReplayScreen(replay["id"], replay.get("replay_title", replay["id"])))

    def go_up(self) -> None:
        if not self.app.state.path:
            self.app.go_home()
            return
        new_path = self.app.state.path[:-1]
        group_id = new_path[-1][0] if new_path else None
        self.app.go_to_state(replace(self.app.state, group_id=group_id, path=new_path))
