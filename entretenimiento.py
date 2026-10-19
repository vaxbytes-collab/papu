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



    @app_commands.command(name="adivinanza", description="Te da una adivinanza con la respuesta oculta")
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

    @app_commands.command(name="dado_personalizado", description="Tira un dado con el maximo que tu elijas")
    async def dado_personalizado(self, interaction: discord.Interaction, caras: app_commands.Range[int, 2, 1000] = 20):
        await interaction.response.send_message(f"🎲 dado de 1 a {caras}: **{random.randint(1, caras)}** :v")

    @app_commands.command(name="fortuna", description="Recibe una fortuna ficticia para divertirte")
    async def fortuna(self, interaction: discord.Interaction):
        cards = [
            "hoy encontraras algo que creias perdido. o era el cargador de alguien mas.",
            "una idea sencilla te salvara de una tarea enorme.",
            "el universo recomienda tomar agua y revisar dos veces antes de enviar.",
            "tu proximo gran logro podria empezar con cinco minutos de esfuerzo.",
            "una sorpresa agradable aparecera donde menos te lo esperes; probablemente en la nevera.",
            "la suerte favorece a quien guarda el archivo antes de cerrar el programa.",
            "un viejo meme volvera a estar de moda. el ciclo es inevitable.",
            "la fortuna te sonrie, pero primero actualiza el sistema.",
        ]
        await interaction.response.send_message(f"🔮 {random.choice(cards)}\n\n*fortuna inventada, solo por diversion :v*")

    @app_commands.command(name="nombre_banda", description="Genera un nombre aleatorio para una banda")
    async def nombre_banda(self, interaction: discord.Interaction):
        left = ["Los", "Club", "Radio", "Neon", "Turbo", "Michi", "Planeta", "Archivo"]
        right = ["Saturno", "del Caos", "Pixel", "Fantasma", "de Medianoche", "404", "Las Papas", "del Futuro"]
        genre = random.choice(["indie de garage", "rap intergalactico", "pop de otra dimension", "rock de videojuego", "synth de madrugada", "cumbia cuantica"])
        await interaction.response.send_message(f"🎸 nombre: **{random.choice(left)} {random.choice(right)}**\ngenero: {genre}")

    @app_commands.command(name="nombre_usuario", description="Genera un nombre de usuario ficticio")
    @app_commands.choices(estilo=[
        app_commands.Choice(name="gamer", value="gamer"),
        app_commands.Choice(name="retro", value="retro"),
        app_commands.Choice(name="michi", value="michi"),
        app_commands.Choice(name="caotico", value="caotico"),
    ])
    async def nombre_usuario(self, interaction: discord.Interaction, estilo: app_commands.Choice[str]):
        parts = {
            "gamer": (["Turbo", "Pixel", "Combo", "Respawn", "Critico", "Lag"], ["GG", "Provisional", "404", "XP", "Deluxe"]),
            "retro": (["VHS", "CRT", "Cassette", "Win98", "Disquete", "Arcade"], ["Azul", "2007", "Plus", "FM", "Offline"]),
            "michi": (["Michi", "Bigotes", "Choclo", "Miau", "Gatuno", "Paw"], ["Astral", "Cósmico", "Deluxe", "404", "Ninja"]),
            "caotico": (["Don", "Ultra", "Señor", "Patata", "Papu", "Mega"], ["Random", "Caotico", "Supremo", "Inesperado", "X"]),
        }
        a, b = parts[estilo.value]
        await interaction.response.send_message(f"🪪 tu nuevo nick podria ser: **{random.choice(a)}{random.choice(b)}**")

    @app_commands.command(name="pov", description="Genera un POV tipo meme con tu tema")
    async def pov(self, interaction: discord.Interaction, tema: app_commands.Range[str, 3, 100]):
        clean = discord.utils.escape_mentions(tema.strip())
        setups = [
            "pov: entras cinco minutos y de repente ya son las 3 de la mañana.",
            "pov: dices que esta es la ultima partida y tus amigos invitan otra.",
            "pov: abres la tarea y el archivo te mira de vuelta.",
            "pov: actualizas una cosa y ahora hay otros siete problemas.",
            "pov: el profe dice que es facil y abre 38 diapositivas.",
            "pov: tu wifi decide tomarse un descanso justo ahora.",
        ]
        await interaction.response.send_message(f"🎬 **{random.choice(setups)}**\ncontexto: {clean}")

    @app_commands.command(name="superpoder", description="Te asigna un superpoder aleatorio")
    async def superpoder(self, interaction: discord.Interaction):
        powers = [
            "encontrar el mando a distancia en menos de 10 segundos.",
            "pausar cualquier cancion sin tocar el telefono.",
            "saber quien se ha comido la ultima galleta.",
            "cargar tu movil al 1% con una mirada, una vez al dia.",
            "respawnear una patata frita cada vez que dices miau.",
            "entender perfectamente a los gatos, pero solo los martes.",
            "hacer que el transporte llegue justo cuando tu llegas a la parada.",
            "guardar cualquier archivo con solo pensarlo.",
            "detectar spoilers a 30 metros.",
            "convertir cualquier cola de espera en una sesion de karaoke silencioso.",
        ]
        await interaction.response.send_message(f"🦸 superpoder desbloqueado: **{random.choice(powers)}**")

    @app_commands.command(name="villano", description="Crea un villano ficticio y ridiculo")
    async def villano(self, interaction: discord.Interaction):
        names = ["Doctor Buffer", "El Conde del Lag", "La Patata Oscura", "Señor Actualizacion", "El Spoileador", "Capitan Caps Lock"]
        plans = [
            "quiere cambiar todos los sonidos de notificacion por una flauta desafinada.",
            "planea esconder el boton de guardar en todos los programas.",
            "quiere poner anuncios de 40 minutos antes de cada meme.",
            "intenta convertir todos los servidores en reuniones eternas.",
            "pretende renombrar todos los archivos como documento_final_final_ahora_si.",
            "quiere que cada juego tenga una pantalla de carga con otra pantalla de carga.",
        ]
        await interaction.response.send_message(f"🦹 **{random.choice(names)}**\nplan maestro: {random.choice(plans)}")

    @app_commands.command(name="dato_michi", description="Un dato curioso sobre gatos")
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

    @app_commands.command(name="reto_sano", description="Un reto opcional y sin riesgo para el servidor")
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

    @app_commands.command(name="mood_michi", description="Elige la energia gatuna de hoy")
    async def mood_michi(self, interaction: discord.Interaction):
        moods = [
            ("michi panqueque", "modo horizontal, bateria social al 2%."),
            ("michi zoomies", "energia caotica: correr en circulos es una opcion figurada."),
            ("michi filosofico", "mirando la pared como si supiera el secreto del universo."),
            ("michi gamer", "concentrado en una mision secundaria muy importante."),
            ("michi nube", "vibra tranquila y cero prisa."),
            ("michi gremlin", "pequeño caos, grandes intenciones de tirar un lapiz."),
            ("michi sabio", "hoy toca resolver una cosa a la vez."),
        ]
        title, description = random.choice(moods)
        await interaction.response.send_message(f"🐾 **{title}**: {description}")

    @app_commands.command(name="palabra_aleatoria", description="Te da una palabra al azar para escribir o dibujar")
    async def palabra_aleatoria(self, interaction: discord.Interaction):
        words = ["laberinto", "cometa", "paraguas", "reliquia", "pixel", "tormenta", "cafetera", "saturno", "fantasma", "brujula", "ferrocarril", "caramelo", "glaciar", "cassette", "misterio", "semilla", "nublado", "ascensor", "recreo", "paradoja"]
        await interaction.response.send_message(f"📝 palabra aleatoria: **{random.choice(words)}**")

    @app_commands.command(name="duelo_aleatorio", description="Genera un duelo absurdo entre dos cosas")
    async def duelo_aleatorio(self, interaction: discord.Interaction):
        things = ["un michi con wifi", "una tostadora gamer", "un pato con corbata", "la calculadora del colegio", "un robot que solo dice miau", "una papa interdimensional", "un ventilador dramatico", "un dinosaurio con patines", "un modem legendario", "una silla que cruje"]
        a, b = random.sample(things, 2)
        winner = random.choice([a, b])
        await interaction.response.send_message(f"🥊 **{a} VS {b}**\nveredicto cientificamente inventado: gana **{winner}**.")

    @app_commands.command(name="completa_frase", description="Completa una frase meme de forma aleatoria")
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

    @app_commands.command(name="verso_michi", description="Genera un mini verso original sobre michis")
    async def verso_michi(self, interaction: discord.Interaction):
        first = ["bajo la luna de carton", "sobre el router dormido", "en una caja sin razon", "junto al teclado encendido", "por el pasillo espacial"]
        second = ["un michi vigila el universo", "bigotes redacta un verso", "la siesta vence al final", "el caos se vuelve musical", "y el lunes queda suspendido"]
        await interaction.response.send_message(f"📜 {random.choice(first)},\n{random.choice(second)}.")

    @app_commands.command(name="npc", description="Te asigna una frase de NPC de videojuego")
    async def npc(self, interaction: discord.Interaction):
        lines = [
            "no he visto nada interesante desde el parche 1.02.",
            "si buscas al herrero, gira a la izquierda despues de la roca con forma de pan.",
            "mi inventario esta lleno de objetos que probablemente nunca usare.",
            "vuelve cuando tengas mas experiencia y menos pestañas abiertas.",
            "el camino del norte esta cerrado por mantenimiento de lore.",
            "he perdido una llave. no se de que abre, pero la necesito.",
            "el jefe final esta ocupado leyendo los terminos y condiciones.",
            "no soy parte de la historia principal, pero tengo una mision secundaria.",
        ]
        await interaction.response.send_message(f"🧙 NPC: «{random.choice(lines)}»")

    @app_commands.command(name="excusa_gamer", description="Genera una excusa gamer completamente absurda")
    async def excusa_gamer(self, interaction: discord.Interaction):
        excuses = [
            "perdi porque mi raton estaba procesando sus emociones.",
            "el servidor estaba en otra dimension; yo llegue tarde al multiverso.",
            "mi teclado cambio de idioma en medio del combo.",
            "el enemigo tenia ventaja de lore.",
            "estaba probando una estrategia que todavia no ha sido inventada.",
            "mi michi estaba supervisando la partida y no aprobo el gameplay.",
            "eso no fue lag, fue una pausa cinematografica involuntaria.",
            "mi silla activo el modo ranked inverso.",
        ]
        await interaction.response.send_message(f"🎮 excusa oficial: {random.choice(excuses)}")

    @app_commands.command(name="cancion_inventada", description="Genera un titulo y una vibra para una cancion ficticia")
    async def cancion_inventada(self, interaction: discord.Interaction):
        titles = ["Ascensor a Saturno", "Michi.exe", "Domingo en 240p", "La Ultima Patata", "Neon en Usera", "Modo Avion", "Buffer Emocional", "Archivo Sin Guardar", "Papas en el Espacio", "La Siesta Final"]
        vibes = ["rap espacial", "synth pop retro", "rock de videojuego", "lofi de madrugada", "electronica de arcade", "balada para un router", "cumbia intergalactica"]
        await interaction.response.send_message(f"🎵 **{random.choice(titles)}**\nvibra: {random.choice(vibes)}\n*tema inventado al vuelo; no es una cancion real conocida.*")

    @app_commands.command(name="lore_aleatorio", description="Crea una premisa de lore absurdo para el servidor")
    async def lore_aleatorio(self, interaction: discord.Interaction):
        premises = [
            "el canal de memes fue construido encima de una antigua civilizacion de patatas.",
            "cada vez que alguien escribe 'xd', un NPC de otro universo recibe una mision secundaria.",
            "el primer modem del servidor sigue vivo y controla las mareas.",
            "los michis no tiran cosas: estan equilibrando la linea temporal.",
            "el bot de musica sabe quien puso pausa, pero ha jurado no revelar nada.",
            "el emoji mas usado del servidor es en realidad el rey de una dimension paralela.",
            "hay una puerta secreta en el canal general que solo aparece cuando todos dicen buenas noches.",
        ]
        await interaction.response.send_message(f"📚 lore desbloqueado: {random.choice(premises)}")

    @app_commands.command(name="traductor_michi", description="Traduce una frase corta al idioma inventado de los michis")
    async def traductor_michi(self, interaction: discord.Interaction, frase: app_commands.Range[str, 1, 120]):
        clean = discord.utils.escape_mentions(frase.strip())
        translations = ["miau miau, prrr, mrrp.", "nyaaa, prrrt, miau.", "mrrr? miau! prrr.", "miau-miau, brrrp, nya.", "prrr prrr, meow, mrrp."]
        await interaction.response.send_message(f"🐈 original: {clean}\ntraduccion oficial del michiverso: {random.choice(translations)}")

async def setup(bot):
    await bot.add_cog(Entretenimiento(bot))