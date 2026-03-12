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
    """Clase base para todos los menús genéricos intergenerable."""

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
