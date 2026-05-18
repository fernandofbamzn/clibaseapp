"""
Demo de integración: valida que el framework funciona como padre heredable.
"""

from pathlib import Path

import questionary

from clibaseapp import (
    BrowserMenu,
    CLIBaseApp,
    build_pdf_from_latex,
    clear_screen,
    show_header,
    show_info,
    show_success,
    show_warning,
)


class DemoApp(CLIBaseApp):
    """Aplicación de prueba para validar que el framework funciona."""

    def __init__(self) -> None:
        """Inicializa una app mínima que demuestra herencia y navegación."""

        super().__init__(app_name="demo-cli", description="Aplicación de Demo del Framework")
        self._doctor_binaries.extend(["pdflatex"])
        self.require_binaries(["pdflatex"])

    def run_tests(self) -> None:
        """Muestra una acción simple de negocio sobre el framework."""

        clear_screen()
        show_header("Probando Lógica Hija", icon="🧪")
        show_success("¡La lógica ejecutada desde la hija hereda correctamente la UI!")

    def run_browse(self) -> None:
        """Ejecuta el navegador genérico del framework sobre el cwd."""

        clear_screen()
        show_header("Navegador de Archivos", icon="📁")
        browser = BrowserMenu(file_extensions={".txt", ".py", ".md", ".tex"}, file_icon="📝")
        result = browser.browse(Path.cwd())
        if result:
            show_info(f"Seleccionado: {result.selected_path} ({result.selection_type})")
        else:
            show_info("Navegación cancelada.")

    def run_build_pdf(self) -> None:
        """Solicita un .tex y compila un PDF local usando pdflatex."""

        clear_screen()
        show_header("Generador PDF desde LaTeX", icon="📄")

        tex_input = questionary.text("Ruta al fichero .tex:", default=str(Path.cwd() / "main.tex")).ask()
        if not tex_input:
            show_warning("Operación cancelada: no se indicó archivo .tex.")
            return

        output_input = questionary.text(
            "Carpeta de salida (vacío = misma carpeta del .tex):",
            default="",
        ).ask()

        output_dir = Path(output_input).expanduser() if output_input else None
        result = build_pdf_from_latex(tex_input, output_dir=output_dir, app_name=self.app_name)
        if result.success:
            show_success(result.message)
            return
        show_warning(result.message)

    def setup_commands(self) -> None:
        self.register_menu_option("🧪 Ejecutar Test de Integración", "test", self.run_tests)
        self.register_menu_option("📁 Navegar Archivos", "browse", self.run_browse)
        self.register_menu_option("📄 Compilar LaTeX a PDF", "latex_pdf", self.run_build_pdf)


if __name__ == "__main__":
    app = DemoApp()
    app.run()
