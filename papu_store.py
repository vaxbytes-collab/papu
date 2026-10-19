"""Persistencia de Papu: PostgreSQL cuando DATABASE_URL esta configurada, JSON local si no."""
import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock

import psycopg
from psycopg.types.json import Jsonb

PERSISTED_JSON_FILES = (
    "pets.json",
    "utility_settings.json",
    "reminders.json",
    "events.json",
    "suggestions.json",
    "log_channels.json",
    "warns.json",
    "moderation_settings.json",
    "chat_histories.json",
    "security_settings.json",
    "afk.json",
    "staff_notes.json",
    "security_incidents.json",
    "moderation_case_counters.json",
)
_LOCK = RLock()


def _database_url() -> str:
    """Lee la URL dinamicamente para respetar el entorno del proceso."""
    return str(os.getenv("DATABASE_URL", "") or "").strip()


def _select_data_dir(environ=None, cwd=None) -> Path:
    """Elige un directorio local para ejecucion sin PostgreSQL."""
    env = os.environ if environ is None else environ
    base = Path(cwd) if cwd is not None else Path.cwd()
    is_render = bool(env.get("RENDER_SERVICE_ID") or env.get("RENDER_INSTANCE_ID"))
    configured = str(env.get("PAPU_DATA_DIR", "") or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_absolute():
            return path
        return (Path("/var/data") if is_render else base) / path
    if is_render:
        return Path("/var/data")
    return base / "data"


DATA_DIR = _select_data_dir()


def _connect():
    """Abre una conexion nueva; el proveedor administra disponibilidad y backups."""
    url = _database_url()
    if not url:
        raise RuntimeError("DATABASE_URL no esta configurada")
    return psycopg.connect(url, connect_timeout=8)


def data_path(name: str) -> Path:
    """Devuelve una ruta dentro del directorio de datos local."""
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("El nombre debe ser un nombre de archivo, no una ruta")
    return DATA_DIR / name


def _legacy_dirs():
    """Directorios donde las versiones anteriores de Papu pudieron guardar JSON."""
    root = Path.cwd()
    return (DATA_DIR, root, root / "data", Path("/var/data"))


def _migrate_legacy_data(legacy_dirs=None) -> int:
    """En modo local, copia archivos antiguos sin sobrescribir archivos existentes."""
    if legacy_dirs is None:
        legacy_dirs = _legacy_dirs()
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
                logging.info("[STORAGE] Datos JSON antiguos migrados: %s", filename)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                logging.exception("[STORAGE] No se pudo migrar el archivo %s", source)
    return copied


def _migrate_legacy_data_to_postgres(conn, legacy_dirs=None) -> int:
    """Importa JSON antiguos solo cuando su clave aun no existe en PostgreSQL."""
    imported = 0
    for legacy_dir in (legacy_dirs if legacy_dirs is not None else _legacy_dirs()):
        source_dir = Path(legacy_dir)
        for filename in PERSISTED_JSON_FILES:
            source = source_dir / filename
            try:
                if not source.is_file():
                    continue
                value = json.loads(source.read_text(encoding="utf-8"))
                result = conn.execute(
                    """
                    INSERT INTO papu_json_store (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO NOTHING
                    RETURNING key
                    """,
                    (filename, Jsonb(value)),
                ).fetchone()
                if result:
                    imported += 1
                    logging.info("[STORAGE] Datos antiguos importados a PostgreSQL: %s", filename)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                logging.exception("[STORAGE] No se pudo importar el archivo antiguo %s", source)
    return imported


def init_storage() -> str:
    """Inicializa el backend antes de cargar comandos; no cambia de backend silenciosamente."""
    if _database_url():
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papu_json_store (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            imported = _migrate_legacy_data_to_postgres(conn)
        logging.info("[STORAGE] PostgreSQL conectado; %s archivo(s) JSON antiguo(s) importado(s)", imported)
        return "postgresql"

    _migrate_legacy_data()
    _warn_if_render_filesystem_is_ephemeral()
    logging.warning("[STORAGE] DATABASE_URL no configurada: usando almacenamiento local JSON")
    return "json"


def _warn_if_render_filesystem_is_ephemeral() -> None:
    render_env = bool(os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER_INSTANCE_ID"))
    render_root = Path("/var/data")
    try:
        data_dir_under_render_disk = DATA_DIR.resolve().is_relative_to(render_root)
    except OSError:
        data_dir_under_render_disk = False
    if render_env and (not data_dir_under_render_disk or not render_root.is_mount()):
        logging.warning(
            "[STORAGE] No hay almacenamiento persistente confirmado. Configura DATABASE_URL "
            "o un Persistent Disk de Render; el sistema de archivos normal se pierde al desplegar."
        )


def load_json(name: str, default):
    """Carga JSON de PostgreSQL si esta configurado; de lo contrario, del disco local."""
    if _database_url():
        with _connect() as conn:
            row = conn.execute(
                "SELECT value FROM papu_json_store WHERE key = %s",
                (name,),
            ).fetchone()
        if row is None:
            return default
        value = row[0]
        return value if isinstance(value, type(default)) else default

    path = data_path(name)
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, type(default)) else default
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def save_json(name: str, value) -> None:
    """Guarda en PostgreSQL o en archivos locales, sin cambiar de backend en caso de fallo."""
    if _database_url():
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO papu_json_store (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = NOW()
                """,
                (name, Jsonb(value)),
            )
        return

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
