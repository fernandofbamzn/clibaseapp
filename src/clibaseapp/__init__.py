"""
CLI Base App Framework.
Framework reutilizable para construir interfaces CLI interactivas modernas.
"""

__version__ = "0.1.0"

from clibaseapp.app import CLIBaseApp
from clibaseapp.exceptions import CLIAppError, ConfigurationError, BinaryMissingError
from clibaseapp.models import BrowseResult
from clibaseapp.core.config import ConfigManager
from clibaseapp.ui.components import (
    clear_screen,
    console,
    dict_table,
    pause,
    show_error,
    show_header,
    show_info,
    show_success,
    show_warning,
)
from clibaseapp.ui.browser import BrowserMenu
from clibaseapp.ui.menus import BaseMenu

__all__ = [
    "CLIBaseApp",
    "CLIAppError",
    "ConfigurationError",
    "BinaryMissingError",
    "BrowseResult",
    "ConfigManager",
    "BrowserMenu",
    "BaseMenu",
    "clear_screen",
    "console",
    "dict_table",
    "pause",
    "show_error",
    "show_header",
    "show_info",
    "show_success",
    "show_warning",
]
