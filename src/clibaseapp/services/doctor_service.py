"""
Servicio genérico de diagnóstico del sistema.
"""

import shutil
from pathlib import Path
from typing import Dict, List

from clibaseapp.models import DoctorCheck, DoctorResult


class DoctorService:
    """Diagnóstico genérico: verifica binarios y paths del sistema."""

    def run_diagnosis(
        self,
        binaries: List[str],
        paths: Dict[str, Path] | None = None,
    ) -> DoctorResult:
        """Ejecuta un diagnóstico completo.

        Args:
            binaries: Lista de nombres de ejecutables a verificar (ej: ["git", "ffmpeg"]).
            paths: Diccionario nombre → Path a verificar existencia (ej: {"media_root": Path(...)}).

        Returns:
            DoctorResult con checks de binarios y paths.
        """
        checks = [
            DoctorCheck(name=binary, available=bool(shutil.which(binary)))
            for binary in binaries
        ]

        verified_paths = {}
        if paths:
            for name, path in paths.items():
                p = Path(path) if not isinstance(path, Path) else path
                verified_paths[name] = (p, p.exists())

        return DoctorResult(checks=checks, paths=verified_paths)
