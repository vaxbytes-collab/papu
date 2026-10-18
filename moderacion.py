import os
import json
import discord
from discord import app_commands
from discord.ext import commands

WARNS_FILE = "warns.json"

def load_warns():
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_warns(data):
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Moderacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulsa a un usuario del servidor")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón especificada papu"):
        await usuario.kick(reason=razon)
        await interaction.response.send_message(f"✅ **{usuario.mention}** fue expulsado del servidor. Razón: {razon} :v")

    @app_commands.command(name="ban", description="Banea permanentemente a un usuario")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón especificada papu"):
        await usuario.ban(reason=razon)
        await interaction.response.send_message(f"🔨 **{usuario.mention}** fue baneado del PapuCollective. Razón: {razon} :v")

    @app_commands.command(name="unban", description="Desbanea a un usuario usando su ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"🔓 **{user.name}** fue desbaneado papu :v")
        except Exception as e:
            await interaction.response.send_message(f"No se encontró la ID o el usuario no está baneado: {e}", ephemeral=True)

    @app_commands.command(name="timeout", description="Silencia temporalmente a un usuario")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, razon: str = "Portarse mal"):
        tiempo = discord.utils.utcnow() + discord.timedelta(minutes=minutos)
        await usuario.timeout(tiempo, reason=razon)
        await interaction.response.send_message(f"🤐 **{usuario.mention}** fue silenciado por {minutos} minutos. Razón: {razon} :v")

    @app_commands.command(name="untimeout", description="Remueve el silencio de un usuario")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, usuario: discord.Member):
        await usuario.timeout(None)
        await interaction.response.send_message(f"🔊 Se le quitó el silencio a **{usuario.mention}** papu :v")

    @app_commands.command(name="warn", description="Aplica una advertencia oficial a un usuario")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def warn(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "Incumplir reglas"):
        warns = load_warns()
        guild_id = str(interaction.guild_id)
        user_id = str(usuario.id)

        if guild_id not in warns:
            warns[guild_id] = {}
        if user_id not in warns[guild_id]:
            warns[guild_id][user_id] = []

        warns[guild_id][user_id].append(razon)
        save_warns(warns)

        total = len(warns[guild_id][user_id])
        await interaction.response.send_message(f"⚠️ **{usuario.mention}** recibió un warn (Total acumulado: {total}). Razón: {razon}")

    @app_commands.command(name="warns", description="Muestra las advertencias acumuladas de un usuario")
    async def warns_cmd(self, interaction: discord.Interaction, usuario: discord.Member):
        warns = load_warns()
        guild_id = str(interaction.guild_id)
        user_id = str(usuario.id)

        user_warns = warns.get(guild_id, {}).get(user_id, [])
        if not user_warns:
            await interaction.response.send_message(f"✨ **{usuario.mention}** está totalmente limpio, 0 warns :v")
        else:
            lista = "\n".join([f"{i+1}. {r}" for i, r in enumerate(user_warns)])
            await interaction.response.send_message(f"📋 **Historial de warns de {usuario.mention}:**\n{lista}")

    @app_commands.command(name="clearwarns", description="Borra todas las advertencias de un usuario")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, usuario: discord.Member):
        warns = load_warns()
        guild_id = str(interaction.guild_id)
        user_id = str(usuario.id)

        if guild_id in warns and user_id in warns[guild_id]:
            warns[guild_id][user_id] = []
            save_warns(warns)
            await interaction.response.send_message(f"🧹 Se borraron todos los warns de **{usuario.mention}** papu :v")
        else:
            await interaction.response.send_message("El usuario no tiene warns registrados.", ephemeral=True)

    @app_commands.command(name="purge", description="Borra mensajes masivamente")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, cantidad: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=cantidad)
        await interaction.followup.send(f"🧹 Se borraron {len(deleted)} mensajes correctamente :v")

    @app_commands.command(name="slowmode", description="Ajusta el modo lento del canal en segundos")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, segundos: int):
        await interaction.channel.edit(slowmode_delay=segundos)
        await interaction.response.send_message(f"⏱️ Modo lento ajustado a {segundos} segundos en este canal :v")

    @app_commands.command(name="lock", description="Bloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Canal bloqueado por el staff papu :v")

    @app_commands.command(name="unlock", description="Desbloquea el canal actual")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Canal desbloqueado papu :v")

    @app_commands.command(name="kickoutsiders", description="Expulsa miembros sin ningún rol")
    @app_commands.checks.has_permissions(administrator=True)
    async def kickoutsiders(self, interaction: discord.Interaction):
        await interaction.response.defer()
        expulsados = 0
        for member in interaction.guild.members:
            if len(member.roles) == 1:
                try:
                    await member.kick(reason="Limpieza de cuentas sin roles")
                    expulsados += 1
                except Exception:
                    pass
        await interaction.followup.send(f"🧹 Se expulsaron {expulsados} cuentas sospechosas sin roles :v")

    @app_commands.command(name="modcheck", description="Escanea un texto con IA para detectar racismo o toxicidad")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def modcheck(self, interaction: discord.Interaction, texto: str):
        await interaction.response.defer()
        try:
            prompt = (
                "Analiza el siguiente texto y dime si contiene racismo, discriminación, acoso o actitudes sospechosas. "
                "Responde con un veredicto claro y directo para el equipo de moderación. "
                f"Texto a analizar: {texto}"
            )
            response = self.bot.ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            await interaction.followup.send(f"🛡️ **Análisis de seguridad IA:**\n{response.text}")
        except Exception as e:
            await interaction.followup.send(f"Error al analizar texto con IA: {e}")

async def setup(bot):
    await bot.add_cog(Moderacion(bot))