"""Almacenamiento JSON local con escrituras atomicas para Papu."""
import json
import os
import tempfile
from pathlib import Path
from threading import RLock

DATA_DIR = Path(os.getenv("PAPU_DATA_DIR", "."))
_LOCK = RLock()


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
