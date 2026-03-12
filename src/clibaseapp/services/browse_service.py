"""
Servicio genérico de navegación de directorios desacoplado de la UI.
"""

from pathlib import Path
from typing import Optional, Protocol

from clibaseapp.models import BrowseResult


class BrowseSelector(Protocol):
    """Protocolo para la capa de UI que resuelve navegación."""

    def browse(self, root: Path) -> Optional[BrowseResult]:
        """Resuelve una selección de archivo o carpeta."""


class BrowseService:
    """Lógica de navegación sin dependencias de UI."""

    def browse(self, root: Path, selector: BrowseSelector) -> Optional[BrowseResult]:
        """Delega la selección al adaptador recibido por inversión de dependencias."""
        return selector.browse(root)
