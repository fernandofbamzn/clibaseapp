"""Configuracion central basada en XDG con ambito global y por aplicacion."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from clibaseapp.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestor de configuracion con merge global/app/default."""

    def __init__(
        self,
        app_name: str,
        default_config: dict | None = None,
        global_app_name: str = "clibaseapp",
    ) -> None:
        self.app_name = app_name
        self.default_config = default_config or {}
        self.global_app_name = global_app_name

        xdg_config = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.global_config_dir = xdg_config / global_app_name
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        self.global_config_file = self.global_config_dir / "config.json"

        self.config_dir = xdg_config / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

    def _write_file(self, path: Path, data: dict[str, Any]) -> dict[str, Any]:
        try:
            with path.open("w", encoding="utf-8") as handler:
                json.dump(data, handler, indent=4, ensure_ascii=False)
            return data
        except OSError as exc:
            message = f"No se pudo guardar la configuracion en '{path}': {exc}"
            logger.error(message)
            raise ConfigurationError(message) from exc

    def _read_file(self, path: Path, default_data: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            if not path.exists():
                if default_data is None:
                    return {}
                return self._write_file(path, dict(default_data))
            with path.open("r", encoding="utf-8") as handler:
                loaded = json.load(handler)
        except json.JSONDecodeError as exc:
            message = (
                f"El archivo '{path}' no contiene JSON valido. "
                "Corrige el formato o eliminalo."
            )
            logger.error(message)
            raise ConfigurationError(message) from exc
        except OSError as exc:
            message = f"No se pudo leer el archivo de configuracion '{path}': {exc}"
            logger.error(message)
            raise ConfigurationError(message) from exc

        if not isinstance(loaded, dict):
            message = f"El archivo '{path}' debe contener un objeto JSON."
            logger.error(message)
            raise ConfigurationError(message)

        return loaded

    def read_all(self, scope: str = "app") -> dict[str, Any]:
        """Lee el config solicitado.

        `scope` puede ser `app`, `global` o `merged`.
        """

        if scope == "app":
            return self._read_file(self.config_file, self.default_config)
        if scope == "global":
            return self._read_file(self.global_config_file)
        if scope == "merged":
            merged = dict(self.default_config)
            merged.update(self.read_all(scope="global"))
            merged.update(self.read_all(scope="app"))
            return merged
        raise ValueError(f"Scope de configuracion no soportado: {scope}")

    def get(
        self,
        key: str,
        default: Any = None,
        *,
        env_var: str = "",
        scope: str = "merged",
    ) -> Any:
        """Obtiene un valor usando prioridad env -> app -> global -> defaults."""

        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                return env_value

        data = self.read_all(scope=scope)
        if key in data:
            return data[key]
        return default

    def update(self, key: str, value: Any, scope: str = "app") -> None:
        """Actualiza una clave en el ambito indicado y guarda el archivo."""

        if scope == "app":
            path = self.config_file
            config_data = self.read_all(scope="app")
        elif scope == "global":
            path = self.global_config_file
            config_data = self.read_all(scope="global")
        else:
            raise ValueError(f"Scope de configuracion no soportado: {scope}")

        config_data[key] = value
        self._write_file(path, config_data)

    def set(self, key: str, value: Any, scope: str = "app") -> None:
        """Alias legacy de `update()`."""

        self.update(key, value, scope=scope)

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

    def load_path(self, key: str, env_var: str = "", fallback: Path | None = None) -> Path:
        """Carga un path desde env -> config app/global -> fallback."""

        fallback = fallback or Path.cwd()

        env_value = os.getenv(env_var) if env_var else None
        if env_value:
            try:
                return self.validate_path(Path(env_value), f"variable de entorno {env_var}")
            except ConfigurationError:
                logger.warning("Variable %s invalida, probando configuracion.", env_var)

        config_value = self.get(key)
        if config_value:
            try:
                return self.validate_path(Path(config_value), f"config ({key})")
            except ConfigurationError:
                logger.warning("Config '%s' invalido, usando fallback.", key)

        try:
            return self.validate_path(fallback, "fallback")
        except ConfigurationError:
            logger.warning("Fallback '%s' invalido, devolviendo sin validar.", fallback)
            return fallback
