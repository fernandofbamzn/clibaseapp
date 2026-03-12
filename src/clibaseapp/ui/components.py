"""
Componentes compartidos de la interfaz de usuario con Rich. Engine gráfico genérico.
"""

from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clibaseapp.models import BrowseResult, DoctorResult
from clibaseapp.ui.theme import APP_THEME

console = Console(theme=APP_THEME)


def clear_screen() -> None:
    """Limpia la terminal."""
    console.clear()


def pause() -> None:
    """Pausa la ejecución hasta que el usuario pulse Enter."""
    console.print()
    console.print("[dim]Pulsar Enter para continuar...[/dim]", end="")
    input()
    console.print()


def show_header(title: str, breadcrumb: str = "", icon: str = "") -> None:
    """Renderiza encabezado principal con breadcrumb e icono opcional."""
    if breadcrumb:
        console.print(f"[breadcrumb]📍 {breadcrumb}[/breadcrumb]")

    title_text = f"{icon} {title}" if icon else title
    console.print(Panel(f"[header]{title_text}[/header]", border_style="cyan", padding=(1, 2), expand=False))


def show_info(text: str) -> None:
    """Muestra un mensaje informativo."""
    console.print(f"[info]ℹ[/info] {text}")


def show_success(text: str) -> None:
    """Muestra un mensaje de éxito."""
    console.print(f"[success]✔[/success] {text}")


def show_warning(text: str) -> None:
    """Muestra un aviso o advertencia."""
    console.print(f"[warning]⚠[/warning] {text}")


def show_error(text: str) -> None:
    """Muestra un error crítico."""
    console.print(f"[error]✖[/error] {text}")


def dict_table(title: str, values: Dict[str, int], key_label: str, value_label: str) -> Table:
    """Construye una tabla Rich estandarizada a partir de un diccionario."""
    table = Table(title=f"📊 [bold]{title}[/bold]", show_lines=True, header_style="bold cyan", expand=True)
    table.add_column(key_label, style="cyan", justify="left")
    table.add_column(value_label, justify="right", style="green", width=15)

    for key, value in sorted(values.items(), key=lambda x: (-x[1], x[0])):
        table.add_row(str(key), str(value))

    return table


# ── Renderizadores genéricos ──────────────────────────────────────

def render_doctor_result(result: DoctorResult) -> None:
    """Renderiza el diagnóstico genérico del sistema."""
    clear_screen()
    show_header("Diagnóstico del Sistema", "Inicio > Doctor", icon="🩺")

    for check in result.checks:
        if check.available:
            show_success(f"{check.name} encontrado")
        else:
            show_error(f"{check.name} NO encontrado")

    for name, (path, exists) in result.paths.items():
        if exists:
            show_success(f"{name}: {path}")
        else:
            show_warning(f"{name}: {path} (no existe)")


def render_browse_result(result: BrowseResult | None) -> None:
    """Renderiza el resultado de una navegación genérica."""
    clear_screen()
    show_header("Navegador de Archivos", "Inicio > Navegación", icon="📁")
    if result is None:
        show_warning("Navegación cancelada.")
        return
    show_success(f"Seleccionado: {result.selected_path}")
    show_info(f"Tipo de selección: {result.selection_type}")
