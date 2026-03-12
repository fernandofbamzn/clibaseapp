"""
Navegador genérico de directorios y archivos por terminal.
Recibe opcionalmente un set de extensiones para filtrar ficheros.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple

from questionary import Choice

from clibaseapp.models import BrowseResult
from clibaseapp.ui.menus import BaseMenu

logger = logging.getLogger(__name__)


def list_entries(
    current: Path, file_extensions: Optional[Set[str]] = None
) -> Tuple[List[Path], List[Path]]:
    """Lista directorios y archivos (opcionalmente filtrados) visibles en una carpeta."""
    dirs: List[Path] = []
    files: List[Path] = []

    for item in sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if item.name.startswith("."):
            continue
        if item.is_dir():
            dirs.append(item)
        elif item.is_file():
            if file_extensions is None or item.suffix.lower() in file_extensions:
                files.append(item)

    return dirs, files


class BrowserMenu(BaseMenu):
    """Menú genérico de navegación por árbol de carpetas.
    
    Args:
        file_extensions: Set de extensiones a mostrar (ej: {".mkv", ".mp4"}).
                         Si es None, muestra todos los archivos.
        file_icon: Emoji representativo para los archivos listados.
    """

    def __init__(self, file_extensions: Optional[Set[str]] = None, file_icon: str = "📄"):
        self.file_extensions = file_extensions
        self.file_icon = file_icon

    def browse(self, root: Path) -> Optional[BrowseResult]:
        """Navega desde una raíz y permite elegir carpeta o archivo."""
        current = root.resolve()

        while True:
            breadcrumb = str(current)

            try:
                dirs, files = list_entries(current, self.file_extensions)
            except (PermissionError, FileNotFoundError, NotADirectoryError):
                logger.warning("No se pudo abrir la ruta de navegación: %s", current)
                choices: List[Choice] = []

                if current != root:
                    choices.append(Choice(title="⬅ Volver atrás", value=("up", current.parent)))

                choices.append(Choice(title="❌ Cancelar", value=("cancel", None)))

                result = self.ask_select(
                    message=(
                        f"Navegación > {breadcrumb}\n"
                        "No se pudo abrir esta ruta (permisos o ruta inválida)."
                    ),
                    choices=choices,
                )

                if result is None:
                    return None

                action, path = result

                if action == "up":
                    current = path
                    continue

                return None

            choices: List[Choice] = [
                Choice(
                    title=f"✅ Seleccionar esta carpeta: {current.name or str(current)}",
                    value=("select_dir", current),
                ),
            ]

            if current != root:
                choices.append(Choice(title="⬆ Subir un nivel", value=("up", current.parent)))

            for directory in dirs:
                choices.append(Choice(title=f"📁 {directory.name}", value=("enter", directory)))

            for file_path in files:
                choices.append(
                    Choice(title=f"{self.file_icon} {file_path.name}", value=("select_file", file_path))
                )

            choices.append(Choice(title="❌ Cancelar", value=("cancel", None)))

            selection = self.ask_select(
                message=f"Navegación > {breadcrumb}",
                choices=choices,
            )

            if selection is None:
                return None

            action, selected_path = selection

            if action == "select_dir" and selected_path is not None:
                return BrowseResult(selected_path=selected_path, selection_type="directory")

            if action == "select_file" and selected_path is not None:
                return BrowseResult(selected_path=selected_path, selection_type="file")

            if action == "up" and selected_path is not None:
                current = selected_path
                continue

            if action == "enter" and selected_path is not None:
                current = selected_path
                continue

            if action == "cancel":
                return None
