"""Seleccion y compatibilidad de modelos de Groq."""
import os

DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
_RETIRED_REPLACEMENTS = {
    "llama-3.1-8b-instant": "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
}
_warned_settings = set()


def get_groq_model(setting_name: str) -> str:
    """Retorna el modelo configurado y migra IDs retirados a sus reemplazos."""
    requested = (os.getenv(setting_name) or DEFAULT_GROQ_MODEL).strip()
    replacement = _RETIRED_REPLACEMENTS.get(requested)
    if replacement:
        if setting_name not in _warned_settings:
            print(
                f"[WARN] {setting_name} usa el modelo retirado {requested!r}; "
                f"se usara {replacement!r}. Actualiza la variable de entorno."
            )
            _warned_settings.add(setting_name)
        return replacement
    return requested
