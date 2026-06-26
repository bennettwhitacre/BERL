from pathlib import Path

from berl.config import AppConfig, UploadDefaults, load_config, save_config


def test_load_missing_config_uses_defaults(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.json")

    assert config.api_token == ""
    assert config.subscription_tier == "free"
    assert config.upload_defaults == UploadDefaults()


def test_save_and_load_config(tmp_path: Path) -> None:
    path = tmp_path / ".berl" / "config.json"
    config = AppConfig(
        api_token="token",
        subscription_tier="diamond",
        upload_defaults=UploadDefaults(
            visibility="private",
            player_identification="by-name",
            team_identification="by-player-clusters",
            shared=True,
        ),
    )

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config
