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
        self.groups_by_parent = {}
        self.replays_by_group = {}
        self.replay_calls = []

    def list_groups(self, **params: object) -> dict[str, object]:
        if "group" in params:
            return {"list": self.groups_by_parent.get(params["group"], [])}
        return {"list": self.groups}

    def list_replays(self, **params: object) -> dict[str, object]:
        self.replay_calls.append(params)
        return {"list": self.replays_by_group.get(params.get("group"), [])}


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


def test_token_screen_clear_button_clears_current_token() -> None:
    async def run() -> tuple[str, object, str]:
        app = BerlApp()
        app.config = AppConfig(api_token="old-token")
        app.client = FakeClient()  # type: ignore[assignment]
        async with app.run_test() as pilot:
            await app.push_screen(TokenScreen())
            await pilot.pause()
            await pilot.click("#clear-token")
            await pilot.pause()
            token_value = app.screen.query_one("#token").value  # type: ignore[attr-defined]
            return app.config.api_token, app.client, token_value

    token, client, input_value = asyncio.run(run())
    assert token == ""
    assert client is None
    assert input_value == ""


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


def test_replays_default_to_current_group_top_level_only() -> None:
    async def run() -> list[dict[str, object]]:
        app = BerlApp()
        app.config = AppConfig()
        client = FakeClient()
        client.replays_by_group = {
            "root": [{"id": "root-replay", "replay_title": "Root"}],
            "child": [{"id": "child-replay", "replay_title": "Child"}],
        }
        client.groups_by_parent = {"root": [{"id": "child", "name": "Child"}]}
        app.state = app.state.__class__(group_id="root", path=(("root", "Root"),))
        async with app.run_test() as pilot:
            app.client = client  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            return app.screen.replays  # type: ignore[attr-defined]

    assert asyncio.run(run()) == [{"id": "root-replay", "replay_title": "Root"}]


def test_replays_toggle_can_include_subgroups() -> None:
    async def run() -> list[str]:
        app = BerlApp()
        app.config = AppConfig()
        client = FakeClient()
        client.replays_by_group = {
            "root": [{"id": "root-replay", "replay_title": "Root"}],
            "child": [{"id": "child-replay", "replay_title": "Child"}],
        }
        client.groups_by_parent = {"root": [{"id": "child", "name": "Child"}], "child": []}
        app.state = app.state.__class__(group_id="root", path=(("root", "Root"),))
        async with app.run_test() as pilot:
            app.client = client  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            await pilot.click("#direct-replays-only")
            await pilot.pause()
            return [replay["id"] for replay in app.screen.replays]  # type: ignore[attr-defined]

    assert asyncio.run(run()) == ["root-replay", "child-replay"]


def test_home_replays_default_to_ungrouped_only() -> None:
    async def run() -> list[str]:
        app = BerlApp()
        app.config = AppConfig()
        client = FakeClient()
        client.replays_by_group = {
            None: [
                {"id": "ungrouped", "replay_title": "Ungrouped", "groups": []},
                {"id": "grouped", "replay_title": "Grouped", "groups": [{"id": "group-1"}]},
            ]
        }
        async with app.run_test() as pilot:
            app.client = client  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            return [replay["id"] for replay in app.screen.replays]  # type: ignore[attr-defined]

    assert asyncio.run(run()) == ["ungrouped"]


def test_home_replays_toggle_can_show_all_uploaded_replays() -> None:
    async def run() -> list[str]:
        app = BerlApp()
        app.config = AppConfig()
        client = FakeClient()
        client.replays_by_group = {
            None: [
                {"id": "ungrouped", "replay_title": "Ungrouped", "groups": []},
                {"id": "grouped", "replay_title": "Grouped", "groups": [{"id": "group-1"}]},
            ]
        }
        async with app.run_test() as pilot:
            app.client = client  # type: ignore[assignment]
            await app.push_screen(ExplorerScreen())
            await pilot.pause()
            await pilot.click("#direct-replays-only")
            await pilot.pause()
            return [replay["id"] for replay in app.screen.replays]  # type: ignore[attr-defined]

    assert asyncio.run(run()) == ["ungrouped", "grouped"]
