from pathlib import Path

from clibaseapp.core.config import ConfigManager


def test_get_merges_default_global_and_app_with_expected_priority(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config = ConfigManager(
        app_name="demo-app",
        default_config={"shared": "default", "local_only": "default-local"},
    )

    config.update("shared", "global", scope="global")
    config.update("global_only", "global-value", scope="global")
    config.update("shared", "app", scope="app")
    config.update("app_only", "app-value", scope="app")

    assert config.get("shared") == "app"
    assert config.get("global_only") == "global-value"
    assert config.get("app_only") == "app-value"
    assert config.get("local_only") == "default-local"


def test_get_prefers_environment_variable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("DEMO_VALUE", "from-env")
    config = ConfigManager(app_name="demo-app", default_config={"key": "from-default"})

    config.update("key", "from-global", scope="global")
    config.update("key", "from-app")

    assert config.get("key", env_var="DEMO_VALUE") == "from-env"


def test_set_is_alias_of_update(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config = ConfigManager(app_name="demo-app")

    config.set("sample", "value")

    assert config.read_all()["sample"] == "value"
