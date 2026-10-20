import random
import discord
from discord import app_commands
from discord.ext import commands

class Entretenimiento(commands.Cog):
    arcade = app_commands.Group(
        name="arcade",
        description="Minijuegos sencillos de Papu",
    )
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

    @app_commands.command(name="avatar", description="Muestra el avatar en alta definición de un usuario")
    async def avatar(self, interaction: discord.Interaction, usuario: discord.Member):
        embed = discord.Embed(title=f"Avatar de {usuario.name} :v", color=discord.Color.blue())
        embed.set_image(url=usuario.avatar.url if usuario.avatar else usuario.default_avatar.url)
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



    @arcade.command(name="adivinanza", description="Te da una adivinanza con la respuesta oculta")
    async def adivinanza(self, interaction: discord.Interaction):
        items = [
            ("tengo teclas pero no abro puertas. ¿que soy?", "un teclado"),
            ("cuanto mas seco, mas mojo. ¿que soy?", "una toalla"),
            ("tengo ciudades sin casas, rios sin agua y bosques sin arboles. ¿que soy?", "un mapa"),
            ("sube y baja, pero siempre se queda en el mismo sitio. ¿que es?", "una escalera"),
            ("tiene agujas pero no cose. ¿que es?", "un reloj"),
            ("si me nombras, desaparezco. ¿que soy?", "el silencio"),
            ("tengo muchos dientes, pero no puedo morder. ¿que soy?", "un peine"),
            ("vuelo sin alas y lloro sin ojos. ¿que soy?", "una nube"),
        ]
        riddle, answer = random.choice(items)
        embed = discord.Embed(
            title="🧩 adivinanza papu",
            description=f"{riddle}\n\nrespuesta: ||{answer}||",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)

    @arcade.command(name="dado_personalizado", description="Tira un dado con el maximo que tu elijas")
    async def dado_personalizado(self, interaction: discord.Interaction, caras: app_commands.Range[int, 2, 1000] = 20):
        await interaction.response.send_message(f"🎲 dado de 1 a {caras}: **{random.randint(1, caras)}** :v")

    @arcade.command(name="dato_michi", description="Un dato curioso sobre gatos")
    async def dato_michi(self, interaction: discord.Interaction):
        facts = [
            "los gatos usan sus bigotes como sensores tactiles; no son solo decoracion.",
            "el ronroneo puede aparecer en distintos contextos, incluso cuando un gato esta estresado.",
            "la nariz de cada gato tiene un patron unico, parecido a una huella.",
            "los gatos suelen dormir muchas horas al dia porque alternan descanso con periodos cortos de actividad.",
            "la cola, las orejas, los ojos y la postura ayudan a interpretar el lenguaje corporal felino.",
            "los gatos tienen un sentido del oido sensible a sonidos agudos.",
            "el juego de caza simulado ayuda a los gatos a practicar conductas naturales.",
            "los gatos pueden aprender rutinas y anticipar eventos diarios.",
        ]
        await interaction.response.send_message(f"🐈 dato michi: {random.choice(facts)}")

    @arcade.command(name="reto_sano", description="Un reto opcional y sin riesgo para el servidor")
    async def reto_sano(self, interaction: discord.Interaction):
        challenges = [
            "comparte un juego que recomiendes sin decir su nombre; deja que lo adivinen.",
            "inventa un titulo de album con tres palabras al azar.",
            "describe tu comida favorita usando solo tres emojis.",
            "recomienda una cancion y explica su vibra en una frase.",
            "dibuja un michi en el chat usando caracteres.",
            "escribe una historia de terror de exactamente siete palabras, sin detalles graficos.",
            "di una cosa pequeña que te alegro el dia.",
            "inventa una nueva regla absurda para un videojuego ficticio.",
            "describe tu meme favorito sin enlazarlo; que el chat lo adivine.",
            "crea el nombre de una ciudad donde solo vivan gatos.",
        ]
        await interaction.response.send_message(f"🎯 reto opcional: {random.choice(challenges)}")

    @arcade.command(name="palabra_aleatoria", description="Te da una palabra al azar para escribir o dibujar")
    async def palabra_aleatoria(self, interaction: discord.Interaction):
        words = ["laberinto", "cometa", "paraguas", "reliquia", "pixel", "tormenta", "cafetera", "saturno", "fantasma", "brujula", "ferrocarril", "caramelo", "glaciar", "cassette", "misterio", "semilla", "nublado", "ascensor", "recreo", "paradoja"]
        await interaction.response.send_message(f"📝 palabra aleatoria: **{random.choice(words)}**")

    @arcade.command(name="duelo", description="Genera un duelo absurdo entre dos cosas")
    async def duelo_aleatorio(self, interaction: discord.Interaction):
        things = ["un michi con wifi", "una tostadora gamer", "un pato con corbata", "la calculadora del colegio", "un robot que solo dice miau", "una papa interdimensional", "un ventilador dramatico", "un dinosaurio con patines", "un modem legendario", "una silla que cruje"]
        a, b = random.sample(things, 2)
        winner = random.choice([a, b])
        await interaction.response.send_message(f"🥊 **{a} VS {b}**\nveredicto cientificamente inventado: gana **{winner}**.")

    @arcade.command(name="completa_frase", description="Completa una frase meme de forma aleatoria")
    async def completa_frase(self, interaction: discord.Interaction):
        beginnings = [
            ("yo diciendo que me voy a dormir temprano...", "...y el algoritmo recomendando otro video."),
            ("el profe: esto no entra en el examen...", "...yo guardando la hoja por si acaso."),
            ("mi PC despues de abrir 42 pestañas...", "...activando el modo avion emocional."),
            ("nadie:", "...mi gato tirando un objeto a las 4 de la mañana."),
            ("cuando todo funciona a la primera...", "...sospecho que estoy en una simulacion."),
            ("yo: hoy si me organizo...", "...mi calendario riendose en binario."),
        ]
        a, b = random.choice(beginnings)
        await interaction.response.send_message(f"🧩 {a}\n{b}")
