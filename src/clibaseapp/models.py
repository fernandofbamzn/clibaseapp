"""
Modelos de datos genéricos del framework.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BrowseResult:
    """Resultado genérico de una navegación por directorios."""
    selected_path: Path
    selection_type: str  # "file" | "directory"
