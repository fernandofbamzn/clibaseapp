# clibaseapp

`clibaseapp` es un framework reutilizable para construir aplicaciones CLI interactivas en Python con una base común de configuración, documentación, diagnóstico y navegación.

## Capacidades principales

- Menú interactivo basado en `Typer`, `Questionary` y `Rich`.
- `ConfigManager` con persistencia XDG (`~/.config/<app>/config.json`).
- Doctor para validar binarios y rutas.
- Visor integrado de documentación Markdown.
- Utilidades de UI compartidas (`show_header`, `show_info`, `dict_table`, `fmt`, etc.).
- Actualización vía Git cuando la app se ejecuta desde un clon del repositorio.

## Instalación

Desde un proyecto hermano:

```bash
pip install -e ../clibaseapp
```

Desde un repositorio Git:

```bash
pip install git+https://github.com/<org>/<repo>.git
```

## Ejemplo mínimo de integración

```python
from pathlib import Path

from clibaseapp import CLIBaseApp, check_and_install, show_success


class MiApp(CLIBaseApp):
    def __init__(self) -> None:
        super().__init__(app_name="mi-app", description="Mi App CLI")
        self.config.default_config = {
            "data_root": str(Path.cwd()),
            "language": "es",
        }
        self._app_dir = Path(__file__).parent.resolve()
        self.require_binaries(["git"])

    def run_healthcheck(self) -> None:
        show_success("La app hija está corriendo sobre clibaseapp.")

    def setup_commands(self) -> None:
        self.register_menu_option("Verificación", "healthcheck", self.run_healthcheck)


if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MiApp().run()
```

## Flujo recomendado para una app hija

1. Heredar de `CLIBaseApp`.
2. Definir `self.config.default_config` en `__init__`.
3. Registrar comandos propios en `setup_commands()`.
4. Mantener la lógica de negocio fuera del entrypoint.
5. Documentar la app hija en `README.md` y `docs/`.

## Menú base incorporado

Toda app hija recibe estas opciones sin implementación adicional:

- `Doctor`: valida binarios y rutas registradas.
- `Config`: edita el `config.json` de la app.
- `Docs`: abre los `.md` del proyecto.
- `Actualizar App`: ejecuta la actualización vía Git si el runtime está dentro de un repositorio válido.
- `Salir`: cierra el bucle interactivo de forma limpia.

## Ejemplos de uso habituales

Ejecutar la demo incluida:

```bash
python demo_app.py
```

Instalar dependencias antes de arrancar una app hija:

```python
from clibaseapp import check_and_install

check_and_install(["rich", "questionary", "typer"])
```

Leer una ruta tipada desde configuración:

```python
from pathlib import Path

data_root = self.config.load_path("data_root", fallback=Path.cwd())
```

## Estructura del framework

```text
src/clibaseapp/
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

## Documentación

- [`docs/getting_started.md`](docs/getting_started.md): cómo crear una app hija.
- [`docs/architecture.md`](docs/architecture.md): responsabilidades, capas y flujo interno.
