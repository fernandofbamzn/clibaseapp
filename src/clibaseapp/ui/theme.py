"""
Estilos base compartidos (Colores, Paneles).
"""

from rich.theme import Theme

APP_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "header": "bold cyan",
        "breadcrumb": "dim italic white",
    }
)
