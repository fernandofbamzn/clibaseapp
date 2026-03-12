# Arquitectura de clibaseapp

## Diagrama de Módulos

```
clibaseapp/
├── app.py               CLIBaseApp (menú principal + defaults)
├── models.py             BrowseResult, DoctorCheck, DoctorResult
├── exceptions.py         Jerarquía de excepciones
├── core/
│   ├── config.py         ConfigManager (XDG config.json)
│   ├── scanner.py        scan_files() genérico
│   ├── updater.py        git pull + reinicio
│   └── dependency_check  Verificación de pip packages
├── services/
│   ├── doctor_service.py DoctorService (binarios + paths)
│   └── browse_service.py BrowseService + BrowseSelector Protocol
└── ui/
    ├── browser.py        BrowserMenu (navegador de directorios)
    ├── components.py     Motor Rich (headers, tablas, renders)
    ├── doc_viewer.py     Visor interactivo de .md
    ├── formatter.py      Formatter + fmt singleton
    ├── menus.py          BaseMenu (select, checkbox, confirm, text, path)
    └── theme.py          APP_THEME (Rich)
```

## Flujo de Herencia

```
CLIBaseApp.__init__()
    ↓
CLIBaseApp.run()
    ↓
child.setup_commands()       ← El hijo registra sus opciones
    ↓
_register_default_commands() ← Doctor, Config, Docs, Update
    ↓
Typer.cli()
    ↓ (sin subcomando)
_interactive_main_menu()     ← Bucle infinito
    ↓ (selección)
opt["callback"]()            ← Ejecuta el callback del hijo o del padre
```

## Jerarquía de Excepciones

```
Exception
└── CLIAppError
    ├── ConfigurationError
    ├── BinaryMissingError
    ├── InteractiveMenuError
    ├── PermissionAccessError
    ├── ExternalToolError
    ├── DependencyInstallationError
    └── (excepciones de la app hija)
        └── MediaToolsError
            └── InvalidMediaMetadataError
```
