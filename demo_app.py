"""
Demo de integración: valida que el framework funciona como padre heredable.
"""

from clibaseapp import CLIBaseApp, BrowserMenu, show_success, clear_screen, show_header, show_info
from pathlib import Path


class DemoApp(CLIBaseApp):
    """Aplicación de prueba para validar que el framework funciona."""

    def __init__(self):
        super().__init__(
            app_name="demo-cli",
            description="Aplicación de Demo del Framework"
        )

    def run_tests(self):
        clear_screen()
        show_header("Probando Lógica Hija", icon="🧪")
        show_success("¡La lógica ejecutada desde la hija hereda correctamente la UI!")

    def run_browse(self):
        clear_screen()
        show_header("Navegador de Archivos", icon="📁")
        browser = BrowserMenu(file_extensions={".txt", ".py", ".md"}, file_icon="📝")
        result = browser.browse(Path.cwd())
        if result:
            show_info(f"Seleccionado: {result.selected_path} ({result.selection_type})")
        else:
            show_info("Navegación cancelada.")

    def setup_commands(self) -> None:
        self.register_menu_option("🧪 Ejecutar Test de Integración", "test", self.run_tests)
        self.register_menu_option("📁 Navegar Archivos", "browse", self.run_browse)


if __name__ == "__main__":
    app = DemoApp()
    app.run()
