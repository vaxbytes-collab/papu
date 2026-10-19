"""Almacenamiento JSON compartido y persistente para Papu."""
import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock

# Todo el estado que sobrevive a los reinicios debe vivir en este directorio.
# Render usa un disco montado en /var/data; en local se usa ./data.
PERSISTED_JSON_FILES = (
    "pets.json",
    "utility_settings.json",
    "reminders.json",
    "events.json",
    "suggestions.json",
    "log_channels.json",
    "warns.json",
    "moderation_settings.json",
)
_LOCK = RLock()


def _select_data_dir(environ=None, cwd=None) -> Path:
    """Elige el directorio de datos según la configuración y el alojamiento."""
    env = os.environ if environ is None else environ
    base = Path(cwd) if cwd is not None else Path.cwd()
    is_render = bool(env.get("RENDER_SERVICE_ID") or env.get("RENDER_INSTANCE_ID"))
    configured = str(env.get("PAPU_DATA_DIR", "") or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_absolute():
            return path
        # En Render, incluso una ruta relativa debe quedar dentro del disco persistente.
        return (Path("/var/data") if is_render else base) / path
    if is_render:
        return Path("/var/data")
    return base / "data"


DATA_DIR = _select_data_dir()


def _migrate_legacy_data(legacy_dirs=None) -> int:
    """Copia datos JSON antiguos al directorio nuevo sin reemplazar nada existente."""
    if legacy_dirs is None:
        root = Path.cwd()
        legacy_dirs = (root, root / "data")

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        logging.exception("[STORAGE] No se pudo crear el directorio de datos %s", DATA_DIR)
        return 0

    copied = 0
    destination_dir = DATA_DIR.resolve()
    for legacy_dir in legacy_dirs:
        source_dir = Path(legacy_dir)
        for filename in PERSISTED_JSON_FILES:
            source = source_dir / filename
            target = DATA_DIR / filename
            try:
                if source.resolve() == target.resolve() or not source.is_file() or target.exists():
                    continue
                # No migres archivos rotos: no deben transformarse en estado vacio.
                value = json.loads(source.read_text(encoding="utf-8"))
                with _LOCK:
                    if target.exists():
                        continue
                    fd, temporary_path = tempfile.mkstemp(
                        prefix=f".{target.name}.migration.",
                        dir=str(destination_dir),
                    )
                    try:
                        with os.fdopen(fd, "w", encoding="utf-8") as handle:
                            json.dump(value, handle, ensure_ascii=False, indent=2)
                            handle.flush()
                            os.fsync(handle.fileno())
                        os.replace(temporary_path, target)
                    finally:
                        try:
                            os.unlink(temporary_path)
                        except FileNotFoundError:
                            pass
                copied += 1
                logging.info("[STORAGE] Datos antiguos migrados: %s", filename)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                logging.exception("[STORAGE] No se pudo migrar el archivo %s", source)
    return copied


def data_path(name: str) -> Path:
    """Devuelve una ruta dentro del directorio de datos de Papu."""
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("El nombre debe ser un nombre de archivo, no una ruta")
    return DATA_DIR / name


def load_json(name: str, default):
    path = data_path(name)
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, type(default)) else default
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def save_json(name: str, value) -> None:
    """Guarda datos de forma atomica para evitar archivos parciales."""
    path = data_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        fd, temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


# Intenta rescatar los JSON antiguos si siguen presentes en el despliegue actual.
_migrate_legacy_data()

# Avisa de forma visible si Render esta usando rutas que no son persistentes.
_RENDER_ENV = bool(os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER_INSTANCE_ID"))
_RENDER_DATA_ROOT = Path("/var/data")
try:
    _DATA_DIR_UNDER_RENDER_DISK = DATA_DIR.resolve().is_relative_to(_RENDER_DATA_ROOT)
except OSError:
    _DATA_DIR_UNDER_RENDER_DISK = False

if _RENDER_ENV and (
    not _DATA_DIR_UNDER_RENDER_DISK or not _RENDER_DATA_ROOT.is_mount()
):
    logging.warning(
        "[STORAGE] Los datos no tienen un disco persistente montado en /var/data. "
        "Configura un Persistent Disk de Render en /var/data y define PAPU_DATA_DIR "
        "como /var/data (o una subcarpeta dentro). De lo contrario, los datos se perderan al desplegar."
    )
