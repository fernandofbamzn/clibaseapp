"""Clase base del framework para utilidades CLI interactivas."""

import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
import shutil

import questionary
import typer
from rich.console import Console

from clibaseapp.core.config import ConfigManager
from clibaseapp.core.logger import setup_logger
from clibaseapp.core.updater import check_for_updates
from clibaseapp.exceptions import CLIAppError, ConfigurationError
from clibaseapp.models import MenuAction
from clibaseapp.services.doctor_service import DoctorService
from clibaseapp.ui.components import (
    clear_screen,
    pause,
    render_doctor_result,
    show_header,
    show_info,
    show_success,
    show_warning,
)
from clibaseapp.ui.doc_viewer import show_docs


class CLIBaseApp:
    """Clase base para aplicaciones CLI interactivas."""

    def __init__(self, app_name: str, description: str):
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        self.app_name = app_name
        self.description = description

        self.cli = typer.Typer(help=description)
        self.console = Console()
        self.config = ConfigManager(app_name=app_name)

        self.menu_actions: List[MenuAction] = []
        self._legacy_order = 100
        self._doctor_binaries: List[str] = []
        self._doctor_paths: Dict[str, Path] = {}
        self._file_extensions: Optional[Set[str]] = None
        self._file_icon: str = "📄"
        self._app_dir: Path = self._resolve_app_dir()

        self.logger = setup_logger(app_name=app_name, app_dir=self._app_dir, config=self.config)
        self.cli.callback(invoke_without_command=True)(self._main_callback)

    def _resolve_app_dir(self) -> Path:
        entrypoint = getattr(sys.modules.get("__main__"), "__file__", "")
        if entrypoint:
            resolved = Path(entrypoint).resolve()
            if "site-packages" not in resolved.parts:
                return resolved.parent
        return Path.cwd()

    def require_binaries(self, binaries: List[str]) -> None:
        """Registra binarios obligatorios."""

        self._doctor_binaries.extend(binaries)
        for binary in binaries:
            if shutil.which(binary) is None:
                self.console.print(
                    f"[bold red]Error Critico:[/] El binario obligatorio '{binary}' "
                    "no esta instalado en el PATH del sistema."
                )
                input("\nPresiona Enter para salir...")
                sys.exit(1)

    def register_menu_option(self, title: str, value: str, callback: Callable[[], None]) -> None:
        """Compatibilidad legacy para registrar opciones estaticas."""

        self._legacy_order += 10
        self.register_menu_action(
            MenuAction(
                id=value,
                title=title,
                handler=callback,
                order=self._legacy_order,
            )
        )

    def register_menu_action(self, action: MenuAction) -> None:
        """Registra una accion declarativa del menu."""

        self.menu_actions.append(action)
        self.menu_actions.sort(key=lambda item: (item.order, item.title.lower()))

    def _run_doctor(self) -> None:
        doctor = DoctorService()
        result = doctor.run_diagnosis(
            binaries=self._doctor_binaries or ["git"],
            paths=self._doctor_paths or {},
        )
        render_doctor_result(result)

    def _run_config(self) -> None:
        clear_screen()
        show_header(f"Configuracion de {self.app_name}", "Inicio > Configuracion", icon="⚙️")
        show_info(f"Archivo app: {self.config.config_file}")
        show_info(f"Archivo global: {self.config.global_config_file}")

        config_data = self.config.read_all(scope="merged")
        if not config_data:
            show_warning("La configuracion esta vacia.")
            return

        keys = list(config_data.keys())
        choices = [f"📝 {k}: {config_data[k]}" for k in keys]
        choices.append("❌ Volver")

        selection = questionary.select("¿Que clave deseas editar?", choices=choices).ask()
        if selection is None or selection == "❌ Volver":
            show_info("Saliendo sin cambios.")
            return

        selected_key = keys[choices.index(selection)]
        current_value = config_data[selected_key]

        scope_choice = questionary.select(
            "¿En que ambito quieres guardar el cambio?",
            choices=[
                questionary.Choice("App", value="app"),
                questionary.Choice("Global", value="global"),
            ],
        ).ask()
        if scope_choice is None:
            show_info("Saliendo sin cambios.")
            return

        new_value = questionary.text(
            f"Nuevo valor para '{selected_key}':",
            default=str(current_value) if not isinstance(current_value, list) else ", ".join(current_value),
        ).ask()

        if new_value is not None:
            if isinstance(current_value, list):
                parsed = [v.strip() for v in new_value.split(",") if v.strip()]
                self.config.update(selected_key, parsed, scope=scope_choice)
            else:
                self.config.update(selected_key, new_value, scope=scope_choice)
            show_success(f"'{selected_key}' actualizado correctamente.")

    def _run_docs(self) -> None:
        show_docs(self._app_dir)

    def _run_logs(self) -> None:
        while True:
            clear_screen()
            show_header("Visor de Logs", "Inicio > Logs", icon="📜")

            log_files = self._get_log_files()
            if not log_files:
                show_warning("No se encontraron archivos de log (.log) en el directorio de la app.")
                return

            choices = [f"📄 {log_file.name} ({log_file.parent.name})" for log_file in log_files]
            choices.append("🧹 Borrar todos los logs")
            choices.append("❌ Volver")

            selection = questionary.select("Elige un archivo de log:", choices=choices).ask()
            if selection is None or selection == "❌ Volver":
                return

            if selection == "🧹 Borrar todos los logs":
                if self._confirm_delete_all_logs(log_files):
                    show_success("Archivos de log borrados correctamente.")
                continue

            selected_file = log_files[choices.index(selection)]
            action = questionary.select(
                f"Accion para {selected_file.name}:",
                choices=["👁 Ver log", "🗑 Borrar log", "↩ Volver"],
            ).ask()

            if action is None or action == "↩ Volver":
                continue
            if action == "👁 Ver log":
                self._view_log_file(selected_file)
                continue
            if action == "🗑 Borrar log" and self._confirm_delete_log(selected_file):
                show_success(f"Log eliminado: {selected_file.name}")

    def _get_log_files(self) -> List[Path]:
        log_files = list(self._app_dir.glob("*.log")) + list(self._app_dir.glob("logs/*.log"))
        return sorted(log_files, key=lambda path: path.stat().st_mtime, reverse=True)

    def _view_log_file(self, log_file: Path) -> None:
        try:
            content = log_file.read_text(encoding="utf-8", errors="replace")
            pager = self.console.pager() if sys.stdout.isatty() else nullcontext()
            with pager:
                self.console.print(content)
        except Exception as exc:
            self.logger.warning("Error al leer el log '%s': %s", log_file, exc, exc_info=True)
            show_warning(f"Error al leer el log: {exc}")

    def _confirm_delete_log(self, log_file: Path) -> bool:
        confirm = questionary.confirm(
            f"¿Borrar el log '{log_file.name}'?",
            default=False,
        ).ask()
        if not confirm:
            return False
        return self._delete_log_file(log_file)

    def _confirm_delete_all_logs(self, log_files: List[Path]) -> bool:
        confirm = questionary.confirm(
            f"¿Borrar los {len(log_files)} archivo(s) de log?",
            default=False,
        ).ask()
        if not confirm:
            return False

        deleted_any = False
        for log_file in log_files:
            deleted_any = self._delete_log_file(log_file) or deleted_any
        return deleted_any

    def _delete_log_file(self, log_file: Path) -> bool:
        try:
            log_file.unlink()
            self.logger.info("Log eliminado manualmente: %s", log_file)
            return True
        except FileNotFoundError:
            self.logger.warning("El log ya no existe al intentar borrarlo: %s", log_file)
            show_warning(f"El archivo '{log_file.name}' ya no existe.")
            return False
        except OSError as exc:
            self.logger.warning("No se pudo borrar el log '%s': %s", log_file, exc, exc_info=True)
            show_warning(f"No se pudo borrar '{log_file.name}': {exc}")
            return False

    def _run_update(self) -> None:
        entrypoint = sys.modules["__main__"].__file__
        check_for_updates(entrypoint)

    def _register_default_commands(self) -> None:
        self.register_menu_action(MenuAction("doctor", "🩺 Diagnostico (doctor)", self._run_doctor, order=900))
        self.register_menu_action(MenuAction("config", "⚙️ Configuracion (config)", self._run_config, order=910))
        self.register_menu_action(MenuAction("logs", "📜 Visor de Logs (logs)", self._run_logs, order=920))
        self.register_menu_action(MenuAction("docs", "📖 Documentacion (docs)", self._run_docs, order=930))
        self.register_menu_action(MenuAction("update", "🔄 Actualizar App (update)", self._run_update, order=940))

    def _resolve_menu_action_title(self, action: MenuAction) -> str:
        title = action.title
        if action.status_suffix:
            suffix = action.status_suffix().strip()
            if suffix:
                title = f"{title} {suffix}"
        return title

    def _iter_visible_actions(self) -> List[MenuAction]:
        visible_actions: List[MenuAction] = []
        for action in self.menu_actions:
            if action.visible and not action.visible():
                continue
            visible_actions.append(action)
        return visible_actions

    def _main_callback(self, ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            self._interactive_main_menu()

    def _interactive_main_menu(self) -> None:
        while True:
            clear_screen()
            show_header(self.description, "Inicio", icon="⚡")

            visible_actions = self._iter_visible_actions()
            choices = []
            for action in visible_actions:
                disabled_reason = None
                if action.enabled and not action.enabled():
                    disabled_reason = "No disponible"
                choices.append(
                    questionary.Choice(
                        self._resolve_menu_action_title(action),
                        value=action.id,
                        disabled=disabled_reason,
                    )
                )
            choices.append(questionary.Choice("❌ Salir", value="exit"))

            choice = questionary.select("Selecciona una opcion:", choices=choices).ask()
            if choice == "exit" or choice is None:
                show_info("¡Hasta la proxima!")
                break

            for action in visible_actions:
                if action.id != choice:
                    continue
                try:
                    action.handler()
                    pause()
                except KeyboardInterrupt:
                    show_info("\nAccion cancelada.")
                    pause()
                break

    def setup_commands(self) -> None:
        pass

    def run(self) -> None:
        try:
            self.setup_commands()
            self._register_default_commands()
            self.cli()
        except ConfigurationError as exc:
            self.logger.error("Error de Configuracion: %s", exc, exc_info=True)
            self.console.print(f"[bold red]Error de Configuracion:[/] {exc}")
            sys.exit(2)
        except CLIAppError as exc:
            self.logger.error("Error del Framework: %s", exc, exc_info=True)
            self.console.print(f"[bold red]Error del Framework:[/] {exc}")
            sys.exit(3)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Aplicacion cerrada por el usuario[/]")
            sys.exit(0)
        except Exception as exc:
            self.logger.critical("Excepcion no controlada: %s", exc, exc_info=True)
            self.console.print(f"[bold red]Excepcion no controlada:[/] {exc}")
            sys.exit(1)
