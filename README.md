# CLI Base App Framework

Framework reutilizable de Python para construir interfaces de línea de comandos modernas e interactivas utilizando `Typer`, `Rich`, y `Questionary`.

## Instalación

```bash
# Desde un repositorio local hermano
pip install -e ../clibaseapp

# Desde GitHub
pip install git+https://github.com/tu-usuario/clibaseapp.git
```

## Uso Básico

```python
from clibaseapp import CLIBaseApp, BrowserMenu, show_success, clear_screen, show_header

class MiApp(CLIBaseApp):
    def __init__(self):
        super().__init__(app_name="mi-app", description="Mi Herramienta CLI")

    def setup_commands(self):
        self.register_menu_option("📁 Navegar", "browse", self.navegar)
        self.register_menu_option("🧪 Test", "test", self.test)
    
    def navegar(self):
        browser = BrowserMenu(file_extensions={".txt", ".csv"}, file_icon="📄")
        result = browser.browse(Path.cwd())
    
    def test(self):
        clear_screen()
        show_header("Mi Comando", icon="🔧")
        show_success("¡Funciona!")

if __name__ == "__main__":
    MiApp().run()
```

## Estructura del Paquete

```
src/clibaseapp/
├── __init__.py          # API pública re-exportada
├── app.py               # CLIBaseApp — clase maestra heredable
├── exceptions.py        # Excepciones base del framework
├── models.py            # BrowseResult y modelos genéricos
├── core/
│   ├── config.py        # ConfigManager (XDG config.json)
│   └── updater.py       # Auto-actualización via git pull
└── ui/
    ├── browser.py       # BrowserMenu — navegador de directorios
    ├── components.py    # Motor gráfico Rich (headers, tablas, etc.)
    ├── menus.py         # BaseMenu abstracto (Questionary)
    └── theme.py         # Tema de colores compartido
```

## Qué Hereda una App Hija Automáticamente

- Menú interactivo principal con bucle infinito
- Clear screen + pause entre pantallas
- Gestión de configuración (`~/.config/<app_name>/config.json`)
- Navegador genérico de directorios
- Auto-actualización via `git pull` + reinicio
- Try/Catch global de excepciones
- Verificación de binarios del sistema (`require_binaries()`)
- Fix automático de Unicode/Emojis en consolas Windows
