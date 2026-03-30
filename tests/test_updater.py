import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from clibaseapp.core import updater


def _completed_process(stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=0, stdout=stdout, stderr=stderr)


def test_extract_direct_reference_requirements_detects_vcs_and_direct_urls(tmp_path: Path) -> None:
    req_path = tmp_path / "requirements.txt"
    req_path.write_text(
        "\n".join(
            [
                "rich",
                "clibaseapp @ git+https://github.com/example/clibaseapp.git",
                "git+https://github.com/example/private-tool.git",
                "package @ https://example.com/pkg.whl",
                "-r extra.txt",
            ]
        ),
        encoding="utf-8",
    )

    result = updater._extract_direct_reference_requirements(req_path)

    assert result == [
        "clibaseapp @ git+https://github.com/example/clibaseapp.git",
        "git+https://github.com/example/private-tool.git",
        "package @ https://example.com/pkg.whl",
    ]


def test_install_repo_requirements_force_reinstalls_direct_references(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    req_path = repo_root / "requirements.txt"
    req_path.write_text(
        "\n".join(
            [
                "rich",
                "clibaseapp @ git+https://github.com/example/clibaseapp.git",
            ]
        ),
        encoding="utf-8",
    )
    run = Mock()

    monkeypatch.setattr(updater.subprocess, "run", run)
    monkeypatch.setattr(updater, "show_info", Mock())

    updater._install_repo_requirements(repo_root)

    assert run.call_args_list[0].args[0] == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "-r",
        str(req_path),
    ]
    assert run.call_args_list[1].args[0] == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "--upgrade",
        "--force-reinstall",
        "clibaseapp @ git+https://github.com/example/clibaseapp.git",
    ]


def test_check_for_updates_when_repo_is_already_updated(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setattr(updater, "_discover_clibaseapp_repo", Mock(return_value=None))
    monkeypatch.setattr(updater, "show_success", show_success)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    assert run_git_command.call_args_list[2].args == (["pull"], repo_root)
    show_success.assert_called_once_with("La aplicacion ya esta en la ultima version.")
    execv.assert_not_called()


def test_check_for_updates_restarts_after_app_changes(monkeypatch, tmp_path: Path) -> None:
    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    show_warning = Mock()
    execv = Mock()
    install_requirements = Mock()

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
    monkeypatch.setattr(updater, "_discover_clibaseapp_repo", Mock(return_value=None))
    monkeypatch.setattr(updater, "_install_repo_requirements", install_requirements)
    monkeypatch.setattr(updater, "show_warning", show_warning)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    install_requirements.assert_called_once_with(repo_root)
    show_warning.assert_called_with("¡La aplicacion se ha actualizado! Reiniciando automaticamente...")
    execv.assert_called_once_with(sys.executable, [sys.executable] + sys.argv)


def test_check_for_updates_can_update_clibaseapp_after_prompt(monkeypatch, tmp_path: Path) -> None:
    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    framework_root = tmp_path / "clibaseapp"
    framework_root.mkdir()

    run_git_command = Mock(
        side_effect=[
            _completed_process(stdout="true\n"),
            _completed_process(stdout=f"{repo_root}\n"),
            _completed_process(stdout="Already up to date.\n"),
            _completed_process(stdout="Updating aaa..bbb\n"),
            _completed_process(stdout="Updating aaa..bbb\n"),
        ]
    )
    refresh_editable = Mock()
    show_warning = Mock()
    execv = Mock()

    monkeypatch.setattr(updater, "_run_git_command", run_git_command)
    monkeypatch.setattr(updater, "_discover_clibaseapp_repo", Mock(return_value=framework_root))
    monkeypatch.setattr(updater, "_refresh_editable_repo", refresh_editable)
    monkeypatch.setattr(
        updater.questionary,
        "confirm",
        lambda *_args, **_kwargs: SimpleNamespace(ask=lambda: True),
    )
    monkeypatch.setattr(updater, "show_warning", show_warning)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    assert run_git_command.call_args_list[2].args == (["pull"], repo_root)
    assert run_git_command.call_args_list[3].args == (["pull", "--dry-run"], framework_root)
    assert run_git_command.call_args_list[4].args == (["pull"], framework_root)
    refresh_editable.assert_called_once_with(framework_root)
    show_warning.assert_called_with("¡clibaseapp se ha actualizado! Reiniciando automaticamente...")
    execv.assert_called_once_with(sys.executable, [sys.executable] + sys.argv)


def test_check_for_updates_skips_clibaseapp_when_user_declines(monkeypatch, tmp_path: Path) -> None:
    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    framework_root = tmp_path / "clibaseapp"
    framework_root.mkdir()
    show_success = Mock()
    execv = Mock()

    run_git_command = Mock(
        side_effect=[
            _completed_process(stdout="true\n"),
            _completed_process(stdout=f"{repo_root}\n"),
            _completed_process(stdout="Already up to date.\n"),
            _completed_process(stdout="Updating aaa..bbb\n"),
        ]
    )

    monkeypatch.setattr(updater, "_run_git_command", run_git_command)
    monkeypatch.setattr(updater, "_discover_clibaseapp_repo", Mock(return_value=framework_root))
    monkeypatch.setattr(
        updater.questionary,
        "confirm",
        lambda *_args, **_kwargs: SimpleNamespace(ask=lambda: False),
    )
    monkeypatch.setattr(updater, "show_success", show_success)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    assert run_git_command.call_count == 4
    show_success.assert_called_once_with("La aplicacion ya esta en la ultima version.")
    execv.assert_not_called()


def test_check_for_updates_handles_non_git_installations(monkeypatch, tmp_path: Path) -> None:
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
    entrypoint = tmp_path / "app.py"
    entrypoint.write_text("print('app')", encoding="utf-8")
    show_error = Mock()

    monkeypatch.setattr(updater, "_run_git_command", Mock(side_effect=FileNotFoundError("git")))
    monkeypatch.setattr(updater, "show_error", show_error)

    updater.check_for_updates(str(entrypoint))

    show_error.assert_called_once_with("Comando 'git' no encontrado en el sistema.")


def test_check_for_updates_handles_pull_errors(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setattr(updater, "_discover_clibaseapp_repo", Mock(return_value=None))
    monkeypatch.setattr(updater, "show_error", show_error)
    monkeypatch.setattr(updater.os, "execv", execv)

    updater.check_for_updates(str(entrypoint))

    show_error.assert_called_once_with("Error al actualizar desde git: merge conflict")
    execv.assert_not_called()
