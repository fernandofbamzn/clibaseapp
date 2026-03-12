"""
Visor interactivo de documentación Markdown.
Escanea archivos .md del proyecto padre y del hijo, y permite seleccionar cuál leer.
"""

import logging
from pathlib import Path
from typing import List, Optional

import questionary
from questionary import Choice
from rich.markdown import Markdown

from clibaseapp.ui.components import clear_screen, console, pause, show_header, show_warning

logger = logging.getLogger(__name__)


def _find_markdown_files(*dirs: Path) -> List[Path]:
    """Busca archivos .md en los directorios proporcionados."""
    files: List[Path] = []
    for d in dirs:
        if d.exists() and d.is_dir():
            files.extend(sorted(d.glob("*.md")))
            docs_sub = d / "docs"
            if docs_sub.exists():
                files.extend(sorted(docs_sub.glob("*.md")))
    return files


def show_docs(*extra_dirs: Path, framework_dir: Optional[Path] = None) -> None:
    """Muestra un menú interactivo para seleccionar y leer documentos .md.

    Args:
        *extra_dirs: Directorios adicionales de la app hija donde buscar .md.
        framework_dir: Directorio raíz del framework (si no se pasa, usa el propio paquete).
    """
    clear_screen()
    show_header("Documentación del Proyecto", icon="📖")

    # Directorio del framework
    if framework_dir is None:
        framework_dir = Path(__file__).parent.parent.parent.parent  # raíz del paquete clibaseapp

    search_dirs = [framework_dir] + list(extra_dirs)
    all_files = _find_markdown_files(*search_dirs)

    if not all_files:
        show_warning("No se encontraron documentos .md en los directorios del proyecto.")
        return

    # Construir choices
    choices: List[Choice] = []
    for f in all_files:
        label = f"📄 {f.relative_to(f.parent.parent) if len(f.parts) > 2 else f.name}"
        choices.append(Choice(title=label, value=str(f)))
    choices.append(Choice(title="❌ Volver", value="cancel"))

    selection = questionary.select(
        "Selecciona un documento para leer:",
        choices=choices,
    ).ask()

    if selection == "cancel" or selection is None:
        return

    # Renderizar
    selected_path = Path(selection)
    clear_screen()
    show_header(selected_path.name, icon="📄")

    try:
        content = selected_path.read_text(encoding="utf-8")
        console.print(Markdown(content))
    except Exception as exc:
        show_warning(f"Error al leer '{selected_path.name}': {exc}")
