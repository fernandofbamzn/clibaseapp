"""
Verificación e instalación automática de dependencias Python.
"""

import importlib
import subprocess
import sys
from types import ModuleType
from typing import List, Optional, Sequence

from clibaseapp.exceptions import DependencyInstallationError
from clibaseapp.ui.components import console


def _load_optional_module(module_name: str) -> Optional[ModuleType]:
    """Carga un módulo opcional y devuelve None si no está disponible."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def missing_packages(required: List[str]) -> List[str]:
    """Detecta dependencias faltantes de la lista proporcionada."""
    return [pkg for pkg in required if _load_optional_module(pkg) is None]


def install_packages(packages: Sequence[str]) -> None:
    """Instala paquetes usando pip del entorno actual."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *packages],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or "Sin salida de error disponible."
        raise DependencyInstallationError(
            f"No se pudieron instalar dependencias ({', '.join(packages)}): {details}"
        ) from exc


def check_and_install(required_packages: List[str]) -> None:
    """Comprueba dependencias y gestiona su instalación interactiva.

    Args:
        required_packages: Lista de nombres de paquetes pip a verificar.
    """
    missing = missing_packages(required_packages)

    if not missing:
        return

    console.print("\n[cyan]Dependencias faltantes detectadas:[/]\n")
    for pkg in missing:
        console.print(f" • {pkg}")

    # Intentar usar questionary si está disponible
    questionary_module = _load_optional_module("questionary")

    if questionary_module is None:
        console.print(
            "\n[yellow]No se encontró 'questionary'. No se puede solicitar confirmación interactiva.[/]"
        )
        console.print(
            "[yellow]Instala las dependencias manualmente y vuelve a ejecutar.[/]\n"
        )
        raise SystemExit(1)

    confirm = questionary_module.confirm(
        "¿Instalarlas ahora?",
        default=True,
    ).ask()

    if not confirm:
        console.print("[yellow]Instalación cancelada por el usuario.[/]\n")
        raise SystemExit(1)

    try:
        install_packages(missing)
    except DependencyInstallationError as exc:
        console.print(f"[red]{exc}[/]\n")
        raise SystemExit(1) from exc

    console.print("[green]Dependencias instaladas correctamente.[/]\n")
