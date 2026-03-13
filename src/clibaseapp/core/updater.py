"""
Módulo de actualización automática desde el origen Git local del ejecutable.
"""

import os
import subprocess
import sys
from pathlib import Path

from clibaseapp.ui.components import clear_screen, show_error, show_header, show_info, show_success, show_warning


def _run_git_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando Git y devuelve su resultado.

    Centralizar la llamada facilita el testeo y mantiene homogéneo el
    tratamiento de `capture_output`, `text` y `cwd`.
    """

    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(cwd),
    )


def _show_non_git_installation_warning() -> None:
    """Informa al usuario de que la autoactualización por Git no está disponible."""

    show_warning(
        "La actualización automática por Git no está disponible en este entorno. "
        "Si instalaste la aplicación vía pip o paquete, actualízala con ese mismo método."
    )


def check_for_updates(app_entrypoint_file: str) -> None:
    """Realiza un `git pull` desde la raíz del repo y reinicia si hay cambios.

    Si el entrypoint no está dentro de un repositorio Git válido, informa al
    usuario y retorna sin tratarlo como error de ejecución.
    """

    clear_screen()
    show_header("Actualización de la Aplicación", icon="🔄")

    project_dir = Path(app_entrypoint_file).parent.resolve()

    try:
        repo_check = _run_git_command(["rev-parse", "--is-inside-work-tree"], project_dir)
        if repo_check.stdout.strip().lower() != "true":
            _show_non_git_installation_warning()
            return

        repo_root = Path(
            _run_git_command(["rev-parse", "--show-toplevel"], project_dir).stdout.strip()
        )
    except subprocess.CalledProcessError:
        _show_non_git_installation_warning()
        return
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
        return
    except Exception as exc:
        show_error(f"Error inesperado al preparar la actualización: {exc}")
        return

    show_info("Buscando actualizaciones en el repositorio remoto...")

    try:
        result = _run_git_command(["pull"], repo_root)
        output = result.stdout.strip()

        if output:
            from clibaseapp.ui.components import console

            console.print(f"[dim]{output}[/dim]")

        if "Already up to date." in output or "Ya está actualizado." in output:
            show_success("La aplicación ya está en la última versión.")
            return

        show_warning("¡La aplicación se ha actualizado! Reiniciando automáticamente...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        show_error(f"Error al actualizar desde git: {stderr}")
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
    except Exception as exc:
        show_error(f"Error inesperado al intentar actualizar: {exc}")
