# CLI Base App Framework

Framework reutilizable de Python para construir interfaces de línea de comandos modernas e interactivas utilizando `Typer`, `Rich`, y `Questionary`. 

Extraído de `Media Tools`. Permite inyectar lógica de negocio custom heredando características de sistema y auto-actualización.

## Uso Básico

```python
from clibaseapp.app import CLIBaseApp

class MiTestApp(CLIBaseApp):
    def __init__(self):
        super().__init__(app_name="mi-test", description="Test Base")

    def setup_commands(self):
        self.register_menu_option("Comando", "cmd", lambda: print("Hola"))

if __name__ == "__main__":
    MiTestApp().run()
```
