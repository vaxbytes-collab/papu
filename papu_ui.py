"""Sistema visual compartido para las respuestas de Papu en Discord."""
from __future__ import annotations

import discord

PALETTE = {
    "midnight": 0x111827,
    "cyan": 0x67E8F9,
    "violet": 0xA78BFA,
    "amber": 0xFDBA74,
    "success": 0x6EE7B7,
    "warning": 0xFCD34D,
    "danger": 0xFB7185,
    "info": 0x7DD3FC,
    "muted": 0x9CA3AF,
}
_LEGACY_COLORS = {
    0x5865F2: PALETTE["violet"],
    0x3498DB: PALETTE["cyan"],
    0x57F287: PALETTE["success"],
    0x2ECC71: PALETTE["success"],
    0xED4245: PALETTE["danger"],
    0xE74C3C: PALETTE["danger"],
    0xE67E22: PALETTE["amber"],
    0xFAA61A: PALETTE["amber"],
    0xF1C40F: PALETTE["amber"],
    0xFEE75C: PALETTE["amber"],
    0x9B59B6: PALETTE["violet"],
}
_FEEDBACK = {
    "success": ("✅", "Todo listo", PALETTE["success"]),
    "info": ("🐈", "Papu", PALETTE["cyan"]),
    "warning": ("⚠️", "Revisa esto", PALETTE["warning"]),
    "error": ("❌", "No se pudo completar", PALETTE["danger"]),
    "ai": ("✨", "Papu AI", PALETTE["violet"]),
}


def _resolve_color(color=None) -> discord.Color:
    if color is None:
        return discord.Color(PALETTE["cyan"])
    value = getattr(color, "value", color)
    try:
        value = int(value)
    except (TypeError, ValueError):
        return discord.Color(PALETTE["cyan"])
    return discord.Color(_LEGACY_COLORS.get(value, value))


def branded_embed(*args, color=None, colour=None, footer=None, **kwargs) -> discord.Embed:
    """Crea una tarjeta con paleta, pie y timestamp compartidos."""
    chosen_color = color if color is not None else colour
    kwargs.setdefault("timestamp", discord.utils.utcnow())
    embed = discord.Embed(*args, color=_resolve_color(chosen_color), **kwargs)
    footer_text = footer or embed.footer.text or "🐈 Papu"
    if "PapuCollective" not in footer_text:
        footer_text = f"{footer_text} • PapuCollective"
    embed.set_footer(text=footer_text[:2048])
    return embed


def feedback_embed(description: str, *, title=None, tone="info", footer=None) -> discord.Embed:
    """Tarjeta compacta para confirmaciones, avisos y errores."""
    icon, default_title, color = _FEEDBACK.get(tone, _FEEDBACK["info"])
    heading = title or default_title
    if not heading.startswith(icon):
        heading = f"{icon} {heading}"
    return branded_embed(
        title=heading[:256],
        description=str(description or "La operación terminó sin detalles.")[:3900],
        color=color,
        footer=footer or "Papu • Estado de la operación",
    )


async def send_feedback(interaction: discord.Interaction, description: str, *, title=None,
                        tone="info", ephemeral=True, **kwargs):
    """Envía feedback coherente y desactiva menciones accidentales."""
    kwargs.setdefault("allowed_mentions", discord.AllowedMentions.none())
    embed = feedback_embed(description, title=title, tone=tone)
    if interaction.response.is_done():
        return await interaction.followup.send(embed=embed, ephemeral=ephemeral, **kwargs)
    return await interaction.response.send_message(embed=embed, ephemeral=ephemeral, **kwargs)


def progress_bar(value, maximum=100, width=12) -> str:
    """Barra textual legible en móvil con valores acotados."""
    try:
        maximum = max(1, int(maximum))
    except (TypeError, ValueError):
        maximum = 100
    try:
        value = max(0, min(maximum, int(value)))
    except (TypeError, ValueError):
        value = 0
    try:
        width = max(1, min(24, int(width)))
    except (TypeError, ValueError):
        width = 12
    filled = round(value / maximum * width)
    return f"{'▰' * filled}{'▱' * (width - filled)}"


def status_label(enabled: bool) -> str:
    return "🟢 Activado" if enabled else "⚪ Desactivado"
