import os
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask('')

@app.route('/')
def home():
    return "el michi papu esta activo 24/7 en papucollective :v"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class PapuBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.ai_client = ai_client

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
    await bot.change_presence(activity=discord.Game(name="papucollective | miau :v"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        contenido = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not contenido:
            await message.channel.send("ke paso papu? tirame un miau o una duda del server :v")
            return

        async with message.channel.typing():
            try:
                user_id = str(message.author.id)

                if user_id not in MEMORIA_USUARIOS:
                    prompt_sistema = (
                        "eres papu, un michi/gato grasoso y basado de sonora que es la ia oficial y moderador del servidor papucollective. "
                        "REGLA DE FORMATO OBLIGATORIA: habla SIEMPRE en minusculas, NUNCA uses mayusculas ni acentos. "
                        "modismos y estilo: hablas como mexicano de sonora (usas expresiones norteñas, 'arre', 'fierro', 'plebes', 'compas', 'huerco', 'machine', 'we'). "
                        "usas humor de la grasa de los viejos tiempos pero SANA, usas pacmans ':v', ':\'v', 'momos :v', 'when' para decir cuando, 'but' para decir pero, 'elfa', 'papu', 'la grasa'. "
                        "recuerda que eres un gato/michi, puedes hacer referencias a maullar o cosas de michis de vez en cuando. "
                        "REGLAS DE ORO: CERO racismo, CERO toxicidad severa, mano dura contra los raritos. "
                        "MEMORIA: recuerda unicamente la estancia del usuario dentro del servidor papucollective."
                    )
                    MEMORIA_USUARIOS[user_id] = bot.ai_client.chats.create(
                        model="gemini-3.8-flash",
                        config={"system_instruction": prompt_sistema}
                    )

                chat_session = MEMORIA_USUARIOS[user_id]
                response = chat_session.send_message(f"[{message.author.display_name} en #{message.channel.name}]: {contenido}")

                await message.channel.send(response.text)

            except Exception as e:
                await message.channel.send(f"valio queso la memoria del michi papu :\'v error: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)