import logging
import uuid
from datetime import date
from pathlib import Path

from clibaseapp.core.logger import setup_logger


def _emit_test_log(logger: logging.Logger) -> None:
    logger.warning("mensaje de prueba")


def test_setup_logger_includes_filename_function_and_line(tmp_path: Path) -> None:
    app_name = f"logger-test-{uuid.uuid4().hex}"
    logger = setup_logger(app_name=app_name, app_dir=tmp_path, level=logging.INFO)

    _emit_test_log(logger)

    for handler in logger.handlers:
        handler.flush()

    log_file = tmp_path / "logs" / f"{date.today()}.log"
    content = log_file.read_text(encoding="utf-8")

    assert "[WARNING]" in content
    assert app_name in content
    assert "test_logger.py:_emit_test_log:" in content
    assert "mensaje de prueba" in content
