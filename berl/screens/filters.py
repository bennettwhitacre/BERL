from __future__ import annotations

from dataclasses import replace

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select


def _clean(values: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value not in ("", None)}


class GroupFilterScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def compose(self) -> ComposeResult:
        yield Label("Group filters")
        yield Input(placeholder="Name", id="name")
        yield Input(placeholder="Child group id", id="group")
        yield Input(placeholder="Created after RFC3339", id="created-after")
        yield Input(placeholder="Created before RFC3339", id="created-before")
        yield Input(placeholder="Count 1-200", id="count")
        yield Select([("created", "created"), ("name", "name")], value=self.app.state.group_sort_by, id="sort-by")
        yield Select([("desc", "desc"), ("asc", "asc")], value=self.app.state.group_sort_dir, id="sort-dir")
        with Horizontal(id="filter-actions"):
            yield Button("Apply", id="apply", variant="primary")
            yield Button("Clear", id="clear")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        filters = self.app.state.group_filters
        for field_id in ("name", "group", "created-after", "created-before", "count"):
            self.query_one(f"#{field_id}", Input).value = str(filters.get(field_id, ""))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        if event.button.id == "clear":
            new_state = replace(self.app.state, group_filters={}, group_sort_by="created", group_sort_dir="desc")
        else:
            filters = _clean(
                {
                    "name": self.query_one("#name", Input).value.strip(),
                    "group": self.query_one("#group", Input).value.strip(),
                    "created-after": self.query_one("#created-after", Input).value.strip(),
                    "created-before": self.query_one("#created-before", Input).value.strip(),
                    "count": self.query_one("#count", Input).value.strip(),
                }
            )
            sort_by = str(self.query_one("#sort-by", Select).value)
            sort_dir = str(self.query_one("#sort-dir", Select).value)
            new_state = replace(self.app.state, group_filters=filters, group_sort_by=sort_by, group_sort_dir=sort_dir)
        self.app.pop_screen()
        self.app.go_to_state(new_state)


class ReplayFilterScreen(Screen[None]):
    CSS_CLASSES = "form-screen"

    def compose(self) -> ComposeResult:
        yield Label("Replay filters")
        for field_id, placeholder in (
            ("title", "Title"),
            ("player-name", "Player name"),
            ("player-id", "Player id platform:id"),
            ("playlist", "Playlist"),
            ("season", "Season"),
            ("match-result", "Match result win/loss"),
            ("min-rank", "Min rank"),
            ("max-rank", "Max rank"),
            ("pro", "Pro true/false"),
            ("group", "Group id"),
            ("map", "Map code"),
            ("created-after", "Created after RFC3339"),
            ("created-before", "Created before RFC3339"),
            ("replay-date-after", "Replay date after RFC3339"),
            ("replay-date-before", "Replay date before RFC3339"),
            ("count", "Count 1-200"),
        ):
            yield Input(placeholder=placeholder, id=field_id)
        yield Select(
            [("upload-date", "upload-date"), ("replay-date", "replay-date")],
            value=self.app.state.replay_sort_by,
            id="sort-by",
        )
        yield Select([("desc", "desc"), ("asc", "asc")], value=self.app.state.replay_sort_dir, id="sort-dir")
        with Horizontal(id="filter-actions"):
            yield Button("Apply", id="apply", variant="primary")
            yield Button("Clear", id="clear")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        filters = self.app.state.replay_filters
        for field_id in (
            "title",
            "player-name",
            "player-id",
            "playlist",
            "season",
            "match-result",
            "min-rank",
            "max-rank",
            "pro",
            "group",
            "map",
            "created-after",
            "created-before",
            "replay-date-after",
            "replay-date-before",
            "count",
        ):
            self.query_one(f"#{field_id}", Input).value = str(filters.get(field_id, ""))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return
        if event.button.id == "clear":
            new_state = replace(self.app.state, replay_filters={}, replay_sort_by="upload-date", replay_sort_dir="desc")
        else:
            field_ids = (
                "title",
                "player-name",
                "player-id",
                "playlist",
                "season",
                "match-result",
                "min-rank",
                "max-rank",
                "pro",
                "group",
                "map",
                "created-after",
                "created-before",
                "replay-date-after",
                "replay-date-before",
                "count",
            )
            filters = _clean({field_id: self.query_one(f"#{field_id}", Input).value.strip() for field_id in field_ids})
            sort_by = str(self.query_one("#sort-by", Select).value)
            sort_dir = str(self.query_one("#sort-dir", Select).value)
            new_state = replace(self.app.state, replay_filters=filters, replay_sort_by=sort_by, replay_sort_dir=sort_dir)
        self.app.pop_screen()
        self.app.go_to_state(new_state)
