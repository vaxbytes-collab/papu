"""Herramientas de organizacion, comunidad y administracion para Papu."""
import asyncio
import random
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from papu_store import load_json, save_json


class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_json("utility_settings.json", {})
        self.reminders = load_json("reminders.json", [])
        self.events = load_json("events.json", {})
        self.suggestions = load_json("suggestions.json", {})
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    def guild_settings(self, guild_id):
        return self.settings.setdefault(str(guild_id), {})

    @tasks.loop(seconds=15)
    async def reminder_loop(self):
        now = time.time()
        due, pending = [], []
        for item in self.reminders:
            (due if item.get("due", now + 1) <= now else pending).append(item)
        if len(due) == 0:
            return
        self.reminders = pending
        save_json("reminders.json", self.reminders)
        for item in due:
            channel = self.bot.get_channel(int(item.get("channel_id", 0)))
            if channel:
                try:
                    user = await self.bot.fetch_user(int(item["user_id"]))
                    await channel.send(f"⏰ {user.mention}, recordatorio: {discord.utils.escape_mentions(item['text'])}",
                                       allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                except (discord.HTTPException, KeyError, ValueError):
                    continue

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="recordatorio", description="Guarda un recordatorio persistente (1 min a 30 dias)")
    async def recordatorio(self, interaction: discord.Interaction,
                           minutos: app_commands.Range[int, 1, 43200], texto: app_commands.Range[str, 1, 500]):
        self.reminders.append({"user_id": interaction.user.id, "guild_id": interaction.guild_id,
                               "channel_id": interaction.channel_id, "text": str(texto),
                               "due": time.time() + minutos * 60})
        save_json("reminders.json", self.reminders)
        await interaction.response.send_message(f"⏰ Te aviso en {minutos} minutos. Recordatorio guardado.", ephemeral=True)

    @app_commands.command(name="encuesta", description="Crea una encuesta con hasta cuatro opciones")
    async def encuesta(self, interaction: discord.Interaction, pregunta: app_commands.Range[str, 1, 180],
                       opcion_a: app_commands.Range[str, 1, 80],
                       opcion_b: app_commands.Range[str, 1, 80],
                       opcion_c: str = "", opcion_d: str = ""):
        options = [x.strip() for x in (opcion_a, opcion_b, opcion_c, opcion_d) if x and x.strip()]
        if len(options) < 2 or len(set(options)) != len(options):
            return await interaction.response.send_message("Pon al menos dos opciones distintas.", ephemeral=True)
        embed = discord.Embed(title=f"📊 {pregunta}", color=discord.Color.blurple())
        marks = ["🇦", "🇧", "🇨", "🇩"]
        embed.description = "\n".join(f"{marks[i]} {discord.utils.escape_mentions(value)}" for i, value in enumerate(options))
        embed.set_footer(text=f"Encuesta de {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for mark in marks[:len(options)]:
            await message.add_reaction(mark)

    @app_commands.command(name="evento_crear", description="Publica un evento de la comunidad")
    @app_commands.checks.has_permissions(manage_events=True)
    async def evento_crear(self, interaction: discord.Interaction,
                           nombre: app_commands.Range[str, 1, 100],
                           fecha: app_commands.Range[str, 10, 25],
                           detalles: app_commands.Range[str, 1, 800]):
        try:
            dt = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return await interaction.response.send_message("Fecha invalida. Usa ISO 8601, por ejemplo 2026-12-31T18:00+01:00.", ephemeral=True)
        if dt.timestamp() <= time.time():
            return await interaction.response.send_message("La fecha debe estar en el futuro.", ephemeral=True)
        key = str(interaction.guild_id)
        self.events.setdefault(key, []).append({"name": nombre, "date": dt.isoformat(),
            "details": detalles, "creator": interaction.user.id})
        save_json("events.json", self.events)
        embed = discord.Embed(title=f"📅 {nombre}", description=detalles, color=discord.Color.green())
        embed.add_field(name="Fecha", value=discord.utils.format_dt(dt, "F"))
        embed.set_footer(text=f"Organizado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🎉")

    @app_commands.command(name="eventos", description="Muestra los proximos eventos guardados")
    async def eventos(self, interaction: discord.Interaction):
        entries = self.events.get(str(interaction.guild_id), [])
        if not entries:
            return await interaction.response.send_message("Todavia no hay eventos guardados.", ephemeral=True)
        embed = discord.Embed(title="📅 Agenda de Papu", color=discord.Color.green())
        for item in entries[-10:]:
            embed.add_field(name=item["name"][:200], value=f"{item['date']}\n{item['details'][:500]}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sugerencia", description="Envía una sugerencia al canal configurado")
    async def sugerencia(self, interaction: discord.Interaction, texto: app_commands.Range[str, 5, 900]):
        target_id = self.guild_settings(interaction.guild_id).get("suggestion_channel")
        target = interaction.guild.get_channel(int(target_id)) if target_id else None
        if not isinstance(target, discord.TextChannel):
            return await interaction.response.send_message("El staff debe configurar el canal con /canal_sugerencias.", ephemeral=True)
        embed = discord.Embed(title="💡 Nueva sugerencia", description=discord.utils.escape_mentions(texto), color=discord.Color.gold())
        embed.set_footer(text=f"Autor ID: {interaction.user.id}")
        msg = await target.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        self.suggestions[str(msg.id)] = {"guild_id": interaction.guild_id, "author_id": interaction.user.id, "text": texto}
        save_json("suggestions.json", self.suggestions)
        await interaction.response.send_message("Sugerencia enviada. ¡Gracias por aportar!", ephemeral=True)

    @app_commands.command(name="canal_sugerencias", description="Configura el canal de sugerencias")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def canal_sugerencias(self, interaction: discord.Interaction, canal: discord.TextChannel):
        perms = canal.permissions_for(interaction.guild.me)
        if not (perms.view_channel and perms.send_messages and perms.embed_links and perms.add_reactions):
            return await interaction.response.send_message("Necesito ver el canal, enviar embeds y añadir reacciones.", ephemeral=True)
        self.guild_settings(interaction.guild_id)["suggestion_channel"] = canal.id
        save_json("utility_settings.json", self.settings)
        await interaction.response.send_message(f"Canal de sugerencias: {canal.mention}", ephemeral=True)

    @app_commands.command(name="sorteo", description="Elige al azar entre usuarios mencionados")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sorteo(self, interaction: discord.Interaction, participantes: app_commands.Range[str, 3, 1000]):
        ids = []
        for token in participantes.split():
            if token.startswith("<@") and token.endswith(">"):
                raw = token.strip("<@!>")
                if raw.isdigit():
                    ids.append(int(raw))
        ids = list(dict.fromkeys(ids))
        if len(ids) < 2:
            return await interaction.response.send_message("Menciona al menos dos participantes diferentes.", ephemeral=True)
        winner = random.choice(ids)
        await interaction.response.send_message(f"🎉 Sorteo terminado: gana <@{winner}>.", allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))

    @app_commands.command(name="serverinfo", description="Información del servidor actual")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Este comando solo funciona en un servidor.", ephemeral=True)
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        embed.add_field(name="Miembros", value=str(guild.member_count or "No disponible"))
        embed.add_field(name="Canales", value=str(len(guild.channels)))
        embed.add_field(name="Roles", value=str(len(guild.roles)))
        embed.add_field(name="Creado", value=discord.utils.format_dt(guild.created_at, "D"))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Información pública de un miembro")
    async def userinfo(self, interaction: discord.Interaction, usuario: discord.Member = None):
        usuario = usuario or interaction.user
        embed = discord.Embed(title=f"Perfil de {usuario.display_name}", color=discord.Color.blurple())
        embed.add_field(name="Cuenta", value=discord.utils.format_dt(usuario.created_at, "D"))
        if usuario.joined_at:
            embed.add_field(name="Entró al servidor", value=discord.utils.format_dt(usuario.joined_at, "D"))
        embed.add_field(name="ID", value=str(usuario.id))
        embed.set_thumbnail(url=usuario.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Comprueba la latencia de Papu")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong: {round(self.bot.latency * 1000)} ms")

    @app_commands.command(name="elegir", description="Papu elige una opcion por ti")
    async def elegir(self, interaction: discord.Interaction, opciones: app_commands.Range[str, 3, 500]):
        choices = [x.strip() for x in opciones.split("|") if x.strip()]
        if len(choices) < 2:
            return await interaction.response.send_message("Separa al menos dos opciones con |.", ephemeral=True)
        await interaction.response.send_message(f"🎲 Papu elige: **{discord.utils.escape_mentions(random.choice(choices))}**")

    @app_commands.command(name="config_papu", description="Muestra configuraciones comunitarias")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_papu(self, interaction: discord.Interaction):
        cfg = self.guild_settings(interaction.guild_id)
        channel = interaction.guild.get_channel(int(cfg["suggestion_channel"])) if cfg.get("suggestion_channel") else None
        await interaction.response.send_message(f"Canal de sugerencias: {channel.mention if channel else 'sin configurar'}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Utilidades(bot))
