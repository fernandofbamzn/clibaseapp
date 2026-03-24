import subprocess
from pathlib import Path
from unittest.mock import Mock

from clibaseapp.services import sshfs_service


class DummyConfig:
    def __init__(self, mount_point: str):
        self.app_name = "dummy-sshfs"
        self._data = {
            "download_root": mount_point,
            "sshfs_config": {},
        }

    def get(self, key, default=None):
        return self._data.get(key, default)

    def update(self, key, value):
        self._data[key] = value


def test_mount_drive_handles_missing_sshfs(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    config = DummyConfig(str(mount_point))
    inputs = iter(["1.2.3.4", "/remote/path", "root"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: False)

    def _run(command, **_kwargs):
        if command[0] == "sshfs":
            raise FileNotFoundError("sshfs")
        return subprocess.CompletedProcess(command, 0, "", "")

    run_mock = Mock(side_effect=_run)
    monkeypatch.setattr(sshfs_service.subprocess, "run", run_mock)

    sshfs_service.mount_drive(config)

    assert run_mock.call_count == 1
    assert config.get("sshfs_config")["ip"] == "1.2.3.4"
    assert run_mock.call_args.args[0][1] == "root@1.2.3.4:/remote/path"


def test_mount_drive_handles_non_zero_sshfs_exit(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    config = DummyConfig(str(mount_point))
    inputs = iter(["1.2.3.4", "/remote/path", "root"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: False)
    monkeypatch.setattr(
        sshfs_service.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                ["sshfs"],
                1,
                stdout="",
                stderr="connection refused",
            )
        ),
    )

    sshfs_service.mount_drive(config)


def test_mount_drive_reports_successful_command_without_real_mount(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    config = DummyConfig(str(mount_point))
    inputs = iter(["1.2.3.4", "/remote/path", "root"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: False)
    monkeypatch.setattr(
        sshfs_service.subprocess,
        "run",
        Mock(return_value=subprocess.CompletedProcess(["sshfs"], 0, stdout="", stderr="")),
    )

    sshfs_service.mount_drive(config)


def test_mount_drive_can_unmount_before_remount(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    mount_point.mkdir(parents=True, exist_ok=True)
    config = DummyConfig(str(mount_point))
    inputs = iter(["s", "1.2.3.4", "/remote/path", "root"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    ismount_values = iter([True, False, False, True])
    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: next(ismount_values))

    run_mock = Mock(
        side_effect=[
            subprocess.CompletedProcess(["umount"], 0, stdout="", stderr=""),
            subprocess.CompletedProcess(["sshfs"], 0, stdout="", stderr=""),
        ]
    )
    monkeypatch.setattr(sshfs_service.subprocess, "run", run_mock)

    sshfs_service.mount_drive(config)

    assert run_mock.call_args_list[0].args[0][0] == "umount"
    assert run_mock.call_args_list[1].args[0][0] == "sshfs"


def test_mount_drive_aborts_when_directory_has_content_and_user_declines(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    mount_point.mkdir(parents=True, exist_ok=True)
    (mount_point / "existing.txt").write_text("x", encoding="utf-8")
    config = DummyConfig(str(mount_point))

    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: False)
    run_mock = Mock()
    monkeypatch.setattr(sshfs_service.subprocess, "run", run_mock)

    sshfs_service.mount_drive(config)

    run_mock.assert_not_called()


def test_describe_mount_status_does_not_treat_content_as_mounted(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    mount_point.mkdir(parents=True, exist_ok=True)
    (mount_point / "existing.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(sshfs_service.os.path, "ismount", lambda _path: False)
    monkeypatch.setattr(sshfs_service, "_detect_mount_from_mountinfo", lambda _path: None)
    monkeypatch.setattr(sshfs_service, "_detect_mount_from_commands", lambda _path: None)
    monkeypatch.setattr(sshfs_service, "_detect_mount_from_stat", lambda _path: None)

    mounted, detail = sshfs_service.describe_mount_status(str(mount_point))

    assert mounted is False
    assert "no se pudo verificar como punto de montaje" in detail.lower()


def test_detect_mount_from_commands_ignores_findmnt_non_exact_target(monkeypatch, tmp_path: Path) -> None:
    mount_point = tmp_path / "mnt"
    mount_point.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sshfs_service.shutil, "which", lambda command: "x" if command == "findmnt" else None)
    monkeypatch.setattr(
        sshfs_service.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                ["findmnt"],
                0,
                stdout="/ /dev/sda1 ext4\n",
                stderr="",
            )
        ),
    )

    detail = sshfs_service._detect_mount_from_commands(mount_point)

    assert detail is None
