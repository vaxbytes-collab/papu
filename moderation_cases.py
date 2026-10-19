"""Formato Markdown compartido para informes de moderacion y reportes."""
import re

import discord
from papu_store import load_json, save_json


def next_case_id(guild_id: int) -> int:
    """Reserva un identificador consecutivo por servidor, sin guardar el texto reportado."""
    counters = load_json("moderation_case_counters.json", {})
    key = str(guild_id)
    try:
        current = int(counters.get(key, 0)) + 1
    except (TypeError, ValueError):
        current = 1
    counters[key] = current
    save_json("moderation_case_counters.json", counters)
    return current


def _clean(value, limit=500, flatten=False):
    text = str(value or "—")
    if flatten:
        text = " ".join(text.split())
    text = discord.utils.escape_mentions(text)
    text = text.replace("`", "ˋ").replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text or "—"


def make_case_content(
    *,
    case_id: int,
    title: str,
    username: str,
    user_id: int,
    channel_name: str,
    channel_id: int | None,
    category: str,
    severity: int | str,
    confidence: float | str | None,
    reason: str,
    message_text: str,
    status: str,
    message_url: str | None = None,
    reporter: str | None = None,
    created_at=None,
) -> str:
    """Genera un mensaje de Discord con etiquetas Markdown, similar a una ficha de infraccion."""
    timestamp = created_at or discord.utils.utcnow()
    severity_text = f"gravedad {severity}"
    if isinstance(confidence, (float, int)):
        confidence_text = f"{float(confidence):.0%}"
    else:
        confidence_text = str(confidence or "sin evaluar")
    verdict = f"{_clean(category, 70, True)} · {severity_text} · confianza {confidence_text}"

    clean_title = _clean(title, 100, True)
    if "caso grave" in clean_title.lower() and "🚨" in clean_title:
        heading = "**[🚨](https://discord.com/assets/8d433206d7a0fe81.svg) caso grave**"
    else:
        heading = f"**{clean_title}**"

    user_line = f"**<@{int(user_id)}>** (`{int(user_id)}`)"
    channel_line = f"<#{int(channel_id)}>" if channel_id else f"**{_clean(channel_name, 120, True)}**"
    if message_url and re.fullmatch(r"https://(?:(?:ptb|canary)\.)?discord\.com/channels/\d+/\d+/\d+", message_url):
        link_label = _clean(channel_name or "canal", 90, True) + "Mensaje⁠"
        message_link = f"[{link_label}]({message_url})"
    else:
        message_link = "enlace al mensaje no disponible"

    lines = [
        heading,
        "",
        "**usuario**",
        user_line,
        "",
        "**canal**",
        channel_line,
        "",
        "**veredicto**",
        _clean(verdict, 150, True),
        "",
        "**razon**",
        _clean(reason, 420),
        "",
        "**mensaje**",
        f"`{_clean(message_text, 430, True)}`",
    ]
    if reporter:
        lines.extend(["", "**reportado por**", _clean(reporter, 120, True)])
    lines.extend([
        "",
        "**estado**",
        _clean(status, 250, True),
        "",
        "**ir al mensaje**",
        message_link,
        "",
        f"**id de infraccion: {int(case_id)}** • <t:{int(timestamp.timestamp())}:f>",
    ])
    content = "\n".join(lines)
    if len(content) > 1950:
        # Ultima salvaguarda frente al limite de 2000 caracteres de un mensaje de Discord.
        content = content[:1947] + "…"
    return content
