"""Protecciones opt-in contra spam, invitaciones no deseadas y picos de entradas."""
import json
import re
import time
import uuid
from collections import defaultdict, deque
from datetime import timedelta
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext import commands

from papu_store import load_json, save_json
from moderation_cases import make_case_content, next_case_id

INVITE_RE = re.compile(
    r"(?i)(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/[a-z0-9-]+"
)



URL_RE = re.compile(r"(?i)(?:https?://|www\.)?[^\s<>]+")
SUSPICIOUS_DOMAINS = {
    "grabify.link",
    "iplogger.org",
    "iplogger.com",
    "iplogger.ru",
    "iplogger.info",
    "iplogger.net",
    "2no.co",
    "yip.su",
    "discordnitro.com",
    "discord-gift.com",
    "dlscordapp.com",
    "steamcomunnity.com",
}


def contains_suspicious_link(content: str) -> bool:
    """Detecta dominios conocidos de rastreo/phishing sin bloquear cualquier URL."""
    for match in URL_RE.finditer(content or ""):
        candidate = match.group(0).rstrip(".,!?;:)]}>")
        if not candidate:
            continue
        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        host = (parsed.hostname or "").lower().rstrip(".")
        if host.startswith("www."):
            host = host[4:]
        if any(host == domain or host.endswith("." + domain) for domain in SUSPICIOUS_DOMAINS):
            return True
    return False


def contains_blocked_word(content: str, words) -> bool:
    """Coincidencia por palabra/frase completa para evitar bloquear subcadenas accidentales."""
    text = (content or "").casefold()
    for word in words or []:
        term = str(word).strip().casefold()
        if term and re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
            return True
    return False


def is_caps_spam(content: str, percent: int = 80, minimum: int = 12) -> bool:
    """Detecta texto con exceso de mayusculas solo si tiene suficientes letras."""
    letters = [char for char in (content or "") if char.isalpha()]
    if len(letters) < minimum:
        return False
    uppercase = sum(char.isupper() for char in letters)
    return uppercase / len(letters) * 100 >= percent


def mention_count(message: discord.Message) -> int:
    """Cuenta usuarios, roles y @everyone/@here como menciones."""
    return len(message.mentions) + len(message.role_mentions) + (1 if message.mention_everyone else 0)

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
    guardia = app_commands.Group(
        name="guardia",
        description="Herramientas avanzadas de seguridad y moderacion para el staff",
    )
    """Funciones automáticas opt-in. No expulsa ni banea por una detección automática."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = load_json("security_settings.json", {})
        self.log_channels = load_json("log_channels.json", {})
        self.message_times = defaultdict(deque)
        self.join_times = defaultdict(deque)
        self.last_spam_action = {}
        self.last_raid_alert = {}
        self.recent_texts = defaultdict(deque)
        self.last_report_at = {}
        self.staff_notes = load_json('staff_notes.json', {})
        self.incidents = load_json('security_incidents.json', {})

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
        permissions = interaction.guild.me.guild_permissions
        if activar and not permissions.manage_messages:
            return await interaction.response.send_message(
                "necesito el permiso gestionar mensajes para borrar el spam. no cambie la configuracion.",
                ephemeral=True,
            )
        if activar and timeout_segundos and not permissions.moderate_members:
            return await interaction.response.send_message(
                "necesito el permiso moderar miembros para aplicar timeout. usa timeout_segundos=0 o concedeme ese permiso.",
                ephemeral=True,
            )
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
                f"{umbral} miembros en {ventana} s. esta proteccion avisa en el canal de logs; "
                "configura /setlogchannel para recibir la alerta. no banea ni expulsa automaticamente."
            )
        else:
            description = "anti-raid **desactivado**."
        await interaction.response.send_message(description, ephemeral=True)
        await self.security_log(interaction.guild, f"🚨 Configuracion anti-raid cambiada por {interaction.user}: {description}")

    @app_commands.command(name="antienlaces", description="Bloquea invitaciones y dominios conocidos de phishing/rastreo")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antienlaces(self, interaction: discord.Interaction, activar: bool):
        permissions = interaction.guild.me.guild_permissions
        if activar and not permissions.manage_messages:
            return await interaction.response.send_message(
                "necesito el permiso gestionar mensajes para retirar enlaces no permitidos. no cambie la configuracion.",
                ephemeral=True,
            )
        cfg = self.guild_config(interaction.guild_id)
        cfg["anti_invites"] = {"enabled": activar}
        self.save_settings()
        status = "activado: eliminare invitaciones y enlaces a dominios conocidos de phishing/rastreo de miembros sin permiso de moderacion." if activar else "desactivado."
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
            name="Invitaciones / enlaces sospechosos",
            value="bloqueo activado" if invites.get("enabled") else "bloqueo desactivado",
            inline=False,
        )
        mentions = cfg.get("anti_mentions", {})
        embed.add_field(
            name="Anti-menciones",
            value=f"{'activado' if mentions.get('enabled') else 'desactivado'} · limite {mentions.get('limit', 4)}",
            inline=True,
        )
        repeat = cfg.get("anti_repeat", {})
        embed.add_field(
            name="Anti-repeticion",
            value=f"{'activado' if repeat.get('enabled') else 'desactivado'} · {repeat.get('repeats', 3)} en {repeat.get('window', 12)} s",
            inline=True,
        )
        caps = cfg.get("caps_filter", {})
        embed.add_field(
            name="Filtro caps",
            value=f"{'activado' if caps.get('enabled') else 'desactivado'} · {caps.get('percent', 85)}%",
            inline=True,
        )
        embed.add_field(
            name="Filtro personalizado",
            value=f"{len(cfg.get('blocked_words', []))} palabra(s)/frase(s) configurada(s)",
            inline=True,
        )
        embed.add_field(
            name="Reportes",
            value="canal configurado" if cfg.get("report_channel") else "sin configurar",
            inline=True,
        )
        embed.set_footer(text="Configura un canal de logs con /setlogchannel para recibir alertas.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="antimenciones", description="Limita menciones en mensajes para frenar ataques")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antimenciones(self, interaction: discord.Interaction, activar: bool, maximo: app_commands.Range[int, 2, 10] = 4):
        if activar and not interaction.guild.me.guild_permissions.manage_messages:
            return await interaction.response.send_message("necesito gestionar mensajes para borrar menciones excesivas.", ephemeral=True)
        self.guild_config(interaction.guild_id)["anti_mentions"] = {"enabled": activar, "limit": maximo}
        self.save_settings()
        status = f"activado: maximo {maximo} menciones por mensaje." if activar else "desactivado."
        await interaction.response.send_message(f"anti-menciones {status}", ephemeral=True)
        await self.security_log(interaction.guild, f"🛡️ Anti-menciones cambiado por {interaction.user}: {status}")

    @app_commands.command(name="antirepeticion", description="Detecta mensajes repetidos de forma automatica")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def antirepeticion(self, interaction: discord.Interaction, activar: bool, repeticiones: app_commands.Range[int, 2, 6] = 3, ventana: app_commands.Range[int, 3, 60] = 12):
        if activar and not interaction.guild.me.guild_permissions.manage_messages:
            return await interaction.response.send_message("necesito gestionar mensajes para retirar repeticiones.", ephemeral=True)
        self.guild_config(interaction.guild_id)["anti_repeat"] = {"enabled": activar, "repeats": repeticiones, "window": ventana}
        self.save_settings()
        status = f"activado: {repeticiones} mensajes iguales en {ventana} s." if activar else "desactivado."
        await interaction.response.send_message(f"anti-repeticion {status}", ephemeral=True)
        await self.security_log(interaction.guild, f"🔁 Anti-repeticion cambiado por {interaction.user}: {status}")

    @app_commands.command(name="filtro_caps", description="Retira mensajes excesivamente escritos en mayusculas")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def filtro_caps(self, interaction: discord.Interaction, activar: bool, porcentaje: app_commands.Range[int, 60, 100] = 85, minimo_letras: app_commands.Range[int, 8, 40] = 12):
        if activar and not interaction.guild.me.guild_permissions.manage_messages:
            return await interaction.response.send_message("necesito gestionar mensajes para aplicar el filtro de mayusculas.", ephemeral=True)
        self.guild_config(interaction.guild_id)["caps_filter"] = {"enabled": activar, "percent": porcentaje, "minimum": minimo_letras}
        self.save_settings()
        status = f"activado: {porcentaje}% de mayusculas, minimo {minimo_letras} letras." if activar else "desactivado."
        await interaction.response.send_message(f"filtro caps {status}", ephemeral=True)
        await self.security_log(interaction.guild, f"🔠 Filtro caps cambiado por {interaction.user}: {status}")

    @app_commands.command(name="palabra_bloquear", description="Añade una palabra o frase al filtro del servidor")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def palabra_bloquear(self, interaction: discord.Interaction, palabra: app_commands.Range[str, 2, 40]):
        cfg = self.guild_config(interaction.guild_id)
        words = cfg.setdefault("blocked_words", [])
        word = palabra.strip().casefold()
        if len(words) >= 50 and word not in words:
            return await interaction.response.send_message("el filtro admite hasta 50 palabras o frases.", ephemeral=True)
        if word in words:
            return await interaction.response.send_message("esa palabra ya esta en el filtro.", ephemeral=True)
        words.append(word)
        self.save_settings()
        await interaction.response.send_message(f"añadida al filtro: {discord.utils.escape_markdown(word)}", ephemeral=True)
        await self.security_log(interaction.guild, f"🧰 {interaction.user} añadió una palabra/frase al filtro personalizado.")

    @app_commands.command(name="palabra_permitir", description="Retira una palabra o frase del filtro del servidor")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def palabra_permitir(self, interaction: discord.Interaction, palabra: app_commands.Range[str, 2, 40]):
        cfg = self.guild_config(interaction.guild_id)
        words = cfg.setdefault("blocked_words", [])
        word = palabra.strip().casefold()
        if word not in words:
            return await interaction.response.send_message("esa palabra no estaba en el filtro.", ephemeral=True)
        words.remove(word)
        self.save_settings()
        await interaction.response.send_message(f"retirada del filtro: {discord.utils.escape_markdown(word)}", ephemeral=True)
        await self.security_log(interaction.guild, f"🧰 {interaction.user} retiró una palabra/frase del filtro personalizado.")

    @app_commands.command(name="palabras_bloqueadas", description="Lista las palabras configuradas en el filtro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def palabras_bloqueadas(self, interaction: discord.Interaction):
        words = self.guild_config(interaction.guild_id).get("blocked_words", [])
        if not words:
            return await interaction.response.send_message("el filtro personalizado esta vacio.", ephemeral=True)
        description = "\n".join(f"• {discord.utils.escape_markdown(word)}" for word in words)
        await interaction.response.send_message(f"palabras/frases filtradas:\n{description[:1700]}", ephemeral=True)

    @app_commands.command(name="canal_reportes", description="Configura donde enviar reportes privados al staff")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def canal_reportes(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        cfg = self.guild_config(interaction.guild_id)
        if canal is None:
            cfg.pop("report_channel", None)
            self.save_settings()
            return await interaction.response.send_message("canal de reportes desactivado.", ephemeral=True)
        perms = canal.permissions_for(interaction.guild.me)
        if not (perms.view_channel and perms.send_messages and perms.embed_links):
            return await interaction.response.send_message("necesito ver el canal, enviar mensajes e insertar embeds.", ephemeral=True)
        cfg["report_channel"] = canal.id
        self.save_settings()
        await interaction.response.send_message(f"los reportes se enviaran a {canal.mention}. procura que solo el staff pueda verlo.", ephemeral=True)

    @app_commands.command(name="reportar", description="Envía un reporte privado al canal de moderacion")
    @app_commands.guild_only()
    async def reportar(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: app_commands.Range[str, 10, 500],
        texto_mensaje: str = None,
        enlace_mensaje: str = None,
    ):
        key = (interaction.guild_id, interaction.user.id)
        now = time.monotonic()
        if now - self.last_report_at.get(key, 0) < 30:
            return await interaction.response.send_message("espera un poco antes de enviar otro reporte.", ephemeral=True)
        cfg = self.guild_config(interaction.guild_id)
        channel_id = cfg.get("report_channel")
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
        if channel is None:
            return await interaction.response.send_message("el staff aun no configuró el canal con /canal_reportes.", ephemeral=True)

        referenced_channel = interaction.channel
        if enlace_mensaje:
            match = re.fullmatch(
                r"https://(?:(?:ptb|canary)\.)?discord\.com/channels/(\d+)/(\d+)/(\d+)",
                enlace_mensaje.strip(),
            )
            if not match or int(match.group(1)) != interaction.guild_id:
                return await interaction.response.send_message(
                    "el enlace debe ser un enlace de mensaje de este mismo servidor (discord.com/channels/...).",
                    ephemeral=True,
                )
            linked_channel_id = int(match.group(2))
            referenced_channel = interaction.guild.get_channel_or_thread(linked_channel_id)
            if referenced_channel is None:
                referenced_channel = interaction.guild.get_channel(linked_channel_id)

        case_id = next_case_id(interaction.guild_id)
        case_content = make_case_content(
            case_id=case_id,
            title="📨 reporte recibido",
            username=str(usuario),
            user_id=usuario.id,
            channel_name=getattr(referenced_channel, "name", "canal del enlace no disponible"),
            channel_id=getattr(referenced_channel, "id", None),
            category="reporte del usuario",
            severity="sin evaluar",
            confidence="sin evaluar",
            reason=motivo.strip(),
            message_text=(texto_mensaje.strip() if texto_mensaje and texto_mensaje.strip() else "sin texto aportado; revisar el contexto"),
            message_url=enlace_mensaje.strip() if enlace_mensaje else None,
            reporter=f"{interaction.user} ({interaction.user.id})",
            status="REPORTE RECIBIDO: pendiente de revision humana; no se aplico ninguna sancion desde el reporte.",
        )
        try:
            await channel.send(content=case_content, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            return await interaction.response.send_message("no pude enviar el reporte; avisa al staff por otro medio.", ephemeral=True)
        self.last_report_at[key] = now
        await interaction.response.send_message(
            f"reporte #{case_id} enviado de forma privada al canal de moderacion. el staff revisara el contexto.",
            ephemeral=True,
        )

    @guardia.command(name="auditoria_permisos", description="Revisa permisos delicados de everyone y del bot")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def auditoria_permisos(self, interaction: discord.Interaction):
        guild = interaction.guild
        everyone = guild.default_role.permissions
        dangerous = [
            ("Administrador", everyone.administrator),
            ("Gestionar servidor", everyone.manage_guild),
            ("Gestionar canales", everyone.manage_channels),
            ("Gestionar roles", everyone.manage_roles),
            ("Expulsar miembros", everyone.kick_members),
            ("Banear miembros", everyone.ban_members),
            ("Gestionar webhooks", everyone.manage_webhooks),
            ("Mencionar everyone", everyone.mention_everyone),
        ]
        enabled = [label for label, active in dangerous if active]
        bot_member = guild.me
        missing = []
        if bot_member:
            perms = bot_member.guild_permissions
            for attr, label in (
                ("view_channel", "Ver canales"),
                ("send_messages", "Enviar mensajes"),
                ("manage_messages", "Gestionar mensajes"),
                ("moderate_members", "Aplicar timeout"),
                ("manage_channels", "Gestionar canales"),
            ):
                if not getattr(perms, attr):
                    missing.append(label)
        embed = discord.Embed(title="🔎 Auditoria de permisos", color=discord.Color.orange() if enabled else discord.Color.green())
        embed.add_field(name="Permisos delicados de everyone", value="\n".join(f"⚠️ {item}" for item in enabled) if enabled else "No encontre permisos delicados activados para everyone.", inline=False)
        embed.add_field(name="Permisos que le faltan a Papu", value="\n".join(f"• {item}" for item in missing) if missing else "No encontre carencias generales en la lista revisada.", inline=False)
        embed.set_footer(text="Auditoria orientativa; no cambia permisos automaticamente.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @guardia.command(name="enlace_comprobar", description="Comprueba si un enlace coincide con patrones bloqueados")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def enlace_comprobar(self, interaction: discord.Interaction, enlace: app_commands.Range[str, 5, 300]):
        invitation = contains_discord_invite(enlace)
        suspicious = contains_suspicious_link(enlace)
        if invitation:
            status = "coincide con un patron de invitacion de Discord."
        elif suspicious:
            status = "coincide con un dominio conocido de rastreo/phishing."
        else:
            status = "no coincide con la lista local de bloqueo. Esto no garantiza que sea seguro."
        await interaction.response.send_message(f"resultado: {status}", ephemeral=True)

    @guardia.command(name="palabra_previsualizar", description="Prueba una frase contra el filtro personalizado")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def palabra_previsualizar(self, interaction: discord.Interaction, texto: app_commands.Range[str, 1, 300]):
        words = self.guild_config(interaction.guild_id).get("blocked_words", [])
        matches = contains_blocked_word(texto, words)
        result = "coincidiria con una regla configurada." if matches else "no coincide con las reglas de palabras configuradas."
        await interaction.response.send_message(f"el texto {result} no borre ni guarde el texto de prueba.", ephemeral=True)

    @guardia.command(name="log_prueba", description="Comprueba que el canal de logs recibe mensajes")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def log_prueba(self, interaction: discord.Interaction):
        log_channels = load_json("log_channels.json", {})
        raw_id = log_channels.get(str(interaction.guild_id))
        channel = interaction.guild.get_channel(int(raw_id)) if raw_id else None
        if channel is None:
            return await interaction.response.send_message("no hay canal de logs configurado; usa /setlogchannel primero.", ephemeral=True)
        await self.security_log(interaction.guild, f"prueba de logs solicitada por {interaction.user} ({interaction.user.id}).")
        await interaction.response.send_message(f"envie una prueba a {channel.mention}.", ephemeral=True)

    @guardia.command(name="reporte_prueba", description="Comprueba el canal de reportes sin crear una denuncia")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reporte_prueba(self, interaction: discord.Interaction):
        channel_id = self.guild_config(interaction.guild_id).get("report_channel")
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
        if channel is None:
            return await interaction.response.send_message("no hay canal de reportes configurado; usa /canal_reportes.", ephemeral=True)
        try:
            await channel.send(
                f"prueba del sistema de reportes solicitada por {interaction.user} ({interaction.user.id}).",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            return await interaction.response.send_message("no pude escribir en el canal de reportes; revisa sus permisos.", ephemeral=True)
        await interaction.response.send_message(f"prueba enviada a {channel.mention}.", ephemeral=True)

    @guardia.command(name="nota_agregar", description="Guarda una nota de moderacion interna sobre un miembro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def nota_agregar(self, interaction: discord.Interaction, usuario: discord.Member, nota: app_commands.Range[str, 5, 300]):
        guild_key, user_key = str(interaction.guild_id), str(usuario.id)
        guild_notes = self.staff_notes.setdefault(guild_key, {})
        notes = guild_notes.setdefault(user_key, [])
        note_id = uuid.uuid4().hex[:8]
        notes.append({
            "id": note_id,
            "text": discord.utils.escape_mentions(nota.strip()),
            "author_id": interaction.user.id,
            "created_at": int(time.time()),
        })
        guild_notes[user_key] = notes[-50:]
        save_json("staff_notes.json", self.staff_notes)
        await interaction.response.send_message(f"nota interna guardada con ID {note_id}. usala solo para informacion relevante de moderacion.", ephemeral=True)
        await self.security_log(interaction.guild, f"nota interna añadida por {interaction.user} para el miembro {usuario.id}.")

    @guardia.command(name="notas_usuario", description="Consulta notas internas de moderacion de un miembro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notas_usuario(self, interaction: discord.Interaction, usuario: discord.Member):
        notes = self.staff_notes.get(str(interaction.guild_id), {}).get(str(usuario.id), [])
        if not notes:
            return await interaction.response.send_message("ese miembro no tiene notas internas guardadas.", ephemeral=True)
        lines = []
        for note in notes[-10:]:
            stamp = int(note.get("created_at", 0))
            lines.append(f"ID {note.get('id', '?')} - <t:{stamp}:d> - staff {note.get('author_id', '?')}\n{note.get('text', '')}")
        embed = discord.Embed(
            title=f"Notas internas: {discord.utils.escape_mentions(usuario.display_name)}",
            description="\n\n".join(lines)[:3900],
            color=discord.Color.orange(),
        )
        embed.set_footer(text="Solo para revision del staff; no guardes datos sensibles innecesarios.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @guardia.command(name="nota_borrar", description="Elimina una nota interna usando su ID")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def nota_borrar(self, interaction: discord.Interaction, usuario: discord.Member, nota_id: app_commands.Range[str, 8, 8]):
        guild_notes = self.staff_notes.get(str(interaction.guild_id), {})
        notes = guild_notes.get(str(usuario.id), [])
        kept = [note for note in notes if note.get("id") != nota_id]
        if len(kept) == len(notes):
            return await interaction.response.send_message("no encontre una nota con ese ID para ese miembro.", ephemeral=True)
        if kept:
            guild_notes[str(usuario.id)] = kept
        else:
            guild_notes.pop(str(usuario.id), None)
        save_json("staff_notes.json", self.staff_notes)
        await interaction.response.send_message(f"nota {nota_id} eliminada.", ephemeral=True)
        await self.security_log(interaction.guild, f"nota interna {nota_id} eliminada por {interaction.user}.")

    @guardia.command(name="incidente_crear", description="Registra un incidente para seguimiento del staff")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidente_crear(self, interaction: discord.Interaction, titulo: app_commands.Range[str, 3, 80], detalle: app_commands.Range[str, 10, 500]):
        guild_key = str(interaction.guild_id)
        incidents = self.incidents.setdefault(guild_key, [])
        incident_id = uuid.uuid4().hex[:8]
        incidents.append({
            "id": incident_id,
            "title": discord.utils.escape_mentions(titulo.strip()),
            "details": discord.utils.escape_mentions(detalle.strip()),
            "status": "abierto",
            "created_by": interaction.user.id,
            "created_at": int(time.time()),
        })
        self.incidents[guild_key] = incidents[-100:]
        save_json("security_incidents.json", self.incidents)
        await interaction.response.send_message(f"incidente registrado con ID {incident_id}; usa /guardia incidentes para consultarlo.", ephemeral=True)
        await self.security_log(interaction.guild, f"incidente {incident_id} registrado por {interaction.user}.")

    @guardia.command(name="incidentes", description="Lista los incidentes recientes del servidor")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentes(self, interaction: discord.Interaction):
        incidents = self.incidents.get(str(interaction.guild_id), [])
        if not incidents:
            return await interaction.response.send_message("no hay incidentes registrados.", ephemeral=True)
        lines = [
            f"{item.get('id', '?')} - {item.get('status', 'abierto')} - {item.get('title', 'sin titulo')}"
            for item in reversed(incidents[-12:])
        ]
        embed = discord.Embed(title="Incidentes recientes", description="\n".join(lines)[:3900], color=discord.Color.orange())
        embed.set_footer(text="Registros internos; registrar un incidente no verifica las alegaciones.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @guardia.command(name="incidente_cerrar", description="Marca un incidente como resuelto")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidente_cerrar(self, interaction: discord.Interaction, incidente_id: app_commands.Range[str, 8, 8]):
        incidents = self.incidents.get(str(interaction.guild_id), [])
        incident = next((item for item in incidents if item.get("id") == incidente_id), None)
        if incident is None:
            return await interaction.response.send_message("no encontre ese incidente.", ephemeral=True)
        if incident.get("status") == "cerrado":
            return await interaction.response.send_message("ese incidente ya estaba cerrado.", ephemeral=True)
        incident["status"] = "cerrado"
        incident["closed_by"] = interaction.user.id
        incident["closed_at"] = int(time.time())
        save_json("security_incidents.json", self.incidents)
        await interaction.response.send_message(f"incidente {incidente_id} marcado como cerrado.", ephemeral=True)
        await self.security_log(interaction.guild, f"incidente {incidente_id} cerrado por {interaction.user}.")

    @guardia.command(name="incidente_reabrir", description="Reabre un incidente que estaba cerrado")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidente_reabrir(self, interaction: discord.Interaction, incidente_id: app_commands.Range[str, 8, 8]):
        incidents = self.incidents.get(str(interaction.guild_id), [])
        incident = next((item for item in incidents if item.get("id") == incidente_id), None)
        if incident is None:
            return await interaction.response.send_message("no encontre ese incidente.", ephemeral=True)
        if incident.get("status") != "cerrado":
            return await interaction.response.send_message("ese incidente no esta cerrado.", ephemeral=True)
        incident["status"] = "abierto"
        incident.pop("closed_by", None)
        incident.pop("closed_at", None)
        save_json("security_incidents.json", self.incidents)
        await interaction.response.send_message(f"incidente {incidente_id} reabierto.", ephemeral=True)

    @guardia.command(name="raid_estado", description="Muestra cuantas entradas recientes registra el detector anti-raid")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def raid_estado(self, interaction: discord.Interaction):
        cfg = self.guild_config(interaction.guild_id).get("anti_raid", {})
        window = max(3, min(int(cfg.get("window", 10)), 60))
        events = self.join_times[interaction.guild_id]
        count = count_recent_events(events, time.monotonic(), window)
        threshold = max(3, min(int(cfg.get("threshold", 8)), 50))
        await interaction.response.send_message(
            f"anti-raid {'activado' if cfg.get('enabled') else 'desactivado'}. registro local: {count} entrada(s) en {window} s; umbral {threshold}.",
            ephemeral=True,
        )

    @guardia.command(name="contadores_reset", description="Limpia los contadores antispam de un miembro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def contadores_reset(self, interaction: discord.Interaction, usuario: discord.Member):
        guild_id, user_id = interaction.guild_id, usuario.id
        for key in list(self.message_times):
            if key[0] == guild_id and key[-1] == user_id:
                self.message_times.pop(key, None)
                self.last_spam_action.pop(key, None)
        for key in list(self.recent_texts):
            if key[0] == guild_id and key[-1] == user_id:
                self.recent_texts.pop(key, None)
        await interaction.response.send_message(f"contadores temporales limpiados para {discord.utils.escape_mentions(usuario.display_name)}.", ephemeral=True)

    @guardia.command(name="filtros_lista", description="Muestra todos los filtros automaticos configurados")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def filtros_lista(self, interaction: discord.Interaction):
        cfg = self.guild_config(interaction.guild_id)
        filters = [
            ("anti-spam", cfg.get("anti_spam", {})),
            ("anti-raid", cfg.get("anti_raid", {})),
            ("invitaciones/enlaces", cfg.get("anti_invites", {})),
            ("anti-menciones", cfg.get("anti_mentions", {})),
            ("anti-repeticion", cfg.get("anti_repeat", {})),
            ("caps", cfg.get("caps_filter", {})),
        ]
        lines = [f"{name}: {'ON' if settings.get('enabled') else 'OFF'}" for name, settings in filters]
        lines.append(f"palabras/frases bloqueadas: {len(cfg.get('blocked_words', []))}")
        lines.append(f"canales excluidos manualmente: {len(cfg.get('excluded_channels', {}))}")
        embed = discord.Embed(title="Resumen de filtros", description="\n".join(lines), color=discord.Color.blurple())
        embed.add_field(name="Reportes", value="configurado" if cfg.get("report_channel") else "sin configurar", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @guardia.command(name="filtros_reset", description="Desactiva filtros y borra reglas personalizadas con confirmacion")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def filtros_reset(self, interaction: discord.Interaction, confirmar: bool):
        if not confirmar:
            return await interaction.response.send_message("no hice cambios. vuelve a ejecutar con confirmar=true para desactivar los filtros y borrar palabras/canales excluidos.", ephemeral=True)
        cfg = self.guild_config(interaction.guild_id)
        for key in ("anti_spam", "anti_raid", "anti_invites", "anti_mentions", "anti_repeat", "caps_filter"):
            cfg[key] = {"enabled": False}
        cfg["blocked_words"] = []
        cfg["excluded_channels"] = {}
        self.save_settings()
        await interaction.response.send_message("filtros automaticos desactivados y reglas personalizadas borradas. el canal de reportes se conserva.", ephemeral=True)
        await self.security_log(interaction.guild, f"filtros reiniciados por {interaction.user}.")

    @guardia.command(name="excluir_canal", description="Excluye un canal de los filtros automaticos")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def excluir_canal(self, interaction: discord.Interaction, canal: discord.TextChannel, motivo: app_commands.Range[str, 3, 100]):
        cfg = self.guild_config(interaction.guild_id)
        excluded = cfg.setdefault("excluded_channels", {})
        if str(canal.id) not in excluded and len(excluded) >= 20:
            return await interaction.response.send_message("solo puedes excluir hasta 20 canales.", ephemeral=True)
        excluded[str(canal.id)] = discord.utils.escape_mentions(motivo.strip())
        self.save_settings()
        await interaction.response.send_message(f"{canal.mention} quedo excluido de filtros automaticos. tambien deja de recibir protecciones de esos filtros.", ephemeral=True)
        await self.security_log(interaction.guild, f"canal excluido de filtros por {interaction.user}: #{canal.name}.")

    @guardia.command(name="incluir_canal", description="Vuelve a aplicar filtros en un canal excluido")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def incluir_canal(self, interaction: discord.Interaction, canal: discord.TextChannel):
        cfg = self.guild_config(interaction.guild_id)
        excluded = cfg.setdefault("excluded_channels", {})
        if str(canal.id) not in excluded:
            return await interaction.response.send_message("ese canal no estaba excluido.", ephemeral=True)
        excluded.pop(str(canal.id), None)
        self.save_settings()
        await interaction.response.send_message(f"filtros automaticos reactivados para {canal.mention}.", ephemeral=True)
        await self.security_log(interaction.guild, f"filtros reactivados en #{canal.name} por {interaction.user}.")

    @guardia.command(name="mensaje_analizar", description="Analiza texto con filtros locales sin borrar ni guardar")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mensaje_analizar(self, interaction: discord.Interaction, texto: app_commands.Range[str, 1, 500]):
        cfg = self.guild_config(interaction.guild_id)
        flags = []
        if contains_discord_invite(texto):
            flags.append("invitacion de Discord")
        if contains_suspicious_link(texto):
            flags.append("dominio de rastreo/phishing conocido")
        if contains_blocked_word(texto, cfg.get("blocked_words", [])):
            flags.append("regla de palabra/frase personalizada")
        caps = cfg.get("caps_filter", {})
        if caps.get("enabled") and is_caps_spam(texto, int(caps.get("percent", 85)), int(caps.get("minimum", 12))):
            flags.append("exceso de mayusculas")
        result = "\n".join(f"• {item}" for item in flags) if flags else "no coincide con los filtros locales revisados."
        await interaction.response.send_message(f"analisis local (no es una garantia de seguridad):\n{result}\nno borre ni almacene el texto enviado.", ephemeral=True)

    @guardia.command(name="url_bloqueadas", description="Lista dominios de rastreo/phishing reconocidos por el filtro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def url_bloqueadas(self, interaction: discord.Interaction):
        description = "\n".join(f"• {domain}" for domain in sorted(SUSPICIOUS_DOMAINS))
        await interaction.response.send_message(f"lista local de dominios vigilados:\n{description}", ephemeral=True)

    @guardia.command(name="spam_estado_usuario", description="Consulta contadores temporales de spam de un miembro")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def spam_estado_usuario(self, interaction: discord.Interaction, usuario: discord.Member):
        rows = []
        now = time.monotonic()
        for key, events in list(self.message_times.items()):
            if key[0] != interaction.guild_id or key[-1] != usuario.id:
                continue
            count_recent_events(events, now, 60)
            if events:
                rows.append(f"canal {key[1]}: {len(events)} evento(s) en los ultimos 60 s")
        description = "\n".join(rows) or "no hay contadores temporales activos para ese miembro."
        await interaction.response.send_message(f"contadores locales para {discord.utils.escape_mentions(usuario.display_name)}:\n{description[:1500]}", ephemeral=True)

    @guardia.command(name="reportes_info", description="Consulta la configuracion del canal de reportes")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reportes_info(self, interaction: discord.Interaction):
        channel_id = self.guild_config(interaction.guild_id).get("report_channel")
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
        if channel is None:
            return await interaction.response.send_message("el canal de reportes no esta configurado o ya no existe.", ephemeral=True)
        await interaction.response.send_message(f"los reportes llegan a {channel.mention}. revisa que sea privado para miembros normales.", ephemeral=True)

    @guardia.command(name="activar_basico", description="Activa una configuracion moderada de anti-spam, menciones y repeticiones")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def activar_basico(self, interaction: discord.Interaction):
        if not interaction.guild.me.guild_permissions.manage_messages:
            return await interaction.response.send_message("necesito gestionar mensajes para activar este perfil.", ephemeral=True)
        cfg = self.guild_config(interaction.guild_id)
        cfg["anti_spam"] = {"enabled": True, "limit": 8, "window": 10, "timeout": 0}
        cfg["anti_mentions"] = {"enabled": True, "limit": 5}
        cfg["anti_repeat"] = {"enabled": True, "repeats": 4, "window": 15}
        self.save_settings()
        await interaction.response.send_message("perfil basico activado: 8 mensajes/10 s, maximo 5 menciones y 4 repeticiones/15 s. no activa caps ni filtro de enlaces.", ephemeral=True)
        await self.security_log(interaction.guild, f"perfil basico activado por {interaction.user}.")

    @guardia.command(name="desactivar_automaticos", description="Apaga filtros automaticos sin borrar sus configuraciones")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def desactivar_automaticos(self, interaction: discord.Interaction):
        cfg = self.guild_config(interaction.guild_id)
        for key in ("anti_spam", "anti_raid", "anti_invites", "anti_mentions", "anti_repeat", "caps_filter"):
            if isinstance(cfg.get(key), dict):
                cfg[key]["enabled"] = False
        self.save_settings()
        await interaction.response.send_message("filtros automaticos apagados; sus valores se conservaron. el filtro de palabras sigue activo hasta borrarlo o usar /guardia filtros_reset.", ephemeral=True)
        await self.security_log(interaction.guild, f"filtros automaticos desactivados por {interaction.user}.")

    @guardia.command(name="config_exportar", description="Exporta configuracion de seguridad en formato JSON")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_exportar(self, interaction: discord.Interaction):
        exported = json.dumps(self.guild_config(interaction.guild_id), ensure_ascii=False, indent=2)
        if len(exported) > 1700:
            return await interaction.response.send_message("la configuracion es demasiado grande para enviarla en una sola respuesta. revisa /guardia filtros_lista.", ephemeral=True)
        await interaction.response.send_message(f"copia de configuracion; guardala con cuidado:\n{exported}", ephemeral=True)

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
        excluded_channels = cfg.get("excluded_channels", {})
        if isinstance(excluded_channels, dict) and str(message.channel.id) in excluded_channels:
            return

        invite_cfg = cfg.get("anti_invites", {})
        if invite_cfg.get("enabled") and (contains_discord_invite(message.content) or contains_suspicious_link(message.content)):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                # No repitas el mensaje ni bloquees el resto de la moderacion si Discord lo rechaza.
                await self.security_log(message.guild, f"⚠️ Detecte una invitacion en #{message.channel.name}, pero no pude borrarla.")
                return
            await self.security_log(
                message.guild,
                f"🔗 Eliminado enlace no permitido de {member} ({member.id}) en #{message.channel.name}.",
            )
            return

        blocked_words = cfg.get("blocked_words", [])
        if blocked_words and contains_blocked_word(message.content, blocked_words):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            await self.security_log(message.guild, f"🧰 Mensaje filtrado por regla personalizada de {member} en #{message.channel.name}.")
            return

        mention_cfg = cfg.get("anti_mentions", {})
        mentions_limit = max(2, min(int(mention_cfg.get("limit", 4)), 10))
        if mention_cfg.get("enabled") and mention_count(message) > mentions_limit:
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            await self.security_log(message.guild, f"📣 Exceso de menciones de {member} en #{message.channel.name}; limite {mentions_limit}.")
            return

        caps_cfg = cfg.get("caps_filter", {})
        if caps_cfg.get("enabled") and is_caps_spam(
            message.content,
            percent=max(60, min(int(caps_cfg.get("percent", 85)), 100)),
            minimum=max(8, min(int(caps_cfg.get("minimum", 12)), 40)),
        ):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            await self.security_log(message.guild, f"🔠 Mensaje con exceso de mayusculas retirado de {member} en #{message.channel.name}.")
            return

        repeat_cfg = cfg.get("anti_repeat", {})
        if repeat_cfg.get("enabled") and message.content.strip():
            window_repeat = max(3, min(int(repeat_cfg.get("window", 12)), 60))
            repeat_limit = max(2, min(int(repeat_cfg.get("repeats", 3)), 6))
            repeat_key = (message.guild.id, message.channel.id, member.id)
            recent = self.recent_texts[repeat_key]
            now_repeat = time.monotonic()
            cutoff_repeat = now_repeat - window_repeat
            while recent and recent[0][0] < cutoff_repeat:
                recent.popleft()
            normalized = " ".join(message.content.casefold().split())[:500]
            recent.append((now_repeat, normalized))
            repeated = sum(1 for _, text in recent if text == normalized)
            if repeated >= repeat_limit:
                recent.clear()
                try:
                    await message.delete()
                except (discord.Forbidden, discord.HTTPException):
                    pass
                await self.security_log(message.guild, f"🔁 Mensaje repetido retirado de {member} en #{message.channel.name}; {repeat_limit} repeticiones en {window_repeat} s.")
                return

        spam_cfg = cfg.get("anti_spam", {})
        if not spam_cfg.get("enabled"):
            return

        window = max(3, min(int(spam_cfg.get("window", 8)), 30))
        limit = max(3, min(int(spam_cfg.get("limit", 6)), 20))
        timeout_seconds = max(0, min(int(spam_cfg.get("timeout", 60)), 600))
        now = time.monotonic()
        key = (message.guild.id, message.channel.id, member.id)
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
