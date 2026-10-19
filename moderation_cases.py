"""Formato comun de registros de moderacion para IA y reportes de usuarios."""
import re

import discord
from papu_store import load_json, save_json


def next_case_id(guild_id: int) -> int:
    """Reserva un identificador consecutivo por servidor sin guardar el texto denunciado."""
    counters = load_json("moderation_case_counters.json", {})
    key = str(guild_id)
    try:
        current = int(counters.get(key, 0)) + 1
    except (TypeError, ValueError):
        current = 1
    counters[key] = current
    save_json("moderation_case_counters.json", counters)
    return current


def _clean(value, limit=1000):
    text = discord.utils.escape_mentions(str(value or "—"))
    text = text.replace("`", "ˋ").replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text or "—"


def make_case_embed(
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
    color: discord.Color | None = None,
    created_at=None,
) -> discord.Embed:
    """Construye el informe con campos estables para que el staff lo lea de un vistazo."""
    timestamp = created_at or discord.utils.utcnow()
    severity_text = f"gravedad {severity}" if isinstance(severity, int) else f"gravedad {severity}"
    if isinstance(confidence, (float, int)):
        confidence_text = f"{float(confidence):.0%}"
    else:
        confidence_text = str(confidence or "sin evaluar")
    verdict = f"{_clean(category, 80)} · {severity_text} · confianza {confidence_text}"
    embed = discord.Embed(
        title=_clean(title, 240),
        color=color or discord.Color.orange(),
        timestamp=timestamp,
    )
    user_value = f"<@{int(user_id)}> (`{int(user_id)}`)"
    if username:
        user_value += f"\n{_clean(username, 150)}"
    embed.add_field(name="usuario", value=user_value[:1024], inline=False)
    channel_value = f"<#{int(channel_id)}>" if channel_id else _clean(channel_name, 200)
    if channel_name and channel_name not in {"—", ""}:
        channel_value += f"\n{_clean(channel_name, 150)}"
    embed.add_field(name="canal", value=channel_value[:1024], inline=False)
    embed.add_field(name="veredicto", value=_clean(verdict, 1024), inline=False)
    embed.add_field(name="razon", value=_clean(reason, 1024), inline=False)
    embed.add_field(name="mensaje", value=f"`{_clean(message_text, 900)}`"[:1024], inline=False)
    if reporter:
        embed.add_field(name="reportado por", value=_clean(reporter, 1024), inline=False)
    embed.add_field(name="estado", value=_clean(status, 1024), inline=False)
    if message_url and re.match(r"^https://(?:(?:ptb|canary)\.)?discord\.com/channels/\d+/\d+/\d+$", message_url):
        label = _clean(channel_name or "canal", 100) + " · mensaje"
        embed.add_field(name="ir al mensaje", value=f"[{label}]({message_url})", inline=False)
    embed.add_field(
        name="id de infraccion",
        value=f"{int(case_id)} • <t:{int(timestamp.timestamp())}:f>",
        inline=False,
    )
    embed.set_footer(text="PapuCollective · registro de moderacion")
    return embed
