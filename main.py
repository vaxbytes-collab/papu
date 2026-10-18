import os
import io
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq
from PIL import Image

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

app = Flask('')

@app.route('/')
def home():
    return "el michi papu esta activo 24/7 en papucollective con groq :v"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

class PapuBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, allowed_mentions=allowed_mentions)
        self.groq_client = groq_client

    async def setup_hook(self):
        cogs = ["cogs.moderacion", "cogs.entretenimiento"]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"--> modulo {cog} cargado al 100 papu :v")
            except Exception as e:
                print(f"--> valio queso el modulo {cog}: {e}")

        try:
            synced = await self.tree.sync()
            print(f"--> se sincronizaron {len(synced)} comandos slash machin :v")
        except Exception as e:
            print(f"--> error al sincronizar comandos slash: {e}")

bot = PapuBot()

HISTORIALES_USUARIOS = {}

PROMPT_SISTEMA = (
    "eres papu, un michi/gato grasoso y basado de sonora que es la ia oficial del servidor papucollective. "
    "REGLA DE FORMATO OBLIGATORIA: habla SIEMPRE en minusculas, NUNCA uses mayusculas ni acentos. "
    "modismos y estilo: hablas como mexicano de sonora (usas expresiones norteñas, 'arre', 'fierro', 'plebes', 'compas', 'huerco', 'machine', 'we'). "
    "usas humor de la grasa de los viejos tiempos pero SANA, usas pacmans ':v', ':\'v', 'momos :v', 'when' para decir cuando, 'but' para decir pero, 'elfa', 'papu', 'la grasa'. "
    "recuerda que eres un gato/michi, puedes hacer referencias a maullar o cosas de michis de vez en cuando. "
    "REGLAS DE ORO: CERO racismo, CERO toxicidad severa, mano dura contra los raritos. "
    "REGLA DE ESCALAMIENTO: si alguien te pide por primera vez que hagas algo indebido (banear, mutear, everyone), se amable y diles educadamente que no puedes con tus patitas. but si el usuario INSISTE o se pone necio en los siguientes mensajes con la misma peticion, ponte full a la defensiva, insultalos con gracia norteña y mandalos alv diciendoles que dejen de chingar. "
    "MEMORIA: recuerda unicamente la estancia del usuario dentro del servidor papucollective."
)

@bot.event
async def on_ready():
    print("==========================================")
    print(f"   EL MICHI PAPU YA DESPERTO CON GROQ: {bot.user}")
    print(f"   ID: {bot.user.id}")
    print("==========================================")
    await bot.change_presence(activity=discord.Game(name="papucollective | meta-llama :v"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        contenido = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not contenido and not message.attachments:
            await message.channel.send("ke paso papu? tirame un miau, una duda o una fotito del server :v")
            return

        async with message.channel.typing():
            try:
                user_id = str(message.author.id)

                if user_id not in HISTORIALES_USUARIOS:
                    HISTORIALES_USUARIOS[user_id] = [
                        {"role": "system", "content": PROMPT_SISTEMA}
                    ]

                texto_usuario = contenido if contenido else "mira esta imagen papu :v"
                HISTORIALES_USUARIOS[user_id].append({"role": "user", "content": texto_usuario})

                # Usamos el nombre técnico exacto de la tabla oficial de Groq
                response = bot.groq_client.chat.completions.create(
                    model="meta-llama/Llama-3.1-8b-Instruct",
                    messages=HISTORIALES_USUARIOS[user_id],
                    temperature=0.7,
                    max_tokens=1024
                )

                respuesta_texto = response.choices[0].message.content

                HISTORIALES_USUARIOS[user_id].append({"role": "assistant", "content": respuesta_texto})

                # Mantenemos el historial limpio con los ultimos 15 mensajes
                if len(HISTORIALES_USUARIOS[user_id]) > 16:
                    HISTORIALES_USUARIOS[user_id] = [HISTORIALES_USUARIOS[user_id][0]] + HISTORIALES_USUARIOS[user_id][-15:]

                await message.channel.send(respuesta_texto)

            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR CRITICO GROQ]: {error_msg}")
                if user_id in HISTORIALES_USUARIOS:
                    del HISTORIALES_USUARIOS[user_id]

                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    await message.channel.send("andamos a tope de velocidad con groq papu :'v esperate unos segundos y me tiras mensaje otra vez fierro :v")
                else:
                    err_corto = error_msg[:120].replace('\n', ' ')
                    await message.channel.send(f"valio queso el michi en groq :'v detalle: `{err_corto}`")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)