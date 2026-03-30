"""Modelos de datos genericos del framework."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class BrowseResult:
    """Resultado generico de una navegacion por directorios."""

    selected_path: Path
    selection_type: str  # "file" | "directory"


@dataclass
class DoctorCheck:
    """Estado de una dependencia o recurso del sistema."""

    name: str
    available: bool


@dataclass
class DoctorResult:
    """Resultado del diagnostico generico del sistema."""

    checks: List[DoctorCheck]
    paths: dict = field(default_factory=dict)  # nombre -> (Path, exists)


MenuPredicate = Callable[[], bool]
MenuStatusResolver = Callable[[], str]


@dataclass
class MenuAction:
    """Accion declarativa del menu principal."""

    id: str
    title: str
    handler: Callable[[], None]
    order: int = 100
    visible: Optional[MenuPredicate] = None
    enabled: Optional[MenuPredicate] = None
    status_suffix: Optional[MenuStatusResolver] = None
