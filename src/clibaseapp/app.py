"""
Clase maestra del Framework para crear utilidades CLI.
"""

import sys
from typing import Callable, List, Optional
import shutil

import questionary
import typer
from rich.console import Console

from clibaseapp.core.config import ConfigManager
from clibaseapp.core.updater import check_for_updates
from clibaseapp.exceptions import CLIAppError, ConfigurationError
from clibaseapp.ui.components import clear_screen, pause, show_header, show_info


class CLIBaseApp:
    """Clase base de la que deben heredar todas las aplicaciones CLI interactivas."""

    def __init__(self, app_name: str, description: str):
        # Aplicamos fix para renderizado de Emojis Unicode en consolas Windows (cmd)
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

        self.app_name = app_name
        self.description = description
        
        # Inicializa Typer
        self.cli = typer.Typer(help=description)
        self.console = Console()
        
        # Gestor de configuración
        self.config = ConfigManager(app_name=app_name)
        
        # Almacén temporal de opciones de menú
        self.menu_options: List[dict] = []
        
        # Registrar metadatos en el propio CLI para auto-inyección
        self.cli.callback(invoke_without_command=True)(self._main_callback)
        
        # El dev hijo debe llamar a este método explícito tras init.
        # self.setup_commands() 
        # self.register_default_commands()

    def register_default_commands(self) -> None:
        """Registra los comandos y opciones que forman parte del esqueleto de cualquier app."""
        # Se inyecta auto-actualización si el desarrollador decide incluirlo.
        self.register_menu_option("🔄 Actualizar App (update)", "update", self._run_update)

    def register_menu_option(self, title: str, value: str, callback: Callable) -> None:
        """Añade una opción principal al bucle interactivo de esta aplicación."""
        self.menu_options.append({
            "title": title,
            "value": value,
            "callback": callback
        })

    def require_binaries(self, binaries: List[str]) -> None:
        """Verifica que los ejecutables especificados existan en el sistema ANTES de arrancar."""
        for binary in binaries:
            if shutil.which(binary) is None:
                self.console.print(f"[bold red]Error Crítico:[/] El binario obligatorio '{binary}' no está instalado en el PATH del sistema.")
                sys.exit(1)

    def _run_update(self) -> None:
        """Ejecuta el actualizador referenciando el binario del padre."""
        entrypoint = sys.modules["__main__"].__file__
        check_for_updates(entrypoint)

    def _main_callback(self, ctx: typer.Context) -> None:
        """Callback silencioso de Typer que atrapa la ejecución sin submando."""
        if ctx.invoked_subcommand is None:
            self._interactive_main_menu()

    def _interactive_main_menu(self) -> None:
        """Motor del bucle infinito interactivo gráfico principal."""
        
        # Añade la salida por defecto.
        choices = [
            questionary.Choice(opt["title"], value=opt["value"])
            for opt in self.menu_options
        ]
        choices.append(questionary.Choice("❌ Salir", value="exit"))

        while True:
            clear_screen()
            show_header(self.description, "Inicio", icon="⚡")

            choice = questionary.select(
                "Selecciona una opción:",
                choices=choices
            ).ask()

            if choice == "exit" or choice is None:
                show_info("¡Hasta la próxima!")
                break
                
            # Busca en la piscina de opciones el callback y lo ejecuta protegido
            for opt in self.menu_options:
                if opt["value"] == choice:
                    try:
                        opt["callback"]()
                        pause()
                    except KeyboardInterrupt:
                        show_info("\nAcción cancelada de forma forzosa.")
                        pause()

    def setup_commands(self) -> None:
        """Método abstracto que deben sobrescribir los hijos para añadir Typer commands y rutas."""
        pass

    def run(self) -> None:
        """Entrypoint arrancable."""
        try:
            self.setup_commands()
            self.register_default_commands()
            self.cli()
        except ConfigurationError as exc:
            self.console.print(f"[bold red]Error de Configuración:[/] {exc}")
            sys.exit(2)
        except CLIAppError as exc:
            self.console.print(f"[bold red]Error del Framework:[/] {exc}")
            sys.exit(3)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Aplicación cerrada por el usuario[/]")
            sys.exit(0)
        except Exception as exc:
            self.console.print(f"[bold red]Excepción no controlada:[/] {exc}")
            sys.exit(1)
