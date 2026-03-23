"""
CLI Base App Framework.
Framework reutilizable para construir interfaces CLI interactivas modernas.
"""

__version__ = "0.2.0"

# ── Clase maestra ──
from clibaseapp.app import CLIBaseApp

# ── Excepciones ──
from clibaseapp.exceptions import (
    BinaryMissingError,
    CLIAppError,
    ConfigurationError,
    DependencyInstallationError,
    ExternalToolError,
    InteractiveMenuError,
    PermissionAccessError,
)

# ── Modelos ──
from clibaseapp.models import BrowseResult, DoctorCheck, DoctorResult

# ── Core ──
from clibaseapp.core.config import ConfigManager
from clibaseapp.core.logger import get_logger, setup_logger
from clibaseapp.core.scanner import scan_files
from clibaseapp.core.dependency_check import check_and_install

# ── Servicios ──
from clibaseapp.services.doctor_service import DoctorService
from clibaseapp.services.browse_service import BrowseService, BrowseSelector
from clibaseapp.services.sshfs_service import mount_drive

# ── UI ──
from clibaseapp.ui.components import (
    clear_screen,
    console,
    dict_table,
    pause,
    render_browse_result,
    render_doctor_result,
    show_error,
    show_header,
    show_info,
    show_success,
    show_warning,
)
from clibaseapp.ui.browser import BrowserMenu
from clibaseapp.ui.menus import BaseMenu
from clibaseapp.ui.formatter import Formatter, fmt
from clibaseapp.ui.doc_viewer import show_docs

__all__ = [
    # Core
    "CLIBaseApp",
    "ConfigManager",
    "setup_logger",
    "get_logger",
    "scan_files",
    "check_and_install",
    # Exceptions
    "CLIAppError",
    "ConfigurationError",
    "BinaryMissingError",
    "InteractiveMenuError",
    "PermissionAccessError",
    "ExternalToolError",
    "DependencyInstallationError",
    # Models
    "BrowseResult",
    "DoctorCheck",
    "DoctorResult",
    # Services
    "DoctorService",
    "BrowseService",
    "BrowseSelector",
    "mount_drive",
    # UI
    "BrowserMenu",
    "BaseMenu",
    "Formatter",
    "fmt",
    "clear_screen",
    "console",
    "dict_table",
    "pause",
    "render_browse_result",
    "render_doctor_result",
    "show_docs",
    "show_error",
    "show_header",
    "show_info",
    "show_success",
    "show_warning",
]
