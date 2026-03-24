"""
Servicio de montaje SSHFS para el framework clibaseapp.

Permite montar unidades de red remotas vía SSHFS de forma interactiva,
guardando y reutilizando los parámetros de conexión en la configuración
de la aplicación.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import rich

from clibaseapp.core.logger import get_logger


def describe_mount_status(mount_point: str) -> tuple[bool, str]:
    """Devuelve si la ruta puede verificarse como montada y el motivo."""
    state, detail = _inspect_mount_point(mount_point)
    return state == "mounted", detail


def mount_drive(config) -> None:
    """Flujo interactivo para montar una unidad remota vía SSHFS."""
    mount_point = str(config.get("download_root", "/mnt/nas/descargas"))
    logger = get_logger(getattr(config, "app_name", "clibaseapp"))
    logger.info("Inicio del flujo de montaje SSHFS sobre '%s'.", mount_point)

    raw_conf = config.get("sshfs_config", {})
    ssh_conf: dict = raw_conf if isinstance(raw_conf, dict) else {}

    mount_state, mount_detail = _inspect_mount_point(mount_point)
    logger.info("Estado previo del punto de montaje '%s': %s - %s", mount_point, mount_state, mount_detail)

    if mount_state == "mounted":
        rich.print(f"\n[yellow]La carpeta {mount_point} ya está montada.[/yellow]")
        if input("¿Desmontar forzosamente antes de volver a montar? (s/n): ").lower() == "s":
            if not _attempt_unmount(mount_point, logger):
                return
        else:
            logger.info("Montaje cancelado por el usuario: el punto ya estaba montado.")
            return
    elif mount_state == "content":
        rich.print(
            f"\n[yellow]La carpeta {mount_point} contiene datos pero no figura como punto de montaje.[/yellow]"
        )
        rich.print(f"[dim]{mount_detail}[/dim]")
        proceed = input("¿Continuar con el montaje igualmente? (s/n): ").lower() == "s"
        if not proceed:
            logger.info("Montaje cancelado por el usuario: ruta con contenido previo.")
            return
    elif mount_state == "inaccessible":
        rich.print(
            f"\n[red]No se puede acceder a {mount_point}.[/red]\n[dim]{mount_detail}[/dim]"
        )
        logger.warning("Ruta inaccesible antes del montaje '%s': %s", mount_point, mount_detail)
        return

    saved_ip = ssh_conf.get("ip", "")
    saved_remote = ssh_conf.get("remote_path", "")
    saved_user = ssh_conf.get("user", "")

    ip = _ask_with_default("IP del servidor NAS/remoto", saved_ip)
    remote = _ask_with_default("Ruta remota SSHFS", saved_remote)
    user = _ask_with_default("Usuario SSH", saved_user or "root")

    remote_clean = remote.replace("\\ ", " ").replace("\\(", "(").replace("\\)", ")")
    ssh_conf.update({"ip": ip, "remote_path": remote_clean, "user": user})
    config.update("sshfs_config", ssh_conf)

    try:
        Path(mount_point).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("No se pudo crear el punto de montaje '%s': %s", mount_point, exc, exc_info=True)
        rich.print(f"\n[red]✘ No se pudo crear el punto de montaje:[/red] {exc}")
        return

    rich.print(f"\nMontando [cyan]{user}@{ip}:{remote_clean}[/cyan] → [b]{mount_point}[/b]...\n")
    logger.info(
        "Ejecutando sshfs para montar '%s@%s:%s' en '%s'.",
        user,
        ip,
        remote_clean,
        mount_point,
    )
    remote_path_fixed = f"\"{remote_clean}\""
    result = _run_command(
        ["sshfs", f"{user}@{ip}:{remote_path_fixed}", mount_point, "-o", "reconnect"],
        logger=logger,
        description="sshfs",
    )

    if not result["ok"]:
        detail = result["detail"]
        logger.error("Fallo al montar '%s': %s", mount_point, detail)
        rich.print(
            "\n[yellow]⚠ El montaje ha fallado. "
            f"Detalle: {detail}[/yellow]"
        )
        return

    time.sleep(1)
    post_state, post_detail = _inspect_mount_point(mount_point)
    logger.info("Estado posterior del punto de montaje '%s': %s - %s", mount_point, post_state, post_detail)

    if post_state == "mounted":
        rich.print("\n[green]✔ Montaje satisfactorio.[/green]")
        return

    logger.error(
        "sshfs devolvió éxito pero la ruta '%s' no quedó montada/accesible: %s",
        mount_point,
        post_detail,
    )
    rich.print(
        "\n[yellow]⚠ sshfs terminó sin error, pero la ruta no quedó montada correctamente. "
        f"Detalle: {post_detail}[/yellow]"
    )


def _attempt_unmount(mount_point: str, logger) -> bool:
    """Intenta desmontar una ruta y registra cualquier problema."""
    logger.info("Intentando desmontar '%s'.", mount_point)

    result = _run_command(["umount", mount_point], logger=logger, description="umount")
    if result["ok"]:
        time.sleep(1)
        return True

    logger.warning("umount normal falló sobre '%s': %s", mount_point, result["detail"])
    lazy_result = _run_command(["umount", "-l", mount_point], logger=logger, description="umount -l")
    if lazy_result["ok"]:
        time.sleep(1)
        return True

    logger.error("No se pudo desmontar '%s': %s", mount_point, lazy_result["detail"])
    rich.print(
        "\n[red]✘ No se pudo desmontar la unidad antes de remontar.[/red]\n"
        f"[dim]{lazy_result['detail']}[/dim]"
    )
    return False


def _run_command(command: list[str], logger, description: str) -> dict[str, str | bool]:
    """Ejecuta un comando del sistema devolviendo un resultado uniforme."""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        detail = f"Comando no encontrado: {command[0]}"
        logger.error("%s (%s): %s", description, command, exc, exc_info=True)
        return {"ok": False, "detail": detail}
    except PermissionError as exc:
        detail = f"Permiso denegado ejecutando {command[0]}: {exc}"
        logger.error("%s (%s): %s", description, command, exc, exc_info=True)
        return {"ok": False, "detail": detail}
    except OSError as exc:
        detail = f"Error del sistema ejecutando {command[0]}: {exc}"
        logger.error("%s (%s): %s", description, command, exc, exc_info=True)
        return {"ok": False, "detail": detail}

    if result.returncode != 0:
        detail = _summarize_streams(result.stdout, result.stderr) or f"Código de salida {result.returncode}"
        logger.error(
            "Comando '%s' falló con código %s. stdout=%r stderr=%r",
            description,
            result.returncode,
            result.stdout,
            result.stderr,
        )
        return {"ok": False, "detail": detail}

    if result.stdout.strip() or result.stderr.strip():
        logger.info(
            "Comando '%s' completado. stdout=%r stderr=%r",
            description,
            result.stdout,
            result.stderr,
        )
    return {"ok": True, "detail": _summarize_streams(result.stdout, result.stderr) or "OK"}


def _inspect_mount_point(mount_point: str) -> tuple[str, str]:
    """Describe el estado observable de una ruta de montaje."""
    path = Path(mount_point)
    verified, verified_detail = _verify_mount(path)
    if verified:
        return "mounted", verified_detail
    if not path.exists():
        return "missing", "La ruta aún no existe."
    if not path.is_dir():
        return "inaccessible", "La ruta existe pero no es un directorio."

    try:
        entries = list(path.iterdir())
    except OSError as exc:
        return "inaccessible", f"No se pudo listar la ruta: {exc}"

    if entries:
        return "content", (
            f"La ruta contiene {len(entries)} entrada(s), "
            "pero no se pudo verificar como punto de montaje."
        )
    return "empty", "La ruta existe y está vacía."


def _verify_mount(path: Path) -> tuple[bool, str]:
    """Intenta verificar el montaje usando varias fuentes del sistema."""
    mount_point = str(path)

    if os.path.ismount(mount_point):
        return True, "La ruta es un punto de montaje del sistema."

    if not path.exists() or not path.is_dir():
        return False, "La ruta no existe o no es un directorio."

    mountinfo_detail = _detect_mount_from_mountinfo(path)
    if mountinfo_detail:
        return True, mountinfo_detail

    command_detail = _detect_mount_from_commands(path)
    if command_detail:
        return True, command_detail

    stat_detail = _detect_mount_from_stat(path)
    if stat_detail:
        return True, stat_detail

    return False, "No se encontró evidencia verificable de montaje."


def _detect_mount_from_mountinfo(path: Path) -> str | None:
    """Comprueba mountinfo en sistemas Linux."""
    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.exists():
        return None

    try:
        resolved_path = str(path.resolve())
        for line in mountinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            left, _separator, right = line.partition(" - ")
            if not _separator:
                continue
            left_parts = left.split()
            right_parts = right.split()
            if len(left_parts) < 5 or len(right_parts) < 2:
                continue
            mount_target = _decode_mount_field(left_parts[4])
            if mount_target == resolved_path:
                source = right_parts[1] if len(right_parts) > 1 else "desconocido"
                fstype = right_parts[0] if right_parts else "desconocido"
                return f"Montaje verificado por mountinfo: {source} ({fstype})."
    except OSError:
        return None

    return None


def _detect_mount_from_commands(path: Path) -> str | None:
    """Usa comandos estándar del sistema para verificar un mountpoint."""
    mount_point = str(path)

    if shutil.which("mountpoint"):
        try:
            result = subprocess.run(
                ["mountpoint", "-q", mount_point],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return "Montaje verificado por el comando mountpoint."
        except OSError:
            pass

    if shutil.which("findmnt"):
        try:
            result = subprocess.run(
                ["findmnt", "-T", mount_point, "--noheadings", "--output", "TARGET,SOURCE,FSTYPE"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                last_line = result.stdout.strip().splitlines()[-1]
                return f"Montaje verificado por findmnt: {last_line}"
        except OSError:
            pass

    return None


def _detect_mount_from_stat(path: Path) -> str | None:
    """Compara el dispositivo del directorio con el de su padre."""
    try:
        resolved = path.resolve()
        parent = resolved.parent
        if parent == resolved:
            return None
        current_stat = resolved.stat()
        parent_stat = parent.stat()
    except OSError:
        return None

    if current_stat.st_dev != parent_stat.st_dev:
        return "Montaje verificado por cambio de dispositivo respecto al directorio padre."
    return None


def _decode_mount_field(value: str) -> str:
    """Decodifica escapes de mountinfo."""
    return (
        value.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
    )


def _summarize_streams(stdout: str, stderr: str) -> str:
    """Compacta stdout/stderr para mostrar un detalle breve al usuario."""
    parts = []
    if stderr.strip():
        parts.append(stderr.strip().splitlines()[-1])
    if stdout.strip():
        parts.append(stdout.strip().splitlines()[-1])
    return " | ".join(parts)


def _ask_with_default(prompt: str, default: str) -> str:
    """Muestra un prompt con el valor actual y devuelve la respuesta o el valor por defecto."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "

    answer = input(display).strip()
    return answer if answer else default
