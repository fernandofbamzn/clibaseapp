"""
Excepciones base del framework clibaseapp.
Las apps hijas heredarán de estas para sus errores específicos.
"""


class CLIAppError(Exception):
    """Excepción raíz del framework."""
    pass


class ConfigurationError(CLIAppError):
    """Errores de lectura/escritura de configuración."""
    pass


class BinaryMissingError(CLIAppError):
    """Una dependencia binaria del sistema no fue encontrada."""
    pass


class InteractiveMenuError(CLIAppError):
    """Errores durante el control interactivo de menús."""
    pass


class PermissionAccessError(CLIAppError):
    """Error de permisos al acceder a rutas o archivos."""
    pass


class ExternalToolError(CLIAppError):
    """Fallo al ejecutar una herramienta externa (retorno no-cero)."""
    pass


class DependencyInstallationError(CLIAppError):
    """Fallo al instalar dependencias de Python mediante pip."""
    pass
