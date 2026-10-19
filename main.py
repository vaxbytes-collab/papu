import asyncio
import logging
import os
from threading import Thread

import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from groq import Groq
from groq_config import get_groq_model
from chat_policy import PROMPT_SISTEMA, deterministic_chat_reply, normalize_papu_style
from web_search import build_search_query, format_search_context, format_search_reply, search_web, should_search_web

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
        # Valida PostgreSQL antes de cargar cogs para no arrancar con estado vacio si la DB falla.
        from papu_store import init_storage

        try:
            backend = init_storage()
            logging.info("[STORAGE] Backend activo: %s", backend)
        except Exception as exc:
            logging.exception("[STORAGE] No se pudo inicializar el almacenamiento")
            raise RuntimeError(
                "Papu no puede iniciar sin acceso a su almacenamiento configurado. "
                "Comprueba DATABASE_URL y la disponibilidad de PostgreSQL."
            ) from exc

        # Los cogs estan en la raiz del repositorio, no dentro de una carpeta cogs/.
        for module in ("moderacion", "entretenimiento", "utilidades", "juegos", "musica"):
            try:
                await self.load_extension(module)
                print(f"[OK] Modulo cargado: {module}")
            except Exception:
                logging.exception("[ERROR] No se pudo cargar %s", module)
        try:
            synced = await self.tree.sync()
            print(f"[OK] Comandos slash sincronizados: {len(synced)}")
        except Exception:
            logging.exception("[ERROR] No se pudieron sincronizar los comandos slash")

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
            elif bot.groq_client is None and not should_search_web(contenido):
                await message.channel.send(normalize_papu_style("falta configurar GROQ_API_KEY para que funcione la ia, papu."))
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
                    last_assistant_message = next(
                        (
                            item.get("content", "")
                            for item in reversed(history)
                            if item.get("role") == "assistant"
                        ),
                        "",
                    )
                    local_reply = deterministic_chat_reply(
                        contenido,
                        has_prior_context=had_prior_context,
                        has_attachments=bool(message.attachments),
                        last_assistant_message=last_assistant_message,
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
                        search_requested = should_search_web(contenido)
                        search_query = ""
                        search_results = []
                        try:
                            async with message.channel.typing():
                                if search_requested:
                                    # "busca" sin tema hereda el contexto del chat anterior.
                                    search_query = build_search_query(contenido, history[:-1])
                                    if search_query:
                                        try:
                                            search_results = await asyncio.wait_for(
                                                asyncio.to_thread(search_web, search_query),
                                                timeout=15.0,
                                            )
                                        except asyncio.TimeoutError:
                                            print("[WARN] La busqueda web agoto el tiempo de espera.")
                                            search_results = []
                                        except Exception:
                                            logging.exception("[WARN] Fallo la busqueda web")
                                            search_results = []

                                    if not search_query:
                                        answer = normalize_papu_style(
                                            "arre, compa, si te busco el dato, pero no me quedo claro el tema. "
                                            "dime que quieres encontrar y me pongo a buscarlo :v"
                                        )
                                    elif not search_results:
                                        answer = normalize_papu_style(
                                            f"ay, compa, intente buscar «{search_query[:100]}» pero el buscador no me devolvio "
                                            "resultados esta vez. no te voy a inventar datos; probamos otra consulta? :v"
                                        )
                                    elif bot.groq_client is None:
                                        answer = normalize_papu_style(format_search_reply(search_query, search_results))
                                if not search_requested or (search_query and search_results and bot.groq_client is not None):
                                    model_messages = [dict(item) for item in history]
                                    if search_requested and search_results:
                                        model_messages.insert(
                                            1,
                                            {
                                                "role": "system",
                                                "content": format_search_context(search_query, search_results),
                                            },
                                        )
                                    response = await asyncio.wait_for(
                                        asyncio.to_thread(
                                            bot.groq_client.chat.completions.create,
                                            model=get_groq_model("GROQ_CHAT_MODEL"),
                                            messages=model_messages,
                                            temperature=0.7,
                                            max_tokens=700,
                                        ),
                                        timeout=30.0,
                                    )
                                    answer = normalize_papu_style((response.choices[0].message.content or "").strip())
                                    if not answer:
                                        answer = normalize_papu_style("miau, la ia devolvio una respuesta vacia :v")
                                    answer = answer[:1900]

                            history.append({"role": "assistant", "content": answer})
                            HISTORIALES_USUARIOS[user_key] = [history[0]] + history[-MAX_HISTORIAL:]
                            keep_turn = True
                        except asyncio.TimeoutError:
                            answer = normalize_papu_style("la ia se quedo pensando demasiado, compa 😿. intentalo otra vez en unos segundos :v")
                            print("[WARN] Groq agoto el tiempo de espera al responder un mensaje.")
                        except Exception:
                            answer = normalize_papu_style("se me trabaron las patitas con la ia :'v intenta de nuevo en un rato.")
                            logging.exception("[ERROR] Fallo la llamada a Groq")
                        finally:
                            # No dejes preguntas fallidas acumuladas en el historial.
                            if not keep_turn and history and history[-1].get("role") == "user":
                                history.pop()

                    try:
                        answer = normalize_papu_style(answer)
                        await message.channel.send(
                            answer,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    except discord.HTTPException:
                        logging.exception(
                            "[ERROR] Discord rechazó el mensaje. Comprueba View Channel y Send Messages en el canal."
                        )
    finally:
        await bot.process_commands(message)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("Falta DISCORD_TOKEN en las variables de entorno.")
    keep_alive()
    bot.run(DISCORD_TOKEN)
