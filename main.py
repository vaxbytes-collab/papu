import os
import io
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

app = Flask('')

@app.route('/')
def home():
    return "el michi papu esta activo 24/7 en papucollective con 1,500 RPD :v"

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

MEMORIA_USUARIOS = {}

@bot.event
async def on_ready():
    print("==========================================")
    print(f"   EL MICHI PAPU YA DESPERTO COMO: {bot.user}")
    print(f"   ID: {bot.user.id}")
    print("==========================================")
    await bot.change_presence(activity=discord.Game(name="papucollective | miau 1500 rpd :v"))

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

                prompt_sistema = (
                    "eres papu, un michi/gato grasoso y basado de sonora que es la ia oficial del servidor papucollective. "
                    "REGLA DE FORMATO OBLIGATORIA: habla SIEMPRE en minusculas, NUNCA uses mayusculas ni acentos. "
                    "modismos y estilo: hablas como mexicano de sonora (usas expresiones norteñas, 'arre', 'fierro', 'plebes', 'compas', 'huerco', 'machine', 'we'). "
                    "usas humor de la grasa de los viejos tiempos pero SANA, usas pacmans ':v', ':\'v', 'momos :v', 'when' para decir cuando, 'but' para decir pero, 'elfa', 'papu', 'la grasa'. "
                    "recuerda que eres un gato/michi, puedes hacer referencias a maullar o cosas de michis de vez en cuando. "
                    "REGLAS DE ORO: CERO racismo, CERO toxicidad severa, mano dura contra los raritos. "
                    "REGLA DE ESCALAMIENTO: si alguien te pide por primera vez que hagas algo indebido (banear, mutear, everyone), se amable y diles educadamente que no puedes con tus patitas. but si el usuario INSISTE o se pone necio en los siguientes mensajes con la misma peticion, ponte full a la defensiva, insultalos con gracia norteña y mandalos alv diciendoles que dejen de chingar. "
                    "MULTIMODALIDAD: puedes ver perfectamente las imagenes que te manden adjuntas en el chat y opinar sobre ellas con tu estilo de michi grasoso. "
                    "MEMORIA: recuerda unicamente la estancia del usuario dentro del servidor papucollective."
                )

                if user_id not in MEMORIA_USUARIOS:
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=prompt_sistema
                    )
                    MEMORIA_USUARIOS[user_id] = model.start_chat(history=[])

                chat_inputs = []
                if contenido:
                    chat_inputs.append(contenido)

                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            image_bytes = await attachment.read()
                            img = Image.open(io.BytesIO(image_bytes))
                            chat_inputs.append(img)

                chat_session = MEMORIA_USUARIOS[user_id]
                response = chat_session.send_message(chat_inputs)

                await message.channel.send(response.text)

            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR CRITICO MICHI]: {error_msg}")

                if user_id in MEMORIA_USUARIOS:
                    del MEMORIA_USUARIOS[user_id]

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    await message.channel.send("ya me gaste los sobrecitos de atun diarios de la ia papu :'v se acabo la cuota miau, esperate un ratito fierro :v")
                elif any(code in error_msg for code in ["500", "502", "503", "504", "UNAVAILABLE"]):
                    await message.channel.send("andan sobrecargados los servidores de la ia papu :'v tirame el mensaje otra vez en unos segundos miau :v")
                else:
                    err_corto = error_msg[:120].replace('\n', ' ')
                    await message.channel.send(f"valio queso el michi papu :'v detalle: `{err_corto}`")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)