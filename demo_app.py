import sys
from clibaseapp.app import CLIBaseApp
from clibaseapp.ui.components import show_success, clear_screen, show_header


class DemoApp(CLIBaseApp):
    """Aplicación de prueba para validar que el framweork funciona."""
    
    def __init__(self):
        super().__init__(
            app_name="demo-cli", 
            description="Aplicación de Demo del Nuevo Framework"
        )
    
    def run_tests(self):
        clear_screen()
        show_header("Probando Lógica Hija", icon="🧪")
        show_success("¡La lógica ejecutada desde la hija hereda correctamente la UI!")
        
    def setup_commands(self) -> None:
        """Aquí añadiremos los comandos de Typer si quisieramos."""
        
        # Registrar una opción nativa en el loop infinito del framrwork
        self.register_menu_option("🧪 Ejecutar Test de Integración", "test", self.run_tests)


if __name__ == "__main__":
    app = DemoApp()
    app.run()
