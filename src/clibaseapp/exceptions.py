"""
Excepciones base manejables globales dentro del framework.
"""

class CLIAppError(Exception):
    """Excepción base de la que heredarán todos los errores operativos conocidos."""
    pass

class ConfigurationError(CLIAppError):
    """Errores debidos a falta o mala lectura de configuración del usuario."""
    pass

class BinaryMissingError(CLIAppError):
    """Dependencias del sistema no encontradas durante la pre-ejecución."""
    pass

class InteractiveMenuError(CLIAppError):
    """Errores generados durante el control interactivo de rutas."""
    pass
