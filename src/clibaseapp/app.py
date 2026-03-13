"""
Clase maestra del framework para crear utilidades CLI interactivas.

`CLIBaseApp` centraliza configuración, documentación, checks básicos y el
menú principal para que las apps hijas solo aporten su lógica de dominio.
"""

import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
import shutil

import questionary
import typer
from rich.console import Console

from clibaseapp.core.config import ConfigManager
from clibaseapp.core.updater import check_for_updates
from clibaseapp.exceptions import CLIAppError, ConfigurationError
from clibaseapp.models import DoctorResult
from clibaseapp.services.doctor_service import DoctorService
from clibaseapp.ui.components import (
    clear_screen, console, pause, render_doctor_result,
    show_header, show_info, show_success, show_warning,
)
from clibaseapp.ui.doc_viewer import show_docs


class CLIBaseApp:
    """Clase base de la que deben heredar todas las aplicaciones CLI interactivas.

    El padre proporciona automáticamente los siguientes servicios del menú:
    - 🩺 Doctor (diagnóstico de binarios y paths)
    - ⚙️ Configuración
    - 📖 Documentación
    - 🔄 Actualizar App (vía Git si la instalación lo soporta)
    - ❌ Salir

    La app hija solo añade sus opciones de negocio en `setup_commands()`.
    """

    def __init__(self, app_name: str, description: str):
        """Inicializa el framework base y la configuración común de la app hija."""

        # Fix Unicode/Emojis en consolas Windows (cmd)
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

        # Almacén de opciones de menú
        self.menu_options: List[dict] = []

        # Binarios que el doctor verificará
        self._doctor_binaries: List[str] = []

        # Paths que el doctor verificará {nombre: Path}
        self._doctor_paths: Dict[str, Path] = {}

        # Extensiones de archivo para el navegador (None = todos)
        self._file_extensions: Optional[Set[str]] = None
        self._file_icon: str = "📄"

        # Directorio raíz de la app hija (para doc_viewer)
        self._app_dir: Path = Path.cwd()

        # Registrar callback de Typer
        self.cli.callback(invoke_without_command=True)(self._main_callback)

    def require_binaries(self, binaries: List[str]) -> None:
        """Registra binarios para verificar con el doctor y falla si faltan al arrancar."""
        self._doctor_binaries.extend(binaries)
        for binary in binaries:
            if shutil.which(binary) is None:
                self.console.print(
                    f"[bold red]Error Crítico:[/] El binario obligatorio '{binary}' "
                    "no está instalado en el PATH del sistema."
                )
                sys.exit(1)

    def register_menu_option(self, title: str, value: str, callback: Callable) -> None:
        """Añade una opción de negocio al menú interactivo."""
        self.menu_options.append({
            "title": title,
            "value": value,
            "callback": callback,
        })

    # ── Acciones por defecto del framework ────────────────────────

    def _run_doctor(self) -> None:
        """Diagnóstico del sistema."""
        doctor = DoctorService()
        result = doctor.run_diagnosis(
            binaries=self._doctor_binaries or ["git"],
            paths=self._doctor_paths or {},
        )
        render_doctor_result(result)

    def _run_config(self) -> None:
        """Editor de configuración interactivo genérico."""
        clear_screen()
        show_header(f"Configuración de {self.app_name}", "Inicio > Configuración", icon="⚙️")
        show_info(f"Archivo: {self.config.config_file}")

        config_data = self.config.read_all()
        if not config_data:
            show_warning("La configuración está vacía.")
            return

        # Listar claves editables
        keys = list(config_data.keys())
        choices = [f"📝 {k}: {config_data[k]}" for k in keys]
        choices.append("❌ Volver")

        selection = questionary.select("¿Qué clave deseas editar?", choices=choices).ask()

        if selection is None or selection == "❌ Volver":
            show_info("Saliendo sin cambios.")
            return

        # Extraer clave
        selected_key = keys[choices.index(selection)]
        current_value = config_data[selected_key]

        new_value = questionary.text(
            f"Nuevo valor para '{selected_key}':",
            default=str(current_value) if not isinstance(current_value, list) else ", ".join(current_value),
        ).ask()

        if new_value is not None:
            # Si el valor original era una lista, parsear como lista
            if isinstance(current_value, list):
                parsed = [v.strip() for v in new_value.split(",") if v.strip()]
                self.config.update(selected_key, parsed)
            else:
                self.config.update(selected_key, new_value)
            show_success(f"'{selected_key}' actualizado correctamente.")

    def _run_docs(self) -> None:
        """Visor de documentación."""
        show_docs(self._app_dir)

    def _run_update(self) -> None:
        """Actualizador vía Git si la instalación lo soporta."""
        entrypoint = sys.modules["__main__"].__file__
        check_for_updates(entrypoint)

    # ── Motor del menú ────────────────────────────────────────────

    def _register_default_commands(self) -> None:
        """Registra las opciones por defecto del framework DESPUÉS de las del hijo."""
        self.register_menu_option("🩺 Diagnóstico (doctor)", "doctor", self._run_doctor)
        self.register_menu_option("⚙️ Configuración (config)", "config", self._run_config)
        self.register_menu_option("📖 Documentación (docs)", "docs", self._run_docs)
        self.register_menu_option("🔄 Actualizar App (update)", "update", self._run_update)

    def _main_callback(self, ctx: typer.Context) -> None:
        """Callback de Typer que atrapa ejecución sin subcomando."""
        if ctx.invoked_subcommand is None:
            self._interactive_main_menu()

    def _interactive_main_menu(self) -> None:
        """Bucle interactivo del menú principal.

        La ejecución de callbacks del hijo queda encapsulada aquí para que
        el manejo de cancelaciones y pausas sea uniforme en todas las apps.
        """
        while True:
            clear_screen()
            show_header(self.description, "Inicio", icon="⚡")

            choices = [
                questionary.Choice(opt["title"], value=opt["value"])
                for opt in self.menu_options
            ]
            choices.append(questionary.Choice("❌ Salir", value="exit"))

            choice = questionary.select("Selecciona una opción:", choices=choices).ask()

            if choice == "exit" or choice is None:
                show_info("¡Hasta la próxima!")
                break

            for opt in self.menu_options:
                if opt["value"] == choice:
                    try:
                        opt["callback"]()
                        pause()
                    except KeyboardInterrupt:
                        show_info("\nAcción cancelada.")
                        pause()

    # ── Métodos para el hijo ──────────────────────────────────────

    def setup_commands(self) -> None:
        """Método que sobrescriben los hijos para registrar sus opciones de negocio."""
        pass

    def run(self) -> None:
        """Punto de entrada principal."""
        try:
            self.setup_commands()
            self._register_default_commands()
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
