"""Backend comun de logging para aplicaciones construidas con clibaseapp."""

import logging
import os
import sys
from datetime import date
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from clibaseapp.core.config import ConfigManager

_LEVEL_NAMES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _coerce_level(value: int | str | None, fallback: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _LEVEL_NAMES.get(value.strip().upper(), fallback)
    return fallback


def _resolve_level(
    config: ConfigManager | None,
    *,
    key: str,
    env_var: str,
    fallback: int,
) -> int:
    env_value = os.getenv(env_var)
    if env_value:
        return _coerce_level(env_value, fallback)
    if config is not None:
        return _coerce_level(config.get(key, fallback), fallback)
    return fallback


def setup_logger(
    app_name: str,
    app_dir: Path,
    level: int = logging.WARNING,
    config: ConfigManager | None = None,
) -> logging.Logger:
    """Configura y devuelve el logger de la aplicacion."""

    log_dir = app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{date.today()}.log"
    file_level = _resolve_level(
        config,
        key="log_level",
        env_var="CLIBASEAPP_LOG_LEVEL",
        fallback=level,
    )
    console_level = _resolve_level(
        config,
        key="console_log_level",
        env_var="CLIBASEAPP_CONSOLE_LOG_LEVEL",
        fallback=logging.ERROR,
    )

    logger = logging.getLogger(app_name)
    logger.setLevel(min(file_level, console_level))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d.log"
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(app_name: str) -> logging.Logger:
    """Recupera el logger previamente configurado."""

    return logging.getLogger(app_name)
