from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class TokenScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        with Container(id="token-wrap"):
            with Vertical(id="token-panel"):
                yield Label("ballchasing.com API token")
                yield Input(password=True, placeholder="Paste API token", id="token")
                yield Button("Validate", id="validate", variant="primary")
                yield Static("", id="token-status", classes="status")

    def on_mount(self) -> None:
        token_input = self.query_one("#token", Input)
        if self.app.config.api_token:
            token_input.value = self.app.config.api_token
        token_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "validate":
            return
        token = self.query_one("#token", Input).value.strip()
        status = self.query_one("#token-status", Static)
        if not token:
            status.update("Enter an API token.")
            return

        status.update("Checking token...")
        try:
            self.app.set_token(token)
            self.app.require_client().ping()
        except Exception as exc:  # noqa: BLE001 - user needs the API error text here.
            status.update(str(exc))
            return

        self.app.save()
        self.app.pop_screen()
        from berl.screens.explorer import ExplorerScreen

        self.app.push_screen(ExplorerScreen())
