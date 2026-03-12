"""
Formateador de texto normalizado basado en el tema de la aplicación.
Centraliza el uso de Rich markup para garantizar coherencia visual.
"""

from clibaseapp.ui.theme import APP_THEME


class Formatter:
    """Genera cadenas de texto con formato Rich coherente con el tema."""

    @staticmethod
    def info(text: str) -> str:
        """Texto informativo."""
        return f"[info]ℹ {text}[/info]"

    @staticmethod
    def success(text: str) -> str:
        """Texto de éxito."""
        return f"[success]✔ {text}[/success]"

    @staticmethod
    def warning(text: str) -> str:
        """Texto de advertencia."""
        return f"[warning]⚠ {text}[/warning]"

    @staticmethod
    def error(text: str) -> str:
        """Texto de error crítico."""
        return f"[error]✖ {text}[/error]"

    @staticmethod
    def bold(text: str) -> str:
        """Texto en negrita."""
        return f"[bold]{text}[/bold]"

    @staticmethod
    def dim(text: str) -> str:
        """Texto atenuado."""
        return f"[dim]{text}[/dim]"

    @staticmethod
    def tag(text: str, style: str = "cyan") -> str:
        """Etiqueta coloreada (útil para idiomas, códecs, etc)."""
        return f"[{style}]{text}[/{style}]"

    @staticmethod
    def header_text(text: str) -> str:
        """Texto con estilo de encabezado."""
        return f"[header]{text}[/header]"

    @staticmethod
    def breadcrumb(text: str) -> str:
        """Texto de breadcrumb."""
        return f"[breadcrumb]📍 {text}[/breadcrumb]"


# Instancia global singleton para uso directo
fmt = Formatter()
