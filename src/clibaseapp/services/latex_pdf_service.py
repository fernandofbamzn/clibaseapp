"""Servicio para compilar archivos LaTeX a PDF de forma segura y reproducible."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from clibaseapp.core.logger import get_logger


@dataclass(frozen=True)
class PdfBuildResult:
    """Resultado de compilación LaTeX."""

    success: bool
    pdf_path: Path | None
    message: str


def build_pdf_from_latex(
    tex_file: Path | str,
    output_dir: Path | str | None = None,
    *,
    runs: int = 2,
    timeout_seconds: int = 120,
    app_name: str = "clibaseapp",
) -> PdfBuildResult:
    """Compila un fichero .tex a PDF usando ``pdflatex``.

    Se ejecuta con ``-interaction=nonstopmode`` y ``-halt-on-error`` para
    evitar prompts interactivos y fallar pronto en caso de error.
    """

    logger = get_logger(app_name)
    try:
        source = Path(tex_file).expanduser().resolve()
        if not source.exists() or not source.is_file():
            message = f"No existe el fichero LaTeX: {source}"
            logger.error(message)
            return PdfBuildResult(False, None, message)
        if source.suffix.lower() != ".tex":
            message = f"El fichero debe tener extensión .tex: {source.name}"
            logger.error(message)
            return PdfBuildResult(False, None, message)

        if shutil.which("pdflatex") is None:
            message = "No se encontró 'pdflatex' en el PATH. Instala TeX Live/MacTeX."
            logger.error(message)
            return PdfBuildResult(False, None, message)

        target_dir = Path(output_dir).expanduser().resolve() if output_dir else source.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={target_dir}",
            str(source),
        ]

        effective_runs = max(runs, 1)
        for run_number in range(1, effective_runs + 1):
            logger.info("Compilación LaTeX %s/%s: %s", run_number, effective_runs, source)
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                message = f"Timeout compilando {source.name}: {exc}"
                logger.error(message, exc_info=True)
                return PdfBuildResult(False, None, message)
            except OSError as exc:
                message = f"Error del sistema ejecutando pdflatex: {exc}"
                logger.error(message, exc_info=True)
                return PdfBuildResult(False, None, message)

            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                detail = stderr or stdout or f"Código de salida {result.returncode}"
                logger.error("Falló pdflatex para '%s': %s", source, detail)
                return PdfBuildResult(False, None, f"Error de compilación: {detail}")

        pdf_path = target_dir / f"{source.stem}.pdf"
        if not pdf_path.exists():
            message = f"La compilación terminó pero no se encontró el PDF: {pdf_path}"
            logger.error(message)
            return PdfBuildResult(False, None, message)

        message = f"PDF generado correctamente: {pdf_path}"
        logger.info(message)
        return PdfBuildResult(True, pdf_path, message)

    except Exception as exc:
        message = f"Error inesperado al compilar LaTeX: {exc}"
        logger.exception(message)
        return PdfBuildResult(False, None, message)
