"""Modulo de actualizacion automatica desde el origen Git local del ejecutable."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import questionary

from clibaseapp.ui.components import clear_screen, show_error, show_header, show_info, show_success, show_warning


UP_TO_DATE_MARKERS = (
    "Already up to date.",
    "Already up-to-date.",
    "Ya esta actualizado.",
)


def _run_git_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando Git y devuelve su resultado."""

    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(cwd),
    )


def _show_non_git_installation_warning() -> None:
    """Informa al usuario de que la autoactualizacion por Git no esta disponible."""

    show_warning(
        "La actualizacion automatica por Git no esta disponible en este entorno. "
        "Si instalaste la aplicacion via pip o paquete, actualizala con ese mismo metodo."
    )


def _resolve_repo_root(project_dir: Path) -> Path:
    repo_check = _run_git_command(["rev-parse", "--is-inside-work-tree"], project_dir)
    if repo_check.stdout.strip().lower() != "true":
        raise subprocess.CalledProcessError(returncode=128, cmd=["git", "rev-parse"])
    return Path(_run_git_command(["rev-parse", "--show-toplevel"], project_dir).stdout.strip())


def _print_git_output(output: str) -> None:
    if output:
        from clibaseapp.ui.components import console

        console.print(f"[dim]{output}[/dim]")


def _is_repo_already_updated(output: str) -> bool:
    normalized = output.strip()
    return any(marker in normalized for marker in UP_TO_DATE_MARKERS)


def _discover_clibaseapp_repo(app_repo_root: Path) -> Path | None:
    try:
        import clibaseapp
    except Exception:
        return None

    module_dir = Path(clibaseapp.__file__).resolve().parent

    try:
        framework_repo_root = _resolve_repo_root(module_dir)
    except Exception:
        sibling_repo = app_repo_root.parent / "clibaseapp"
        if sibling_repo.exists():
            try:
                framework_repo_root = _resolve_repo_root(sibling_repo)
            except Exception:
                return None
        else:
            return None

    if framework_repo_root == app_repo_root:
        return None
    return framework_repo_root


def _repo_has_updates(repo_root: Path) -> tuple[bool, str]:
    result = _run_git_command(["pull", "--dry-run"], repo_root)
    output = result.stdout.strip()
    return (not _is_repo_already_updated(output), output)


def _read_requirements_lines(req_path: Path) -> list[str]:
    try:
        return req_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def _is_direct_reference_requirement(line: str) -> bool:
    normalized = line.strip()
    if not normalized or normalized.startswith("#"):
        return False
    if normalized.startswith(("-", "--")):
        return False

    prefixes = ("git+", "hg+", "svn+", "bzr+")
    infix_markers = (" @ git+", " @ hg+", " @ svn+", " @ bzr+", " @ https://", " @ http://")
    return normalized.startswith(prefixes) or any(marker in normalized for marker in infix_markers)


def _extract_direct_reference_requirements(req_path: Path) -> list[str]:
    return [
        line.strip()
        for line in _read_requirements_lines(req_path)
        if _is_direct_reference_requirement(line)
    ]


def _install_repo_requirements(repo_root: Path) -> None:
    req_path = repo_root / "requirements.txt"
    if not req_path.exists():
        return

    show_info("Actualizando dependencias del entorno de la aplicacion...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_path)],
        cwd=repo_root,
        check=True,
    )

    direct_requirements = _extract_direct_reference_requirements(req_path)
    if not direct_requirements:
        return

    show_info("Forzando la reinstalacion de dependencias VCS/direct URL...")
    for requirement in direct_requirements:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--upgrade",
                "--force-reinstall",
                requirement,
            ],
            cwd=repo_root,
            check=True,
        )


def _refresh_editable_repo(repo_root: Path) -> None:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return

    show_info(f"Actualizando instalacion editable de {repo_root.name}...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-e", str(repo_root)],
        cwd=repo_root,
        check=True,
    )


def check_for_updates(app_entrypoint_file: str) -> None:
    """Actualiza el repo de la app y opcionalmente el repo editable de clibaseapp."""

    clear_screen()
    show_header("Actualizacion de la Aplicacion", icon="🔄")

    project_dir = Path(app_entrypoint_file).parent.resolve()

    try:
        repo_root = _resolve_repo_root(project_dir)
    except subprocess.CalledProcessError:
        _show_non_git_installation_warning()
        return
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
        return
    except Exception as exc:
        show_error(f"Error inesperado al preparar la actualizacion: {exc}")
        return

    app_updated = False
    framework_updated = False
    framework_repo_root = _discover_clibaseapp_repo(repo_root)

    show_info("Buscando actualizaciones en el repositorio remoto...")

    try:
        app_result = _run_git_command(["pull"], repo_root)
        app_output = app_result.stdout.strip()
        _print_git_output(app_output)
        app_updated = not _is_repo_already_updated(app_output)

        if framework_repo_root is not None:
            show_info(f"Comprobando actualizaciones para {framework_repo_root.name}...")
            has_framework_updates, framework_probe_output = _repo_has_updates(framework_repo_root)
            _print_git_output(framework_probe_output)

            if has_framework_updates:
                update_framework = questionary.confirm(
                    f"Hay actualizaciones para '{framework_repo_root.name}'. ¿Quieres actualizarlas tambien?",
                    default=True,
                ).ask()
                if update_framework:
                    framework_result = _run_git_command(["pull"], framework_repo_root)
                    framework_output = framework_result.stdout.strip()
                    _print_git_output(framework_output)
                    framework_updated = not _is_repo_already_updated(framework_output)
                else:
                    show_info(f"Se omite la actualizacion de {framework_repo_root.name}.")

        if app_updated:
            _install_repo_requirements(repo_root)

        if framework_updated and framework_repo_root is not None:
            _refresh_editable_repo(framework_repo_root)

        if not app_updated and not framework_updated:
            show_success("La aplicacion ya esta en la ultima version.")
            return

        if app_updated and framework_updated:
            show_warning("¡La aplicacion y clibaseapp se han actualizado! Reiniciando automaticamente...")
        elif app_updated:
            show_warning("¡La aplicacion se ha actualizado! Reiniciando automaticamente...")
        else:
            show_warning("¡clibaseapp se ha actualizado! Reiniciando automaticamente...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        show_error(f"Error al actualizar desde git: {stderr}")
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
    except Exception as exc:
        show_error(f"Error inesperado al intentar actualizar: {exc}")
