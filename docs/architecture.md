# Arquitectura de clibaseapp

`clibaseapp` ofrece una base reutilizable para CLIs interactivas. No contiene lógica de negocio de una aplicación concreta; solo infraestructura, UI genérica y servicios compartidos.

## Objetivo del framework

- estandarizar el arranque de aplicaciones CLI,
- centralizar configuración y documentación,
- reutilizar componentes visuales,
- simplificar diagnósticos y checks comunes,
- evitar que cada aplicación repita la misma infraestructura base.

## Módulos principales

```text
clibaseapp/
├── app.py
├── exceptions.py
├── models.py
├── core/
│   ├── config.py
│   ├── dependency_check.py
│   ├── scanner.py
│   └── updater.py
├── services/
│   ├── browse_service.py
│   └── doctor_service.py
└── ui/
    ├── browser.py
    ├── components.py
    ├── doc_viewer.py
    ├── formatter.py
    ├── menus.py
    └── theme.py
```

## Responsabilidades por paquete

### `app.py`

- define `CLIBaseApp`,
- crea `self.config`,
- registra el menú base,
- controla el ciclo de vida y el manejo global de excepciones.

### `core/`

- `config.py`: persistencia XDG y carga tipada de configuración,
- `dependency_check.py`: instalación/verificación de dependencias Python,
- `scanner.py`: escaneo recursivo de ficheros por extensiones,
- `updater.py`: actualización vía Git cuando el runtime está en un repo válido.

### `services/`

- lógica reutilizable sin UI,
- diagnósticos de binarios y paths,
- abstracciones para navegación.

### `ui/`

- renderizado y tematización,
- menús interactivos,
- navegador de rutas,
- visor de documentación.

## Ciclo de ejecución

```text
child.__init__()
  -> super().__init__()
  -> self.config queda inicializado
  -> la app hija define defaults, binarios y callbacks

child.run()
  -> child.setup_commands()
  -> _register_default_commands()
  -> self.cli()
  -> _interactive_main_menu()
  -> callback seleccionado
```

## Dependencias permitidas

```text
UI de la app hija -> servicios propios -> repositorios propios -> modelos propios
                     ^ usa utilidades genéricas de clibaseapp
```

Reglas:

- `clibaseapp` no debe conocer modelos ni servicios de negocio de una app hija.
- Las apps hijas pueden reutilizar `ConfigManager`, `BrowserMenu`, `scan_files`, `show_*`, etc.
- La lógica de negocio debe vivir fuera del framework.

## Contratos principales

### Configuración

Todas las apps hijas reciben:

```python
self.config = ConfigManager(app_name=app_name)
```

La app hija solo debe:

```python
self.config.default_config = {"workspace": "/tmp"}
```

### Menú

Registrar una opción de negocio:

```python
self.register_menu_option("Auditar", "audit", self._on_audit)
```

### Doctor

```python
self.require_binaries(["git"])
self._doctor_paths = {"workspace": Path.cwd()}
```

## Manejo de errores

Jerarquía base:

```text
CLIAppError
├── ConfigurationError
├── BinaryMissingError
├── InteractiveMenuError
├── PermissionAccessError
├── ExternalToolError
└── DependencyInstallationError
```

La app hija puede extender esta jerarquía con excepciones propias.

## Ejemplo de extensión correcta

```python
class ReportsApp(CLIBaseApp):
    def __init__(self) -> None:
        super().__init__(app_name="reports", description="Reports CLI")
        self.config.default_config = {"root": "."}

    def _on_report(self) -> None:
        summary = self.report_service.build_summary()
        self.renderer.render_summary(summary)

    def setup_commands(self) -> None:
        self.register_menu_option("Report", "report", self._on_report)
```

## Límites del framework

- no ejecutar reglas de negocio del dominio de la app hija,
- no definir modelos de dominio específicos,
- no acoplarse a un repositorio concreto,
- no asumir que la instalación siempre viene de Git.
