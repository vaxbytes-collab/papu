import random
import discord
from discord import app_commands
from discord.ext import commands

class Entretenimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="momo", description="Muestra un momo aleatorio de la grasa sana")
    async def momo(self, interaction: discord.Interaction):
        momos = [
            "when haces tus momos en discord :v / but el staff te premia por ser buen miembro xdxd",
            "el futuro es hoy oíste viejo :v",
            "no lo sé rick parece falso, pasen contexto papus :v",
            "nadie: / absolutamente nadie: / yo entrando a la comunidad sana del PapuCollective :v",
            "when abres el server y ves pura gente basada :v",
            "un gran poder conlleva una gran responsabilidad :v"
        ]
        await interaction.response.send_message(random.choice(momos))

    @app_commands.command(name="chiste", description="Cuenta un chiste sano y apto para todos")
    async def chiste(self, interaction: discord.Interaction):
        chistes = [
            "— Papá, papá, ¿qué se siente tener un hijo tan guapo? — No lo sé hijo, pregúntale a tu abuelo :v",
            "— ¡Camarero! Hay una mosca en mi sopa. — No se preocupe, no bebe mucho xd",
            "— ¿Qué hace una abeja en el gimnasio? — ¡Zum-ba! :v",
            "— ¿Qué le dice un jaguar a otro jaguar? — Jagua yu :v"
        ]
        await interaction.response.send_message(random.choice(chistes))

    @app_commands.command(name="bola8_clasica", description="La bola 8 responderá a tu pregunta")
    async def ball8(self, interaction: discord.Interaction, pregunta: str):
        respuestas = [
            "Sí, totalmente papu :v",
            "Ni de chiste xd",
            "Es muy probable :v",
            "No tengo la menor idea :'v",
            "Vuelve a preguntar luego papu",
            "Las señales indican que sí :v"
        ]
        await interaction.response.send_message(f"🎱 **Pregunta:** {pregunta}\n**Respuesta:** {random.choice(respuestas)}")

    @app_commands.command(name="dado_clasico", description="Tira un dado de 6 caras")
    async def dado(self, interaction: discord.Interaction):
        res = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Te salió un: **{res}** papu :v")

    @app_commands.command(name="moneda_clasica", description="Lanza una moneda al aire (cara o cruz)")
    async def moneda(self, interaction: discord.Interaction):
        res = random.choice(["Cara 🪙", "Cruz 🪙"])
        await interaction.response.send_message(f"🪙 Cayó en: **{res}** papu :v")

    @app_commands.command(name="ppt_clasico", description="Juega piedra, papel o tijera contra el bot")
    @app_commands.choices(eleccion=[
        app_commands.Choice(name="piedra", value="piedra"),
        app_commands.Choice(name="papel", value="papel"),
        app_commands.Choice(name="tijera", value="tijera")
    ])
    async def ppt(self, interaction: discord.Interaction, eleccion: app_commands.Choice[str]):
        opciones = ["piedra", "papel", "tijera"]
        bot_choice = random.choice(opciones)
        user_choice = eleccion.value

        if user_choice == bot_choice:
            res = "Empate xd"
        elif (user_choice == "piedra" and bot_choice == "tijera") or \
             (user_choice == "papel" and bot_choice == "piedra") or \
             (user_choice == "tijera" and bot_choice == "papel"):
            res = "Ganaste papu 🎉 :v"
        else:
            res = "Te gané xd 🤖"

        await interaction.response.send_message(f"Tú: **{user_choice}** | Papu: **{bot_choice}** -> **{res}**")

    @app_commands.command(name="ruleta", description="Gira la ruleta de la suerte")
    async def ruleta(self, interaction: discord.Interaction):
        premios = [
            "Ganaste un saludo especial del staff 👑",
            "Te tocó pase VIP ficticio por un día :v",
            "Suerte legendaria, te salió un momo exclusivo",
            "Te tocó contar un chiste en el general xd"
        ]
        await interaction.response.send_message(f"🎰 Giraste la ruleta y: **{random.choice(premios)}**")

    @app_commands.command(name="avatar", description="Muestra el avatar en alta definición de un usuario")
    async def avatar(self, interaction: discord.Interaction, usuario: discord.Member):
        embed = discord.Embed(title=f"Avatar de {usuario.name} :v", color=discord.Color.blue())
        embed.set_image(url=usuario.avatar.url if usuario.avatar else usuario.default_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo_clasico", description="Muestra la información oficial del servidor")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Información de {guild.name} :v", color=discord.Color.green())
        embed.add_field(name="Dueño", value=guild.owner.mention if guild.owner else "Desconocido", inline=True)
        embed.add_field(name="Miembros", value=f"{guild.member_count} papus", inline=True)
        embed.add_field(name="Creación", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dilema", description="Te plantea un dilema divertido y sano")
    async def dilema(self, interaction: discord.Interaction):
        dilemas = [
            ("Tener internet rapidisimo, pero solo en una silla", "Tener internet normalito en cualquier parte"),
            ("Poder pausar el tiempo durante 10 segundos", "Poder rebobinar los ultimos 10 segundos una vez al dia"),
            ("Jugar Minecraft con todos tus amigos", "Jugar tu juego favorito con todo desbloqueado"),
            ("Tener una playlist perfecta para cada momento", "No volver a tener una cancion pegada en la cabeza"),
            ("Que todos tus memes den risa", "Que todos tus chistes malos se vuelvan buenos"),
            ("Vivir una semana en 2016", "Ver como sera internet en 2036"),
            ("Tener una habitacion secreta gamer", "Tener un cine privado en casa"),
            ("Poder hablar con los michis", "Entender cualquier idioma humano"),
            ("Que tu juego favorito nunca tenga bugs", "Que todos sus DLC sean gratis"),
            ("Tener un boton para encontrar cualquier objeto perdido", "Tener un boton para recordar cualquier contrasena sin verla"),
        ]
        a, b = random.choice(dilemas)
        embed = discord.Embed(
            title="🤔 dilema papu",
            description=f"**A)** {a}\n\n**B)** {b}\n\n*elige sabiamente, papu :v*",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="frase_michi", description="Pide una frase sabia de un michi")
    async def frase_michi(self, interaction: discord.Interaction):
        frases = [
            "si cabe la cabeza, cabe el michi. la caja es un estado mental.",
            "duerme hoy lo que puedas; mañana hay que tirar cosas de la mesa.",
            "no persigas la productividad: persigue el rayo del sol en el suelo.",
            "la paz interior comienza cuando aceptas que el teclado tambien es cama.",
            "un michi no llega tarde: el tiempo humano es una sugerencia.",
            "cuando la vida te cierre una puerta, busca una caja.",
            "respira, toma agua y recuerda que no tienes que resolverlo todo hoy.",
            "la curiosidad llevo al michi al laboratorio; la siesta lo saco de alli.",
            "el verdadero lujo es una manta calentita y cero notificaciones.",
            "no todos los dias son legendarios. hasta los michis tienen dias de mirar la pared.",
        ]
        embed = discord.Embed(
            title="🐈 palabra del michi",
            description=random.choice(frases),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot):
    await bot.add_cog(Entretenimiento(bot))