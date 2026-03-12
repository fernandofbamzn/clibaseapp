# Crear una App Hija con clibaseapp

Guía paso a paso para usar el framework `clibaseapp` como base para una nueva aplicación CLI.

## 1. Estructura Mínima

```
mi-app/
├── main.py          # Entrypoint heredando de CLIBaseApp
├── services/        # Lógica de negocio
├── data/            # Acceso a datos
├── models/          # Schemas y modelos
├── ui/              # Renderers específicos
└── docs/            # Documentación .md
```

## 2. main.py Mínimo

```python
from clibaseapp import CLIBaseApp, check_and_install

class MiApp(CLIBaseApp):
    def __init__(self):
        super().__init__(app_name="mi-app", description="Mi Aplicación CLI")
        
        # Opcionales: binarios requeridos y paths para el doctor
        self.require_binaries(["git"])
        self._doctor_paths = {"data_dir": Path("/mis/datos")}
        self._app_dir = Path(__file__).parent.resolve()
        
        self.config.default_config = {
            "data_path": str(Path.cwd()),
            "language": "es"
        }

    def mi_accion(self):
        from clibaseapp import clear_screen, show_header, show_success
        clear_screen()
        show_header("Mi Acción", icon="🚀")
        show_success("¡Hecho!")

    def setup_commands(self):
        self.register_menu_option("🚀 Mi Acción", "action", self.mi_accion)

if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MiApp().run()
```

## 3. Lo que heredas automáticamente

| Función | Descripción |
|---------|------------|
| 🩺 Doctor | Verifica binarios y paths registrados |
| ⚙️ Config | Editor interactivo de `config.json` |
| 📖 Docs | Visor de `.md` del padre e hijo |
| 🔄 Update | `git pull` + reinicio automático |
| ❌ Salir | Cierre limpio |
| 🎨 UI | `show_header`, `show_info`, `show_success`, etc. |
| 📁 Browser | `BrowserMenu` para navegar directorios |
| 🔍 Scanner | `scan_files(root, extensions)` |
| 📝 Formatter | `fmt.info()`, `fmt.tag()`, etc. |
| ⚠️ Excepciones | Try/catch global + jerarquía de errores |

## 4. API Pública disponible

```python
from clibaseapp import (
    # Clase maestra
    CLIBaseApp,
    # Config
    ConfigManager,
    # Escáner
    scan_files, check_and_install,
    # Servicios
    DoctorService, BrowseService,
    # Modelos
    BrowseResult, DoctorCheck, DoctorResult,
    # UI
    BrowserMenu, BaseMenu, Formatter, fmt,
    clear_screen, console, pause, show_docs,
    show_header, show_info, show_success,
    show_warning, show_error,
    dict_table, render_doctor_result, render_browse_result,
    # Excepciones
    CLIAppError, ConfigurationError, BinaryMissingError,
    PermissionAccessError, ExternalToolError,
    DependencyInstallationError,
)
```

## 5. Tu app solo necesita

1. **`setup_commands()`** — Registrar opciones de menú de negocio
2. **Servicios** — Tu lógica en carpeta `services/`
3. **Renderers** — Si necesitas visualizaciones específicas, en `ui/`
4. **Schemas** — Modelos propios en `models/`
