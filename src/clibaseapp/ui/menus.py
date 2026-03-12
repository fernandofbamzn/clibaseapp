"""
Menús base interactivos abstractos con Questionary.
"""

import logging
from typing import List, Optional, Tuple

import questionary
from questionary import Choice

MenuSelection = Tuple[str, Optional[any]]

logger = logging.getLogger(__name__)


class BaseMenu:
    """Clase base para todos los menús genéricos."""

    def ask_select(
        self,
        message: str,
        choices: List[Choice],
    ) -> Optional[MenuSelection]:
        """Lanza un selector interactivo base de tipo list."""
        return questionary.select(
            message,
            choices=choices,
            use_shortcuts=False,
            instruction="Usa flechas, Enter para elegir",
        ).ask()

    def ask_checkbox(
        self,
        message: str,
        choices: List[Choice],
    ) -> Optional[List]:
        """Lanza un checklist interactivo (multi-selección con espaciador)."""
        return questionary.checkbox(
            message,
            choices=choices,
            style=questionary.Style([
                ('highlighted', 'fg:cyan bold'),
                ('selected', 'fg:green bold'),
            ]),
        ).ask()

    def ask_confirm(
        self,
        message: str,
        default: bool = True,
    ) -> Optional[bool]:
        """Lanza una confirmación sí/no."""
        return questionary.confirm(message, default=default).ask()

    def ask_text(
        self,
        message: str,
        default: str = "",
    ) -> Optional[str]:
        """Lanza un input de texto libre."""
        return questionary.text(message, default=default).ask()

    def ask_path(
        self,
        message: str,
        default: str = "",
    ) -> Optional[str]:
        """Lanza un input de ruta con autocompletado."""
        return questionary.path(message, default=default).ask()
