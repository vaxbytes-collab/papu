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
    return "PapuBot está activo 24/7 en PapuCollective :v"

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
                print(f"--> Módulo {cog} cargado correctamente papu :v")
            except Exception as e:
                print(f"--> Error al cargar {cog}: {e}")

        try:
            synced = await self.tree.sync()
            print(f"--> Sincronizados {len(synced)} comandos slash correctamente.")
        except Exception as e:
            print(f"--> Error sincronizando comandos slash: {e}")

bot = PapuBot()

MEMORIA_USUARIOS = {}

@bot.event
async def on_ready():
    print("==========================================")
    print(f"   PAPU BOT ACTIVO COMO: {bot.user}")
    print(f"   ID: {bot.user.id}")
    print("==========================================")
    await bot.change_presence(activity=discord.Game(name="PapuCollective | Mencióname o usa /"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        contenido = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not contenido:
            await message.channel.send("¿Qué pasó papu? Etiquétame con una pregunta o duda sobre el servidor :v")
            return

        async with message.channel.typing():
            try:
                user_id = str(message.author.id)

                if user_id not in MEMORIA_USUARIOS:
                    prompt_sistema = (
                        "Eres Papu, la inteligencia artificial oficial y moderador del servidor de Discord PapuCollective. "
                        "Te expresas con humor desenfadado, usas pacmans ':v' o ':\'v', y hablas estilo La Grasa pero SANA. "
                        "REGLAS ESTRICTAS: CERO racismo, CERO toxicidad severa, CERO contenido inapropiado y mano dura contra los 'raritos'. "
                        "MEMORIA LIMITADA AL SERVIDOR: Recuerda únicamente la estancia del usuario en el servidor PapuCollective, "
                        "sus interacciones en la comunidad, roles, anécdotas del chat y convivencia del server."
                    )
                    MEMORIA_USUARIOS[user_id] = bot.ai_client.chats.create(
                        model="gemini-2.5-flash",
                        config={"system_instruction": prompt_sistema}
                    )

                chat_session = MEMORIA_USUARIOS[user_id]
                response = chat_session.send_message(f"[{message.author.display_name} en #{message.channel.name}]: {contenido}")

                await message.channel.send(response.text)

            except Exception as e:
                await message.channel.send(f"Valió queso la memoria de la IA papu :\'v error: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)