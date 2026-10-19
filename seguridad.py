"""Protecciones opt-in contra spam, invitaciones no deseadas y picos de entradas."""
import re
import time
from collections import defaultdict, deque
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from papu_store import load_json, save_json

INVITE_RE = re.compile(
    r"(?i)(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/[a-z0-9-]+"
)


def contains_discord_invite(content: str) -> bool:
    """Solo detecta invitaciones de Discord; los enlaces normales no se bloquean."""
    return bool(INVITE_RE.search(content or ""))


def count_recent_events(events: deque, now: float, window_seconds: int) -> int:
    """Elimina eventos antiguos y devuelve cuántos siguen dentro de la ventana."""
    cutoff = now - window_seconds
    while events and events[0] < cutoff:
        events.popleft()
    return len(events)


class Seguridad(commands.Cog):
    """Funciones automáticas opt-in. No expulsa ni banea por una detección automática."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = load_json("security_settings.json", {})
        self.log_channels = load_json("log_channels.json", {})
        self.message_times = defaultdict(deque)
        self.join_times = defaultdict(deque)
        self.last_spam_action = {}
        self.last_raid_alert = {}

    def guild_config(self, guild_id: int) -> dict:
        return self.settings.setdefault(str(guild_id), {})

    def save_settings(self):
        save_json("security_settings.json", self.settings)

    async def security_log(self, guild: discord.Guild, text: str):
        """Usa el canal de logs configurado, sin publicar alertas en canales generales."""
        current_channels = load_json("log_channels.json", {})
        raw_channel_id = current_channels.get(str(guild.id))
        if not raw_channel_id:
            return
        try:
            channel = guild.get_channel(int(raw_channel_id))
        except (TypeError, ValueError):
            return
        if channel is None:
            return
        try:
            await channel.send(
                text[:1800],
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            return

    @app_commands.command(name="antispam", description="Activa o configura la proteccion contra spam")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antispam(
        self,
        interaction: discord.Interaction,
        activar: bool,
        limite: app_commands.Range[int, 3, 20] = 6,
        ventana: app_commands.Range[int, 3, 30] = 8,
        timeout_segundos: app_commands.Range[int, 0, 600] = 60,
    ):
        cfg = self.guild_config(interaction.guild_id)
        cfg["anti_spam"] = {
            "enabled": activar,
            "limit": limite,
            "window": ventana,
            "timeout": timeout_segundos,
        }
        self.save_settings()
        if activar:
            description = (
                f"anti-spam **activado**: {limite} mensajes en {ventana} s. "
                f"al superar el limite, borrare el mensaje y aplicare timeout de "
                f"{timeout_segundos} s (0 = sin timeout)."
            )
        else:
            description = "anti-spam **desactivado**. los mensajes ya no se moderaran automaticamente por frecuencia."
        await interaction.response.send_message(description, ephemeral=True)
        await self.security_log(interaction.guild, f"🛡️ Configuracion anti-spam cambiada por {interaction.user}: {description}")

    @app_commands.command(name="antiraid", description="Alerta al staff si entran muchas cuentas en poco tiempo")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antiraid(
        self,
        interaction: discord.Interaction,
        activar: bool,
        umbral: app_commands.Range[int, 3, 50] = 8,
        ventana: app_commands.Range[int, 3, 60] = 10,
    ):
        cfg = self.guild_config(interaction.guild_id)
        cfg["anti_raid"] = {
            "enabled": activar,
            "threshold": umbral,
            "window": ventana,
        }
        self.save_settings()
        if activar:
            description = (
                f"anti-raid **activado**: avisare al canal de logs si entran "
                f"{umbral} miembros en {ventana} s. esta proteccion alerta al staff; "
                "no banea ni expulsa automaticamente."
            )
        else:
            description = "anti-raid **desactivado**."
        await interaction.response.send_message(description, ephemeral=True)
        await self.security_log(interaction.guild, f"🚨 Configuracion anti-raid cambiada por {interaction.user}: {description}")

    @app_commands.command(name="antienlaces", description="Activa el bloqueo de invitaciones de Discord")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antienlaces(self, interaction: discord.Interaction, activar: bool):
        cfg = self.guild_config(interaction.guild_id)
        cfg["anti_invites"] = {"enabled": activar}
        self.save_settings()
        status = "activado: eliminare invitaciones de Discord de miembros sin permiso de moderacion." if activar else "desactivado."
        await interaction.response.send_message(f"filtro de invitaciones {status}", ephemeral=True)
        await self.security_log(interaction.guild, f"🔗 Configuracion anti-invitaciones cambiada por {interaction.user}: {status}")

    @app_commands.command(name="seguridad_estado", description="Muestra el estado de las protecciones automáticas")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def seguridad_estado(self, interaction: discord.Interaction):
        cfg = self.guild_config(interaction.guild_id)
        spam = cfg.get("anti_spam", {})
        raid = cfg.get("anti_raid", {})
        invites = cfg.get("anti_invites", {})
        embed = discord.Embed(title="🛡️ Seguridad de Papu", color=discord.Color.blurple())
        embed.add_field(
            name="Anti-spam",
            value=(
                f"{'activado' if spam.get('enabled') else 'desactivado'} · "
                f"{spam.get('limit', 6)} mensajes / {spam.get('window', 8)} s · "
                f"timeout {spam.get('timeout', 60)} s"
            ),
            inline=False,
        )
        embed.add_field(
            name="Anti-raid",
            value=(
                f"{'activado' if raid.get('enabled') else 'desactivado'} · "
                f"{raid.get('threshold', 8)} miembros / {raid.get('window', 10)} s · solo alertas"
            ),
            inline=False,
        )
        embed.add_field(
            name="Invitaciones",
            value="bloqueo activado" if invites.get("enabled") else "bloqueo desactivado",
            inline=False,
        )
        embed.set_footer(text="Configura un canal de logs con /setlogchannel para recibir alertas.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot or message.webhook_id:
            return
        member = message.author
        if not isinstance(member, discord.Member):
            return
        if member.guild_permissions.manage_messages or member.guild_permissions.administrator:
            return

        cfg = self.settings.get(str(message.guild.id), {})

        invite_cfg = cfg.get("anti_invites", {})
        if invite_cfg.get("enabled") and contains_discord_invite(message.content):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                # No repitas el mensaje ni bloquees el resto de la moderacion si Discord lo rechaza.
                await self.security_log(message.guild, f"⚠️ Detecte una invitacion en #{message.channel.name}, pero no pude borrarla.")
                return
            await self.security_log(
                message.guild,
                f"🔗 Eliminada invitacion de {member} ({member.id}) en #{message.channel.name}.",
            )
            return

        spam_cfg = cfg.get("anti_spam", {})
        if not spam_cfg.get("enabled"):
            return

        window = max(3, min(int(spam_cfg.get("window", 8)), 30))
        limit = max(3, min(int(spam_cfg.get("limit", 6)), 20))
        timeout_seconds = max(0, min(int(spam_cfg.get("timeout", 60)), 600))
        now = time.monotonic()
        key = (message.guild.id, member.id)
        events = self.message_times[key]
        events.append(now)
        count_recent_events(events, now, window)
        if len(events) < limit:
            return

        events.clear()
        last_action = self.last_spam_action.get(key, 0)
        if now - last_action < 30:
            return
        self.last_spam_action[key] = now

        try:
            await message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        action = "mensaje eliminado"
        if timeout_seconds:
            try:
                await member.timeout(
                    timedelta(seconds=timeout_seconds),
                    reason=f"Anti-spam: {limit} mensajes en {window} segundos",
                )
                action += f" y timeout de {timeout_seconds} s"
            except (discord.Forbidden, discord.HTTPException):
                action += "; no pude aplicar timeout (revisa mis permisos)"
        await self.security_log(
            message.guild,
            f"🚨 Anti-spam: {member} ({member.id}) en #{message.channel.name}; "
            f"{limit} mensajes en {window} s. Accion: {action}.",
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = self.settings.get(str(member.guild.id), {}).get("anti_raid", {})
        if not cfg.get("enabled"):
            return
        window = max(3, min(int(cfg.get("window", 10)), 60))
        threshold = max(3, min(int(cfg.get("threshold", 8)), 50))
        now = time.monotonic()
        events = self.join_times[member.guild.id]
        events.append(now)
        count_recent_events(events, now, window)
        if len(events) < threshold:
            return
        last_alert = self.last_raid_alert.get(member.guild.id, 0)
        if now - last_alert < 120:
            return
        self.last_raid_alert[member.guild.id] = now
        await self.security_log(
            member.guild,
            f"🚨 **Posible raid**: han entrado {len(events)} miembros en {window} s. "
            "No se aplicaron expulsiones ni baneos automaticos; revisa la lista de miembros.",
        )


async def setup(bot):
    await bot.add_cog(Seguridad(bot))
