"""
Auto-bootstrapper de entorno virtual para aplicaciones clibaseapp.

Proporciona la función `ensure_venv()` que garantiza que el script se ejecuta
dentro del `.venv` local del proyecto, instalando dependencias solo cuando
es estrictamente necesario (venv inexistente o paquetes faltantes).

NO realiza `git pull` ni actualizaciones de paquetes existentes.
Eso es responsabilidad del actualizador (`updater.py`).

Uso en el main.py de la app hija, ANTES de cualquier import del framework:

    import sys, os
    from pathlib import Path

    # ── Bootstrap (debe ir PRIMERO, antes de cualquier import externo) ──
    _HERE = Path(__file__).parent.resolve()
    sys.path.insert(0, str(_HERE / ".venv" / "Lib" / "site-packages"))  # opcional
    exec(open(_HERE / ".venv_bootstrap.py").read()) if ... else None

    # O directamente si clibaseapp ya está disponible en el Python base:
    from clibaseapp.core.bootstrap import ensure_venv
    ensure_venv(app_dir=Path(__file__).parent.resolve())
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path


def ensure_venv(
    app_dir: Path,
    requirements_file: str = "requirements.txt",
    check_package: str = "clibaseapp",
) -> None:
    """Garantiza que el script corre dentro del .venv local del proyecto.

    Instala dependencias ÚNICAMENTE cuando:
    - El .venv no existe todavía (primera ejecución).
    - El paquete sentinel (`check_package`) no está instalado (venv corrupto/vacío).

    NO actualiza paquetes ya instalados ni hace git pull.

    Args:
        app_dir: Directorio raíz del proyecto (donde vive requirements.txt y .venv).
        requirements_file: Nombre del fichero de requisitos (relativo a `app_dir`).
        check_package: Paquete que se comprueba para detectar venv vacío.
    """
    venv_dir = app_dir / ".venv"

    # ── Calcular rutas según SO ───────────────────────────────────
    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_bin = str(venv_dir / "Scripts")
        path_key = "Path" if "Path" in os.environ else "PATH"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_bin = str(venv_dir / "bin")
        path_key = "PATH"

    # Inyectar siempre el bin del venv en el PATH (necesario para binarios como `ia`)
    if venv_bin not in os.environ.get(path_key, ""):
        os.environ[path_key] = venv_bin + os.pathsep + os.environ.get(path_key, "")

    is_in_venv = venv_dir in Path(sys.executable).parents
    req_file = app_dir / requirements_file

    if not is_in_venv:
        # ── Caso 1: Ejecutando con Python del sistema ─────────────
        venv_is_new = not venv_dir.exists()

        if venv_is_new:
            print(f"[+] Creando entorno virtual en {venv_dir}...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        # Solo instalar si el venv es nuevo o si el paquete sentinel no está
        if venv_is_new or not _package_installed(venv_python, check_package):
            _install_requirements(venv_python, req_file)

        # Re-ejecutar con el Python del venv
        env = os.environ.copy()
        env[path_key] = venv_bin + os.pathsep + env.get(path_key, "")
        os.execve(str(venv_python), [str(venv_python)] + sys.argv, env)

    else:
        # ── Caso 2: Ya dentro del venv — comprobar integridad ─────
        # (puede faltar si el venv fue clonado vacío o el repo tuvo un pull)
        try:
            importlib.import_module(check_package)
        except ImportError:
            print(f"[!] Paquete '{check_package}' no encontrado en el venv. Instalando...")
            _install_requirements(venv_python, req_file)


# ── Helpers privados ─────────────────────────────────────────────

def _package_installed(venv_python: Path, package: str) -> bool:
    """Comprueba si `package` está instalado en el venv dado."""
    result = subprocess.run(
        [str(venv_python), "-c", f"import {package}"],
        capture_output=True,
    )
    return result.returncode == 0


def _install_requirements(venv_python: Path, req_file: Path) -> None:
    """Instala los paquetes del fichero de requisitos en el venv."""
    if not req_file.exists():
        print(f"[!] No se encontró {req_file}. Saltando instalación de requisitos.")
        return

    print(f"[*] Instalando dependencias desde {req_file.name}...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(req_file)],
            check=True,
        )
        print("[OK] Dependencias instaladas correctamente.\n")
    except subprocess.CalledProcessError as exc:
        print(f"[X] Error al instalar dependencias: {exc}")
        sys.exit(1)
