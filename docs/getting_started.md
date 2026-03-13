# Guía de Inicio para Apps Hijas

Esta guía describe la forma recomendada de crear una aplicación hija sobre `clibaseapp`.

## 1. Estructura mínima

```text
mi-app/
├── main.py
├── core/
├── data/
├── models/
├── services/
├── ui/
└── docs/
```

## 2. Definir el entrypoint

`main.py` debe limitarse al wiring de la aplicación y al registro de callbacks.

```python
from pathlib import Path

from clibaseapp import CLIBaseApp, check_and_install, show_success


class MiApp(CLIBaseApp):
    def __init__(self) -> None:
        super().__init__(app_name="mi-app", description="Mi aplicación CLI")

        self.config.default_config = {
            "workspace": str(Path.cwd()),
            "language": "es",
        }
        self._app_dir = Path(__file__).parent.resolve()
        self.require_binaries(["git"])
        self._doctor_paths = {"workspace": Path.cwd()}

    def show_status(self) -> None:
        show_success("La app está correctamente inicializada.")

    def setup_commands(self) -> None:
        self.register_menu_option("Estado", "status", self.show_status)


if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MiApp().run()
```

## 3. Responsabilidades del framework y de la app hija

Responsabilidad del framework:

- bucle principal de menú,
- editor de configuración,
- visor de documentación,
- doctor de dependencias,
- actualización vía Git si aplica,
- componentes visuales compartidos.

Responsabilidad de la app hija:

- lógica de negocio específica,
- modelos de dominio,
- adaptadores de datos externos,
- renderers o flujos propios,
- documentación funcional de la app.

## 4. Regla de capas

Usa este flujo como norma de diseño:

```text
main.py -> ui/ -> services/ -> data/ -> models/
```

Ejemplo correcto:

- `ui/workflows.py` resuelve el input con `questionary`.
- `services/media_service.py` recibe parámetros ya resueltos.
- `data/repository.py` ejecuta binarios o accede a disco.

Ejemplo incorrecto:

- un servicio que imprime en consola,
- un repositorio que llama a `show_warning`,
- un entrypoint que implementa reglas de negocio largas.

## 5. Configuración

`CLIBaseApp` crea automáticamente `self.config`. La app hija debe reutilizar siempre esa instancia.

Ejemplo:

```python
self.config.default_config = {
    "media_root": str(Path.cwd()),
    "keep_languages": ["spa", "eng"],
}
```

Leer una ruta validada:

```python
from pathlib import Path

media_root = self.config.load_path("media_root", fallback=Path.cwd())
```

Actualizar una clave:

```python
self.config.update("language", "en")
```

## 6. Registrar rutas y binarios para el doctor

```python
self.require_binaries(["ffmpeg", "mediainfo"])
self._doctor_paths = {
    "workspace": Path.cwd(),
    "cache_dir": Path.cwd() / ".cache",
}
```

## 7. Ejemplo de separación UI / servicio

Servicio puro:

```python
class ReportService:
    def build_summary(self, items: list[str]) -> dict[str, int]:
        return {"total": len(items)}
```

Workflow UI:

```python
from clibaseapp import show_success


def run_report_flow(service: ReportService) -> None:
    items = ["a", "b", "c"]
    summary = service.build_summary(items)
    show_success(f"Total: {summary['total']}")
```

## 8. Comandos útiles durante el desarrollo

Ejecutar la app:

```bash
python main.py
```

Ejecutar tests:

```bash
python -m pytest -q
```

Ver la demo del framework:

```bash
python ../clibaseapp/demo_app.py
```

## 9. Lecturas recomendadas

- [`architecture.md`](architecture.md)
- README de la app hija
- documentación funcional propia en `docs/`
