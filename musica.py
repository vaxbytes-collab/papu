"""Reproductor de música por voz. Requiere FFmpeg, PyNaCl y yt-dlp."""
import asyncio
from collections import defaultdict, deque

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": True, "quiet": True,
               "no_warnings": True, "default_search": "ytsearch1"}
FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                  "options": "-vn"}


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = defaultdict(deque)
        self.now_playing = {}

    async def resolve(self, query):
        def extract():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:
                    info = next((x for x in info["entries"] if x), None)
                if not info:
                    raise ValueError("No encontré resultados.")
                return {"title": info.get("title", "Audio"), "url": info["url"],
                        "webpage": info.get("webpage_url", query), "duration": info.get("duration")}
        return await asyncio.to_thread(extract)

    async def play_next(self, guild_id):
        queue = self.queues[guild_id]
        guild = self.bot.get_guild(guild_id)
        if not guild or not guild.voice_client:
            return
        if not queue:
            self.now_playing.pop(guild_id, None)
            return
        track = queue.popleft()
        self.now_playing[guild_id] = track
        source = discord.FFmpegPCMAudio(track["url"], **FFMPEG_OPTIONS)
        def after(error):
            if error:
                print(f"[WARN] Error reproduciendo audio: {error}")
            self.bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.play_next(guild_id)))
        guild.voice_client.play(source, after=after)

    async def connect(self, interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("La música solo funciona en servidores.", ephemeral=True)
            return None
        voice = interaction.user.voice
        if not voice or not voice.channel:
            await interaction.response.send_message("Entra primero a un canal de voz, papu.", ephemeral=True)
            return None
        client = interaction.guild.voice_client
        if client is None:
            client = await voice.channel.connect()
        elif client.channel != voice.channel:
            await client.move_to(voice.channel)
        return client

    @app_commands.command(name="play", description="Busca y reproduce música en tu canal de voz")
    async def play(self, interaction: discord.Interaction, consulta: app_commands.Range[str, 1, 300]):
        if not interaction.guild:
            return await interaction.response.send_message("Solo disponible en servidores.", ephemeral=True)
        await interaction.response.defer(thinking=True)
        try:
            track = await self.resolve(consulta)
        except Exception:
            return await interaction.followup.send("No pude encontrar audio. Prueba otro título o enlace.", ephemeral=True)
        client = interaction.guild.voice_client
        if client is None:
            voice = getattr(interaction.user, "voice", None)
            if not voice or not voice.channel:
                return await interaction.followup.send("Entra a un canal de voz antes de usar /play.", ephemeral=True)
            client = await voice.channel.connect()
        elif isinstance(interaction.user, discord.Member) and interaction.user.voice and client.channel != interaction.user.voice.channel:
            await client.move_to(interaction.user.voice.channel)
        self.queues[interaction.guild_id].append(track)
        if not client.is_playing() and not client.is_paused() and self.now_playing.get(interaction.guild_id) is None:
            await self.play_next(interaction.guild_id)
        await interaction.followup.send(f"🎶 Añadida a la cola: **{discord.utils.escape_mentions(track['title'])}**\n{track['webpage']}")

    @app_commands.command(name="cola", description="Muestra la cola de música")
    async def cola(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        current = self.now_playing.get(guild_id)
        lines = [f"▶️ **Ahora:** {current['title']}" if current else "⏹️ No hay reproducción activa."]
        lines.extend(f"{i}. {item['title']}" for i, item in enumerate(list(self.queues[guild_id])[:10], 1))
        await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)

    @app_commands.command(name="skip", description="Salta la canción actual")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("No hay canción reproduciéndose.", ephemeral=True)
        vc.stop()
        await interaction.response.send_message("⏭️ Canción saltada.")

    @app_commands.command(name="pause", description="Pausa la música")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("No hay audio activo.", ephemeral=True)
        vc.pause()
        await interaction.response.send_message("⏸️ Pausado.")

    @app_commands.command(name="resume", description="Reanuda la música")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        if not vc or not vc.is_paused():
            return await interaction.response.send_message("La música no está pausada.", ephemeral=True)
        vc.resume()
        await interaction.response.send_message("▶️ Reanudado.")

    @app_commands.command(name="stop", description="Detiene la música y vacía la cola")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        if not vc:
            return await interaction.response.send_message("Papu no está en un canal de voz.", ephemeral=True)
        self.queues[interaction.guild_id].clear()
        self.now_playing.pop(interaction.guild_id, None)
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Música detenida y cola vaciada.")

    async def cog_unload(self):
        for guild in self.bot.guilds:
            if guild.voice_client:
                await guild.voice_client.disconnect(force=True)


async def setup(bot):
    await bot.add_cog(Musica(bot))
