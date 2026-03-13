import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

from clibaseapp.core import updater


def _completed_process(stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=0, stdout=stdout, stderr=stderr)


def test_check_for_updates_when_repo_is_already_updated(monkeypatch, tmp_path: Path) -> None:
    """Prueba el flujo de un repositorio Git ya actualizado."""

    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_git_command = Mock(
        side_effect=[
            _completed_process(stdout="true\n"),
            _completed_process(stdout=f"{repo_root}\n"),
            _completed_process(stdout="Already up to date.\n"),
        ]
    )
    show_success = Mock()
    execv = Mock()

    monkeypatch.setattr(updater, "_run_git_command", run_git_command)
    monkeypatch.setattr(updater, "show_success", show_success)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    assert run_git_command.call_args_list[2].args == (["pull"], repo_root)
    show_success.assert_called_once_with("La aplicación ya está en la última versión.")
    execv.assert_not_called()


def test_check_for_updates_restarts_after_changes(monkeypatch, tmp_path: Path) -> None:
    """Prueba que el updater reinicia el proceso cuando git pull trae cambios."""

    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    show_warning = Mock()
    execv = Mock()

    monkeypatch.setattr(
        updater,
        "_run_git_command",
        Mock(
            side_effect=[
                _completed_process(stdout="true\n"),
                _completed_process(stdout=f"{repo_root}\n"),
                _completed_process(stdout="Updating 123..456\n"),
            ]
        ),
    )
    monkeypatch.setattr(updater, "show_warning", show_warning)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    show_warning.assert_called_with("¡La aplicación se ha actualizado! Reiniciando automáticamente...")
    execv.assert_called_once_with(sys.executable, [sys.executable] + sys.argv)


def test_check_for_updates_handles_non_git_installations(monkeypatch, tmp_path: Path) -> None:
    """Prueba que las instalaciones no Git muestran un aviso limpio."""

    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    show_warning = Mock()
    execv = Mock()

    monkeypatch.setattr(
        updater,
        "_run_git_command",
        Mock(
            side_effect=subprocess.CalledProcessError(
                returncode=128,
                cmd=["git", "rev-parse", "--is-inside-work-tree"],
                stderr="not a git repo",
            )
        ),
    )
    monkeypatch.setattr(updater, "show_warning", show_warning)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    show_warning.assert_called_once()
    execv.assert_not_called()


def test_check_for_updates_handles_missing_git(monkeypatch, tmp_path: Path) -> None:
    """Prueba que se informa correctamente cuando git no está instalado."""

    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    show_error = Mock()

    monkeypatch.setattr(updater, "_run_git_command", Mock(side_effect=FileNotFoundError("git")))
    monkeypatch.setattr(updater, "show_error", show_error)

    updater.check_for_updates(str(entrypoint))

    show_error.assert_called_once_with("Comando 'git' no encontrado en el sistema.")


def test_check_for_updates_handles_pull_errors(monkeypatch, tmp_path: Path) -> None:
    """Prueba que un fallo de git pull se comunica como error."""

    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    show_error = Mock()
    execv = Mock()

    monkeypatch.setattr(
        updater,
        "_run_git_command",
        Mock(
            side_effect=[
                _completed_process(stdout="true\n"),
                _completed_process(stdout=f"{repo_root}\n"),
                subprocess.CalledProcessError(returncode=1, cmd=["git", "pull"], stderr="merge conflict"),
            ]
        ),
    )
    monkeypatch.setattr(updater, "show_error", show_error)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    show_error.assert_called_once_with("Error al actualizar desde git: merge conflict")
    execv.assert_not_called()
