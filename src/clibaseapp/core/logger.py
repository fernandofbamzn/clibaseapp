"""
Gestor de logs centralizado para el framework clibaseapp.

Crea automáticamente la carpeta `logs/` en la raíz de la aplicación y genera
un fichero de log por día, con rotación automática. Se integra en `CLIBaseApp`
para capturar excepciones no controladas y errores del ciclo de vida de la app.
"""

import logging
import sys
from datetime import date
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(
    app_name: str,
    app_dir: Path,
    level: int = logging.WARNING,
) -> logging.Logger:
    """Configura y devuelve el logger de la aplicación.

    Crea `<app_dir>/logs/YYYY-MM-DD.log` y rota cada medianoche.
    Los mensajes también aparecen en stderr si el nivel es ERROR o superior.

    Args:
        app_name: Nombre de la aplicación (usado como nombre del logger).
        app_dir: Directorio raíz de la aplicación (donde se crea `logs/`).
        level: Nivel de log mínimo (por defecto WARNING).

    Returns:
        Logger configurado listo para usar.
    """
    log_dir = app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{date.today()}.log"

    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Evitar duplicar handlers si el logger ya fue configurado
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de fichero con rotación diaria (mantiene 30 días de histórico)
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d.log"
    logger.addHandler(file_handler)

    # Handler de consola para errores críticos (ERROR+)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(app_name: str) -> logging.Logger:
    """Recupera el logger ya configurado por setup_logger().

    Útil para obtener el logger desde servicios sin pasar la referencia
    explícitamente por toda la jerarquía de objetos.

    Args:
        app_name: Nombre de la aplicación (mismo que se usó en setup_logger).

    Returns:
        Logger del módulo de logging de Python estándar.
    """
    return logging.getLogger(app_name)
