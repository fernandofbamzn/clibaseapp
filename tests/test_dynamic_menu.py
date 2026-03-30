from types import SimpleNamespace
from unittest.mock import Mock

import questionary

from clibaseapp import MenuAction
from clibaseapp.app import CLIBaseApp


class DummyDynamicApp(CLIBaseApp):
    def setup_commands(self) -> None:
        pass


def test_dynamic_menu_renders_status_suffix_and_executes_handler(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyDynamicApp(app_name="dummy-dynamic", description="dummy")

    handler = Mock()
    app.register_menu_action(
        MenuAction(
            id="sync",
            title="Sync",
            handler=handler,
            order=10,
            status_suffix=lambda: "[OK]",
        )
    )

    captured = {}
    answers = iter(["sync", "exit"])

    def fake_select(_message, choices):
        captured["titles"] = [choice.title for choice in choices]
        return SimpleNamespace(ask=lambda: next(answers))

    monkeypatch.setattr(questionary, "select", fake_select)
    monkeypatch.setattr("clibaseapp.app.pause", Mock())

    app._interactive_main_menu()

    assert "Sync [OK]" in captured["titles"]
    handler.assert_called_once()


def test_dynamic_menu_hides_invisible_actions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyDynamicApp(app_name="dummy-hidden", description="dummy")

    app.register_menu_action(
        MenuAction(id="hidden", title="Hidden", handler=Mock(), visible=lambda: False)
    )

    captured = {}

    def fake_select(_message, choices):
        captured["titles"] = [choice.title for choice in choices]
        return SimpleNamespace(ask=lambda: "exit")

    monkeypatch.setattr(questionary, "select", fake_select)

    app._interactive_main_menu()

    assert "Hidden" not in captured["titles"]


def test_dynamic_menu_marks_disabled_actions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyDynamicApp(app_name="dummy-disabled", description="dummy")

    app.register_menu_action(
        MenuAction(id="disabled", title="Disabled", handler=Mock(), enabled=lambda: False)
    )

    captured = {}

    def fake_select(_message, choices):
        captured["disabled"] = [choice.disabled for choice in choices if choice.value == "disabled"][0]
        return SimpleNamespace(ask=lambda: "exit")

    monkeypatch.setattr(questionary, "select", fake_select)

    app._interactive_main_menu()

    assert captured["disabled"] == "No disponible"
