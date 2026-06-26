from __future__ import annotations

from textual.app import App

from berl.api import BallchasingClient, BallchasingError
from berl.config import AppConfig, load_config, save_config
from berl.models import ExplorerState
from berl.rate_limit import RateLimiter
from berl.screens.explorer import ExplorerScreen
from berl.screens.token import TokenScreen


class BerlApp(App[None]):
    CSS_PATH = "styles.tcss"
    TITLE = "BERL"
    SUB_TITLE = "Ballchasing Easy Replay Loader"

    def __init__(self) -> None:
        super().__init__()
        self.config: AppConfig = load_config()
        self.client: BallchasingClient | None = None
        self.state = ExplorerState()
        self.history: list[ExplorerState] = [self.state]
        self.history_index = 0

    def on_mount(self) -> None:
        if not self.config.api_token:
            self.push_screen(TokenScreen())
            return

        try:
            self.set_token(self.config.api_token)
            assert self.client is not None
            self.client.ping()
        except Exception:
            self.push_screen(TokenScreen())
            return

        self.push_screen(ExplorerScreen())

    def set_token(self, token: str) -> None:
        self.config.api_token = token
        self.client = BallchasingClient(
            token,
            limiter=RateLimiter(self.config.subscription_tier),
        )

    def save(self) -> None:
        save_config(self.config)

    def require_client(self) -> BallchasingClient:
        if self.client is None:
            raise BallchasingError("No API token configured.")
        return self.client

    def go_to_state(self, state: ExplorerState, *, record: bool = True) -> None:
        self.state = state
        if record:
            self.history = self.history[: self.history_index + 1]
            self.history.append(state)
            self.history_index = len(self.history) - 1
        screen = self.screen
        if isinstance(screen, ExplorerScreen):
            screen.reload()

    def go_back(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.go_to_state(self.history[self.history_index], record=False)

    def go_forward(self) -> None:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.go_to_state(self.history[self.history_index], record=False)

    def go_home(self) -> None:
        self.go_to_state(ExplorerState())


def main() -> None:
    BerlApp().run()
