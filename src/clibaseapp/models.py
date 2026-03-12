"""
Modelos de datos genéricos del framework.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class BrowseResult:
    """Resultado genérico de una navegación por directorios."""
    selected_path: Path
    selection_type: str  # "file" | "directory"


@dataclass
class DoctorCheck:
    """Estado de una dependencia o recurso del sistema."""
    name: str
    available: bool


@dataclass
class DoctorResult:
    """Resultado del diagnóstico genérico del sistema."""
    checks: List[DoctorCheck]
    paths: dict = field(default_factory=dict)  # nombre → (Path, exists)
