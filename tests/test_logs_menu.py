from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import questionary

from clibaseapp.app import CLIBaseApp


class DummyApp(CLIBaseApp):
    def setup_commands(self) -> None:
        pass


def _prompt_with_answers(answers):
    iterator = iter(answers)

    def _factory(*_args, **_kwargs):
        return SimpleNamespace(ask=lambda: next(iterator))

    return _factory


def test_run_logs_warns_when_no_logs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyApp(app_name="dummy-no-logs", description="dummy")
    app._app_dir = tmp_path
    app.logger = Mock()

    show_warning = Mock()
    monkeypatch.setattr("clibaseapp.app.show_warning", show_warning)

    app._run_logs()

    show_warning.assert_called_once()


def test_run_logs_can_view_selected_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyApp(app_name="dummy-view-logs", description="dummy")
    app._app_dir = tmp_path
    app.logger = Mock()

    log_file = tmp_path / "logs" / "2026-03-24.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("contenido del log", encoding="utf-8")

    monkeypatch.setattr(
        questionary,
        "select",
        _prompt_with_answers([
            f"📄 {log_file.name} ({log_file.parent.name})",
            "👁 Ver log",
            "❌ Volver",
        ]),
    )
    app.console.print = Mock()

    app._run_logs()

    app.console.print.assert_any_call("contenido del log")


def test_run_logs_can_delete_selected_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyApp(app_name="dummy-delete-log", description="dummy")
    app._app_dir = tmp_path
    app.logger = Mock()

    log_file = tmp_path / "logs" / "2026-03-24.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("contenido", encoding="utf-8")

    monkeypatch.setattr(
        questionary,
        "select",
        _prompt_with_answers([
            f"📄 {log_file.name} ({log_file.parent.name})",
            "🗑 Borrar log",
            "❌ Volver",
        ]),
    )
    monkeypatch.setattr(questionary, "confirm", lambda *_args, **_kwargs: SimpleNamespace(ask=lambda: True))

    app._run_logs()

    assert not log_file.exists()


def test_run_logs_can_delete_all_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyApp(app_name="dummy-delete-all-logs", description="dummy")
    app._app_dir = tmp_path
    app.logger = Mock()

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_a = log_dir / "2026-03-23.log"
    file_b = log_dir / "2026-03-24.log"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    monkeypatch.setattr(
        questionary,
        "select",
        _prompt_with_answers([
            "🧹 Borrar todos los logs",
            "❌ Volver",
        ]),
    )
    monkeypatch.setattr(questionary, "confirm", lambda *_args, **_kwargs: SimpleNamespace(ask=lambda: True))

    app._run_logs()

    assert not file_a.exists()
    assert not file_b.exists()


def test_run_logs_warns_when_deletion_fails(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    app = DummyApp(app_name="dummy-blocked-log", description="dummy")
    app._app_dir = tmp_path
    app.logger = Mock()

    log_file = tmp_path / "logs" / "2026-03-24.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("contenido", encoding="utf-8")

    original_unlink = Path.unlink

    def _blocked_unlink(self: Path, *args, **kwargs):
        if self == log_file:
            raise PermissionError("bloqueado")
        return original_unlink(self, *args, **kwargs)

    show_warning = Mock()
    monkeypatch.setattr(Path, "unlink", _blocked_unlink)
    monkeypatch.setattr("clibaseapp.app.show_warning", show_warning)
    monkeypatch.setattr(
        questionary,
        "select",
        _prompt_with_answers([
            f"📄 {log_file.name} ({log_file.parent.name})",
            "🗑 Borrar log",
            "❌ Volver",
        ]),
    )
    monkeypatch.setattr(questionary, "confirm", lambda *_args, **_kwargs: SimpleNamespace(ask=lambda: True))

    app._run_logs()

    assert log_file.exists()
    show_warning.assert_called()
