# CLI Base App Framework

Framework reutilizable de Python para construir aplicaciones CLI interactivas con menús, configuración, y diagnósticos integrados.

## Instalación

```bash
pip install -e ../clibaseapp     # Desde proyecto hermano
pip install git+https://...      # Desde GitHub
```

## Uso Rápido

```python
from clibaseapp import CLIBaseApp, check_and_install

class MiApp(CLIBaseApp):
    def __init__(self):
        super().__init__(app_name="mi-app", description="Mi App")
        self.require_binaries(["git"])
    
    def mi_accion(self):
        from clibaseapp import show_success
        show_success("¡Funciona!")
    
    def setup_commands(self):
        self.register_menu_option("🚀 Mi Acción", "action", self.mi_accion)

if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MiApp().run()
```

## Menú por Defecto (automático)

Toda app hija incluye sin código adicional:
- 🩺 **Doctor** — Diagnóstico de binarios y paths del sistema
- ⚙️ **Config** — Editor interactivo de configuración
- 📖 **Docs** — Visor de documentación `.md`
- 🔄 **Update** — Auto-actualización vía Git cuando la app se ejecuta desde un clon del repositorio
- ❌ **Salir** — Cierre limpio

## Estructura del Paquete

```
src/clibaseapp/
├── app.py               CLIBaseApp heredable
├── models.py             BrowseResult, DoctorCheck, DoctorResult
├── exceptions.py         7 excepciones base
├── core/
│   ├── config.py         ConfigManager (XDG)
│   ├── scanner.py        Escáner genérico por extensiones
│   ├── updater.py        detección Git + actualización + reinicio
│   └── dependency_check  pip verification
├── services/
│   ├── doctor_service.py Diagnóstico genérico
│   └── browse_service.py Navegación + Protocol
└── ui/
    ├── browser.py        BrowserMenu parametrizado
    ├── components.py     Motor Rich + renders genéricos
    ├── doc_viewer.py     Visor interactivo .md
    ├── formatter.py      Formatter normalizado
    ├── menus.py          BaseMenu (select/checkbox/confirm/text/path)
    └── theme.py          Tema Rich compartido
```

## Documentación

- [Guía: Crear una App](docs/getting_started.md)
- [Arquitectura](docs/architecture.md)
