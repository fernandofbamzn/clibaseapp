"""
Escáner genérico recursivo de archivos por extensiones.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set

from clibaseapp.exceptions import PermissionAccessError

logger = logging.getLogger(__name__)


def scan_files(root: Path, extensions: Optional[Set[str]] = None) -> List[Path]:
    """Escanea recursivamente archivos cuya extensión coincida con el set proporcionado.

    Args:
        root: Directorio raíz desde el que escanear.
        extensions: Set de extensiones (ej: {".mkv", ".mp4"}). Si es None, devuelve todos los archivos.

    Returns:
        Lista de Paths ordenados.
    """
    files: List[Path] = []

    try:
        for path in root.rglob("*"):
            if path.is_file():
                if extensions is None or path.suffix.lower() in extensions:
                    files.append(path)
    except PermissionError as exc:
        logger.exception("Permiso denegado al escanear la ruta: %s", root)
        raise PermissionAccessError(f"Permiso denegado al escanear la ruta: {root}") from exc

    return sorted(files)
