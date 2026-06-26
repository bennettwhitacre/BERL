import asyncio

from berl.app import BerlApp
from berl.config import AppConfig
from berl.rate_limit import RateLimiter
from berl.screens.delete import DeleteGroupScreen
from berl.screens.explorer import ExplorerScreen
from berl.screens.token import TokenScreen


class FakeClient:
    def __init__(self) -> None:
        self.limiter = RateLimiter()
        self.groups = []

    def list_groups(self, **params: object) -> dict[str, object]:
        return {"list": self.groups}

    def list_replays(self, **params: object) -> dict[str, object]:
        return {"list": []}


def test_app_can_be_constructed() -> None:
    app = BerlApp()
    app.config = AppConfig()

    assert app.config.subscription_tier == "free"


def test_delete_group_screen_can_be_constructed() -> None:
    screen = DeleteGroupScreen("group-1", "Group")

    assert screen.group_id == "group-1"
    assert screen.group_name == "Group"


def test_app_routes_to_token_screen_without_token() -> None:
    async def run() -> str:
        app = BerlApp()
        app.config = AppConfig()
        async with app.run_test() as pilot:
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(run()) == TokenScreen.__name__


def test_explorer_screen_renders_with_empty_lists() -> None:
    async def run() -> str:
        app = BerlApp()
        app.config = AppConfig()
        async with app.run_test() as pilot:
            app.client = FakeClient()  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(run()) == ExplorerScreen.__name__


def test_open_group_button_navigates_into_selected_group() -> None:
    async def run() -> str | None:
        app = BerlApp()
        app.config = AppConfig()
        client = FakeClient()
        client.groups = [{"id": "group-1", "name": "Series", "direct_replays": 0, "indirect_replays": 0}]
        async with app.run_test() as pilot:
            app.client = client  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            await pilot.click("#open-group")
            await pilot.pause()
            return app.state.group_id

    assert asyncio.run(run()) == "group-1"
