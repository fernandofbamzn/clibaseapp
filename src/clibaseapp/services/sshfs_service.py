"""
Servicio de montaje SSHFS para el framework clibaseapp.

Permite montar unidades de red remotas vía SSHFS de forma interactiva,
guardando y reutilizando los parámetros de conexión en la configuración
de la aplicación.
"""

import os
import subprocess
import time
from pathlib import Path

import rich


def mount_drive(config) -> None:
    """Flujo interactivo para montar una unidad remota vía SSHFS.

    - Lee/guarda los parámetros de conexión en `config` bajo la clave `sshfs_config`.
    - Pregunta al usuario cualquier dato que no esté guardado aún.
    - Persiste todos los valores introducidos para usarlos como defecto la próxima vez.
    - Crea el punto de montaje si no existe.

    Args:
        config: Instancia de ConfigManager (o cualquier objeto con .get() y .update()).
    """
    mount_point: str = config.get("download_root", "/mnt/nas/descargas")

    # Leer configuración SSHFS, garantizando que sea siempre un dict
    raw_conf = config.get("sshfs_config", {})
    ssh_conf: dict = raw_conf if isinstance(raw_conf, dict) else {}

    # ── Comprobar si ya está montado ──────────────────────────────
    if os.path.ismount(mount_point) or (
        os.path.exists(mount_point) and os.listdir(mount_point)
    ):
        rich.print(
            f"\n[yellow]La carpeta {mount_point} ya parece montada o tiene contenido.[/yellow]"
        )
        if input("¿Desmontar forzosamente antes de volver a montar? (s/n): ").lower() == "s":
            subprocess.run(["umount", mount_point], check=False)
            if os.path.ismount(mount_point):
                subprocess.run(["umount", "-l", mount_point], check=False)
            time.sleep(1)
        else:
            return

    # ── Pedir datos que falten, usando los guardados como sugerencia ──
    saved_ip = ssh_conf.get("ip", "")
    saved_remote = ssh_conf.get("remote_path", "")
    saved_user = ssh_conf.get("user", "")

    ip = _ask_with_default("IP del servidor NAS/remoto", saved_ip)
    remote = _ask_with_default("Ruta remota SSHFS", saved_remote)
    user = _ask_with_default("Usuario SSH", saved_user or "root")

    # Limpiar caracteres escapados de la ruta (ej. rutas copiadas desde terminal)
    remote_clean = remote.replace("\\ ", " ").replace("\\(", "(").replace("\\)", ")")

    # ── Persistir todos los valores para la próxima vez ──────────
    ssh_conf.update({"ip": ip, "remote_path": remote_clean, "user": user})
    config.update("sshfs_config", ssh_conf)

    # ── Crear punto de montaje si no existe ──────────────────────
    Path(mount_point).mkdir(parents=True, exist_ok=True)

    # ── Ejecutar SSHFS ────────────────────────────────────────────
    rich.print(
        f"\nMontando [cyan]{user}@{ip}:{remote_clean}[/cyan] → [b]{mount_point}[/b]...\n"
    )
    result = subprocess.run(
        ["sshfs", f"{user}@{ip}:{remote_clean}", mount_point, "-o", "reconnect"],
        check=False,
    )

    if result.returncode == 0 or os.path.ismount(mount_point):
        rich.print("\n[green]✔ Montaje satisfactorio.[/green]")
    else:
        rich.print(
            "\n[yellow]⚠ El montaje puede haber fallado. "
            "Comprueba la conectividad SSH y que sshfs esté instalado.[/yellow]"
        )


# ── Helpers ──────────────────────────────────────────────────────

def _ask_with_default(prompt: str, default: str) -> str:
    """Muestra un prompt con el valor actual y devuelve la respuesta o el valor por defecto."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "

    answer = input(display).strip()
    return answer if answer else default
