"""Cola persistente de memes seleccionados por el staff y publicación diaria."""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands, tasks

from papu_store import load_json, save_json
from papu_ui import branded_embed, send_feedback

STATE_FILE = "meme_daily.json"
MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def parse_publish_time(value: str) -> str:
    """Valida y normaliza una hora local en formato HH:MM."""
    try:
        parsed = datetime.strptime(str(value).strip(), "%H:%M")
    except (TypeError, ValueError) as exc:
        raise ValueError("La hora debe tener formato HH:MM, por ejemplo 12:30.") from exc
    return parsed.strftime("%H:%M")


def validate_timezone(value: str) -> str:
    """Devuelve una zona IANA válida para el horario de publicación."""
    zone = str(value or "").strip()
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("Zona horaria no válida. Usa una zona IANA, por ejemplo Europe/Madrid.") from exc
    return zone


def publication_is_due(now: datetime, publish_time: str, last_published_date: str) -> bool:
    """Comprueba si toca publicar hoy y evita repetir la fecha local."""
    today = now.date().isoformat()
    if last_published_date == today:
        return False
    hour, minute = map(int, parse_publish_time(publish_time).split(":"))
    return (now.hour, now.minute) >= (hour, minute)


def initial_state():
    return {"guilds": {}}


class MemeDiario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = load_json(STATE_FILE, initial_state())
        if not isinstance(self.state, dict) or not isinstance(self.state.get("guilds"), dict):
            self.state = initial_state()
        self.publication_loop.start()

    def cog_unload(self):
        self.publication_loop.cancel()

    def guild_state(self, guild_id):
        return self.state.setdefault("guilds", {}).setdefault(str(guild_id), {
            "publication_channel_id": None,
            "archive_channel_id": None,
            "publish_time": "12:00",
            "timezone": "Europe/Madrid",
            "queue": [],
            "last_published_date": None,
            "last_published_message_id": None,
            "next_id": 1,
        })

    def save(self):
        save_json(STATE_FILE, self.state)

    @tasks.loop(seconds=30)
    async def publication_loop(self):
        for guild_id, config in list(self.state.get("guilds", {}).items()):
            if not isinstance(config, dict) or not config.get("publication_channel_id"):
                continue
            queue = config.get("queue", [])
            if not isinstance(queue, list) or not queue:
                continue
            try:
                timezone = validate_timezone(config.get("timezone", "Europe/Madrid"))
                now = datetime.now(ZoneInfo(timezone))
                if not publication_is_due(now, config.get("publish_time", "12:00"),
                                          str(config.get("last_published_date") or "")):
                    continue
                guild = self.bot.get_guild(int(guild_id))
                if guild is None:
                    continue
                channel = guild.get_channel(int(config["publication_channel_id"]))
                if channel is None or not hasattr(channel, "send"):
                    continue
                await self.publish_next(guild, config, channel, now.date().isoformat())
            except (ValueError, TypeError, KeyError, discord.HTTPException):
                # Un fallo no elimina el meme: se volverá a intentar en el siguiente ciclo.
                continue

    @publication_loop.before_loop
    async def before_publication_loop(self):
        await self.bot.wait_until_ready()

    async def publish_next(self, guild, config, channel, publish_date=None):
        queue = config.get("queue", [])
        if not queue:
            return False
        item = queue[0]
        archive_channel = guild.get_channel(int(config.get("archive_channel_id") or 0))
        if archive_channel is None:
            return False
        try:
            source_message = await archive_channel.fetch_message(int(item["archive_message_id"]))
            if not source_message.attachments:
                return False
            attachment = source_message.attachments[0]
            file = await attachment.to_file()
            caption = str(item.get("caption") or "").strip()
            number = int(item.get("number", 0))
            embed = branded_embed(
                title=f"🗿 momo del dia #{number:03d}",
                description=caption[:3500] if caption else "momo seleccionado por el staff :v",
                color=0xA78BFA,
                footer=f"Meme diario • ID {item.get('id', 'unknown')}",
            )
            await channel.send(embed=embed, file=file, allowed_mentions=discord.AllowedMentions.none())
        except (discord.HTTPException, KeyError, TypeError, ValueError):
            return False
        config["queue"] = queue[1:]
        config["last_published_date"] = publish_date or datetime.now(
            ZoneInfo(config.get("timezone", "Europe/Madrid"))
        ).date().isoformat()
        self.save()
        return True

    @app_commands.command(name="meme_configurar", description="Configura el canal y horario del meme diario")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme_configurar(
        self,
        interaction: discord.Interaction,
        canal_publicacion: discord.TextChannel,
        canal_archivo: discord.TextChannel,
        hora: app_commands.Range[str, 5, 5] = "12:00",
        zona_horaria: str = "Europe/Madrid",
    ):
        try:
            clean_time = parse_publish_time(hora)
            clean_timezone = validate_timezone(zona_horaria)
        except ValueError as exc:
            return await send_feedback(interaction, str(exc), title="Configuración no válida", tone="warning")
        config = self.guild_state(interaction.guild_id)
        config["publication_channel_id"] = canal_publicacion.id
        config["archive_channel_id"] = canal_archivo.id
        config["publish_time"] = clean_time
        config["timezone"] = clean_timezone
        self.save()
        await send_feedback(
            interaction,
            f"Canal de memes: {canal_publicacion.mention}\nArchivo privado del staff: {canal_archivo.mention}\nPublicación diaria: **{clean_time} ({clean_timezone})**.\nLa publicación automática queda activa cuando haya memes pendientes.",
            title="Meme diario configurado",
            tone="success",
            ephemeral=True,
        )

    @app_commands.command(name="meme_subir", description="Añade una imagen a la cola del meme diario")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme_subir(
        self,
        interaction: discord.Interaction,
        imagen: discord.Attachment,
        texto: app_commands.Range[str, 0, 500] = "",
    ):
        config = self.guild_state(interaction.guild_id)
        archive_channel_id = config.get("archive_channel_id")
        if not config.get("publication_channel_id") or not archive_channel_id:
            return await send_feedback(
                interaction,
                "Primero configura los canales con /meme_configurar.",
                title="Falta configurar el meme diario",
                tone="warning",
            )
        if imagen.content_type not in ALLOWED_IMAGE_TYPES:
            return await send_feedback(interaction, "Adjunta una imagen PNG, JPG, GIF o WebP.", title="Formato no compatible", tone="warning")
        if imagen.size > MAX_IMAGE_BYTES:
            return await send_feedback(interaction, "La imagen debe pesar 8 MB o menos.", title="Imagen demasiado grande", tone="warning")
        archive_channel = interaction.guild.get_channel(int(archive_channel_id))
        if archive_channel is None:
            return await send_feedback(interaction, "No encuentro el canal de archivo. Vuelve a ejecutar /meme_configurar.", title="Canal de archivo no disponible", tone="error")
        try:
            copied_file = await imagen.to_file()
            archived = await archive_channel.send(
                content=f"🗃️ Meme enviado por {discord.utils.escape_mentions(interaction.user.display_name)}"
                        + (f"\n{discord.utils.escape_mentions(texto)}" if texto else ""),
                file=copied_file,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            return await send_feedback(interaction, "No pude guardar la imagen en el canal de archivo. Revisa mis permisos y el límite de subida.", title="No se pudo guardar", tone="error")
        number = int(config.get("next_id", 1))
        item = {
            "id": uuid.uuid4().hex[:10],
            "number": number,
            "archive_message_id": archived.id,
            "caption": str(texto or "").strip()[:500],
            "uploaded_by": interaction.user.id,
            "queued_at": int(time.time()),
        }
        config.setdefault("queue", []).append(item)
        config["next_id"] = number + 1
        self.save()
        await send_feedback(
            interaction,
            f"Guardado como meme **#{number:03d}**. Hay **{len(config['queue'])}** meme(s) en cola.",
            title="Meme añadido",
            tone="success",
            ephemeral=True,
        )

    @app_commands.command(name="meme_cola", description="Consulta los memes pendientes")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme_cola(self, interaction: discord.Interaction):
        config = self.guild_state(interaction.guild_id)
        queue = config.get("queue", [])
        if not queue:
            return await send_feedback(interaction, "La cola está vacía. Usa /meme_subir para añadir el siguiente momo.", title="Cola de memes", tone="info")
        lines = []
        for item in queue[:15]:
            caption = str(item.get("caption") or "sin texto").replace("\n", " ")[:100]
            lines.append(f"**#{int(item.get('number', 0)):03d}** · {discord.utils.escape_markdown(caption)}")
        if len(queue) > 15:
            lines.append(f"… y {len(queue) - 15} más.")
        await send_feedback(interaction, "\n".join(lines), title=f"Cola de memes ({len(queue)})", tone="info")

    @app_commands.command(name="meme_publicar", description="Publica ahora el siguiente meme de la cola")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme_publicar(self, interaction: discord.Interaction):
        config = self.guild_state(interaction.guild_id)
        if not config.get("publication_channel_id") or not config.get("archive_channel_id"):
            return await send_feedback(interaction, "Primero configura los canales con /meme_configurar.", title="Falta configuración", tone="warning")
        if not config.get("queue"):
            return await send_feedback(interaction, "No hay memes pendientes. Usa /meme_subir.", title="Cola vacía", tone="info")
        channel = interaction.guild.get_channel(int(config["publication_channel_id"]))
        if channel is None:
            return await send_feedback(interaction, "No encuentro el canal de publicación.", title="Canal no disponible", tone="error")
        await interaction.response.defer(ephemeral=True, thinking=True)
        ok = await self.publish_next(interaction.guild, config, channel)
        if ok:
            await interaction.followup.send(embed=branded_embed(title="✅ Meme publicado", description="El siguiente meme ya está en el canal configurado.", color=0x6EE7B7), ephemeral=True)
        else:
            await interaction.followup.send(embed=branded_embed(title="⚠️ No se pudo publicar", description="El meme sigue en la cola. Comprueba que el archivo siga disponible y que Papu pueda ver ambos canales.", color=0xFCD34D), ephemeral=True)


async def setup(bot):
    await bot.add_cog(MemeDiario(bot))
