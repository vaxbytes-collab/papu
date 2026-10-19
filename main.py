import asyncio
import os
from threading import Thread

import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from groq import Groq
from groq_config import get_groq_model
from chat_policy import PROMPT_SISTEMA, deterministic_chat_reply

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Evita esperas largas y reintentos ocultos cuando el proveedor no responde.
groq_client = Groq(api_key=GROQ_API_KEY, timeout=25.0, max_retries=0) if GROQ_API_KEY else None

app = Flask(__name__)

@app.get("/")
def home():
    return "el michi papu esta activo :v"

def keep_alive():
    Thread(
        target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), use_reloader=False),
        daemon=True,
    ).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class PapuBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.groq_client = groq_client

    async def setup_hook(self):
        # Los cogs estan en la raiz del repositorio, no dentro de una carpeta cogs/.
        for module in ("moderacion", "entretenimiento", "utilidades", "juegos", "musica"):
            try:
                await self.load_extension(module)
                print(f"[OK] Modulo cargado: {module}")
            except Exception:
                print(f"[ERROR] No se pudo cargar {module}", exc_info=True)
        try:
            synced = await self.tree.sync()
            print(f"[OK] Comandos slash sincronizados: {len(synced)}")
        except Exception:
            print("[ERROR] No se pudieron sincronizar los comandos slash", exc_info=True)

bot = PapuBot()
HISTORIALES_USUARIOS = {}
BLOQUEOS_USUARIOS = {}
MAX_HISTORIAL = 13

@bot.event
async def on_ready():
    print(f"Papu conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="papucollective | miau :v"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    try:
        cog = bot.get_cog("Moderacion")
        auto_reply = bool(cog and cog.should_reply_without_mention(message))
        mentioned = bool(bot.user and bot.user in message.mentions)

        if mentioned or auto_reply:
            contenido = message.content
            if bot.user:
                contenido = contenido.replace(f"<@{bot.user.id}>", "")
                contenido = contenido.replace(f"<@!{bot.user.id}>", "")
            contenido = contenido.strip()

            if not contenido and not message.attachments:
                await message.channel.send("ke paso papu? tirame una duda o una fotito :v")
            elif bot.groq_client is None:
                await message.channel.send("falta configurar GROQ_API_KEY para que funcione la ia, papu.")
            else:
                user_key = f"{message.guild.id if message.guild else 'dm'}:{message.author.id}"
                lock = BLOQUEOS_USUARIOS.setdefault(user_key, asyncio.Lock())

                # Serializa los mensajes del mismo usuario para que el historial
                # no cambie mientras la petición está en curso.
                async with lock:
                    history = HISTORIALES_USUARIOS.setdefault(
                        user_key, [{"role": "system", "content": PROMPT_SISTEMA}]
                    )
                    had_prior_context = len(history) > 1
                    local_reply = deterministic_chat_reply(
                        contenido,
                        has_prior_context=had_prior_context,
                        has_attachments=bool(message.attachments),
                    )
                    history.append({
                        "role": "user",
                        "content": (contenido or "El usuario adjunto una imagen.")[:4000],
                    })
                    answer = None
                    keep_turn = False

                    if local_reply is not None:
                        # Casos claros y breves se resuelven en español sin llamar al modelo.
                        answer = local_reply
                        history.append({"role": "assistant", "content": answer})
                        HISTORIALES_USUARIOS[user_key] = [history[0]] + history[-MAX_HISTORIAL:]
                        keep_turn = True
                    else:
                        try:
                            async with message.channel.typing():
                                response = await asyncio.wait_for(
                                    asyncio.to_thread(
                                        bot.groq_client.chat.completions.create,
                                        model=get_groq_model("GROQ_CHAT_MODEL"),
                                        messages=[dict(item) for item in history],
                                        temperature=0.7,
                                        max_tokens=700,
                                    ),
                                    timeout=30.0,
                                )
                            answer = (response.choices[0].message.content or "").strip()
                            if not answer:
                                answer = "miau, la IA devolvió una respuesta vacía :v"
                            answer = answer[:1900]
                            history.append({"role": "assistant", "content": answer})
                            HISTORIALES_USUARIOS[user_key] = [history[0]] + history[-MAX_HISTORIAL:]
                            keep_turn = True
                        except asyncio.TimeoutError:
                            answer = "Papu se quedó esperando a la IA y agotó el tiempo de espera 😿. Prueba otra vez en unos segundos."
                            print("[WARN] Groq agotó el tiempo de espera al responder un mensaje.")
                        except Exception:
                            answer = "se me trabaron las patitas con la IA :'v intenta de nuevo en un rato."
                            print("[ERROR] Falló la llamada a Groq", exc_info=True)
                        finally:
                            # No dejes preguntas fallidas acumuladas en el historial.
                            if not keep_turn and history and history[-1].get("role") == "user":
                                history.pop()

                    try:
                        await message.channel.send(
                            answer,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    except discord.HTTPException:
                        print(
                            "[ERROR] Groq terminó, pero Discord rechazó el mensaje. "
                            "Comprueba View Channel y Send Messages en el canal.",
                            exc_info=True,
                        )
    finally:
        await bot.process_commands(message)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("Falta DISCORD_TOKEN en las variables de entorno.")
    keep_alive()
    bot.run(DISCORD_TOKEN)
