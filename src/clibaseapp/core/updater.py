"""
Modulo de actualización automática desde el origen Git local del ejecutable.
"""

import os
import subprocess
import sys
from pathlib import Path

from clibaseapp.ui.components import clear_screen, show_header, show_info, show_success, show_warning, show_error


def check_for_updates(app_entrypoint_file: str) -> None:
    """Realiza un git pull desde la ruta del entrypoint y reinicia si hay cambios."""
    clear_screen()
    show_header("Actualización de la Aplicación", icon="🔄")
    show_info("Buscando actualizaciones en el repositorio remoto...")

    project_dir = str(Path(app_entrypoint_file).parent.resolve())

    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir
        )
        
        output = result.stdout.strip()
        from clibaseapp.ui.components import console
        console.print(f"[dim]{output}[/dim]")

        if "Already up to date." in output or "Ya está actualizado." in output:
            show_success("La aplicación ya está en la última versión.")
        else:
            show_warning("¡La aplicación se ha actualizado! Reiniciando automáticamente...")
            
            # Limpiamos y recreamos el proceso desde 0 usando el interprete actual (venv)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
    except subprocess.CalledProcessError as exc:
        show_error(f"Error al actualizar desde git: {exc.stderr}")
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
    except Exception as exc:
        show_error(f"Error inesperado al intentar actualizar: {exc}")
