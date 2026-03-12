"""Configuración genérica central de la aplicación basada en XDG."""

import json
import logging
import os
from pathlib import Path

from clibaseapp.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestor de configuración centralizado y abstracto por aplicación."""
    
    def __init__(self, app_name: str, default_config: dict = None):
        self.app_name = app_name
        self.default_config = default_config or {}
        
        xdg_config = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.config_dir = xdg_config / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

    def update(self, key: str, value: any) -> None:
        """Actualiza una clave en el archivo de configuración y lo guarda."""
        config_data = self.read_all()
        config_data[key] = value
        try:
            with self.config_file.open("w", encoding="utf-8") as handler:
                json.dump(config_data, handler, indent=4, ensure_ascii=False)
        except OSError as exc:
            message = f"No se pudo guardar la configuración en '{self.config_file}': {exc}"
            logger.error(message)
            raise ConfigurationError(message) from exc

    def _write_defaults(self) -> dict:
        """Crea el archivo de configuración con los valores por defecto inyectados."""
        try:
            with self.config_file.open("w", encoding="utf-8") as handler:
                json.dump(self.default_config, handler, indent=4, ensure_ascii=False)
            return self.default_config
        except OSError as exc:
            logger.warning("No se pudo crear el config por defecto '%s': %s", self.config_file, exc)
            return {}

    def read_all(self) -> dict:
        """Lee el json de configuración global, originándolo si no existe."""
        try:
            if not self.config_file.exists():
                return self._write_defaults()
            with self.config_file.open("r", encoding="utf-8") as handler:
                return json.load(handler)
        except json.JSONDecodeError as exc:
            message = (
                f"El archivo '{self.config_file}' no contiene JSON válido. "
                "Corrige el formato o elimínalo."
            )
            logger.error(message)
            raise ConfigurationError(message) from exc
        except OSError as exc:
            message = f"No se pudo leer el archivo de configuración '{self.config_file}': {exc}"
            logger.error(message)
            raise ConfigurationError(message) from exc

    def get(self, key: str, default: any = None) -> any:
        """Obtiene un valor específico del config JSON."""
        data = self.read_all()
        return data.get(key, default)

    def validate_path(self, path: Path, source: str = "") -> Path:
        """Valida que un path exista, sea directorio y tenga permisos de lectura."""
        resolved = path.expanduser().resolve()

        if not resolved.exists():
            raise ConfigurationError(
                f"La ruta '{resolved}'{f' ({source})' if source else ''} no existe."
            )
        if not resolved.is_dir():
            raise ConfigurationError(
                f"La ruta '{resolved}'{f' ({source})' if source else ''} no es un directorio."
            )
        if not os.access(resolved, os.R_OK):
            raise ConfigurationError(
                f"La ruta '{resolved}'{f' ({source})' if source else ''} no tiene permisos de lectura."
            )
        return resolved

    def load_path(self, key: str, env_var: str = "", fallback: Path = None) -> Path:
        """Carga un path desde env → config → fallback con validación suave.

        Args:
            key: Clave en el config.json.
            env_var: Variable de entorno a comprobar primero (opcional).
            fallback: Path por defecto si no se encuentra nada.

        Returns:
            Path resuelto (puede ser el fallback sin validar si todo falla).
        """
        fallback = fallback or Path.cwd()
        source = ""

        # 1. Intentar desde variable de entorno
        env_value = os.getenv(env_var) if env_var else None
        if env_value:
            source = f"variable de entorno {env_var}"
            try:
                return self.validate_path(Path(env_value), source)
            except ConfigurationError:
                logger.warning("Variable %s inválida, probando config.", env_var)

        # 2. Intentar desde config.json
        config_value = self.get(key)
        if config_value:
            source = f"config ({key})"
            try:
                return self.validate_path(Path(config_value), source)
            except ConfigurationError:
                logger.warning("Config '%s' inválido, usando fallback.", key)

        # 3. Fallback
        try:
            return self.validate_path(fallback, "fallback")
        except ConfigurationError:
            logger.warning("Fallback '%s' inválido, devolviendo sin validar.", fallback)
            return fallback

