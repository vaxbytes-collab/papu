"""Minijuegos, caos controlado y mascota persistente de Papu."""
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from papu_store import load_json, save_json
from papu_ui import branded_embed, progress_bar, send_feedback

PET_NAMES = ["Michi", "Papu", "Bigotes", "Choclo", "Gatito"]


def fresh_pet(name=None):
    return {"name": (name or random.choice(PET_NAMES))[:24], "hunger": 70, "energy": 70,
            "happiness": 70, "coins": 25, "created": int(time.time()), "last_care": int(time.time())}


class Juegos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pets = load_json("pets.json", {})
        self.cooldowns = {}

    def pet_key(self, interaction):
        return f"{interaction.guild_id or 'dm'}:{interaction.user.id}"

    def get_pet(self, interaction):
        return self.pets.get(self.pet_key(interaction))

    def store(self):
        save_json("pets.json", self.pets)

    @app_commands.command(name="michi_adoptar", description="Adopta tu propio michi virtual")
    async def michi_adoptar(self, interaction: discord.Interaction, nombre: app_commands.Range[str, 1, 24] = None):
        key = self.pet_key(interaction)
        if key in self.pets:
            return await send_feedback(interaction, "Ya tienes una mascota. Consulta su estado con /michi.", title="Ya tienes un michi", tone="info")
        self.pets[key] = fresh_pet(nombre)
        self.store()
        pet_name = discord.utils.escape_mentions(self.pets[key]["name"])
        embed = branded_embed(
            title="🐈 ¡Nuevo michi adoptado!",
            description=f"**{pet_name}** ya forma parte de tu vida digital.\n\nTu aventura empieza con **25 monedas**. Cuídalo, juega con él y vuelve a visitarlo.",
            color=0xFDBA74,
            footer=f"Mascota de {interaction.user.display_name}",
        )
        embed.add_field(name="🍗 Hambre", value=f"{progress_bar(70)}\n70/100", inline=True)
        embed.add_field(name="⚡ Energía", value=f"{progress_bar(70)}\n70/100", inline=True)
        embed.add_field(name="💖 Felicidad", value=f"{progress_bar(70)}\n70/100", inline=True)
        embed.add_field(name="🪙 Monedas", value="**25**", inline=True)
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="michi", description="Consulta el estado de tu mascota")
    async def michi(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await send_feedback(interaction, "Adopta una mascota con /michi_adoptar para empezar.", title="Todavía no tienes michi", tone="info")
        hunger = max(0, min(100, int(pet.get("hunger", 0))))
        energy = max(0, min(100, int(pet.get("energy", 0))))
        happiness = max(0, min(100, int(pet.get("happiness", 0))))
        if hunger < 25:
            mood, tone = "Necesita comida. Su pancita está pidiendo atención.", 0xFB7185
        elif energy < 25:
            mood, tone = "Está cansadito; una pausa y un rincón cómodo le vendrían bien.", 0xFDBA74
        elif happiness < 35:
            mood, tone = "Necesita un poco de cariño y tiempo para jugar.", 0xA78BFA
        else:
            mood, tone = "Todo tranquilo: listo para una nueva aventura contigo.", 0x67E8F9
        embed = branded_embed(
            title=f"🐈 {discord.utils.escape_mentions(pet['name'])}",
            description=f"*{mood}*",
            color=tone,
            footer=f"Mascota de {interaction.user.display_name}",
        )
        embed.set_author(name=f"El michi de {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="🍗 Hambre", value=f"{progress_bar(hunger)}\n**{hunger}/100**", inline=False)
        embed.add_field(name="⚡ Energía", value=f"{progress_bar(energy)}\n**{energy}/100**", inline=False)
        embed.add_field(name="💖 Felicidad", value=f"{progress_bar(happiness)}\n**{happiness}/100**", inline=False)
        embed.add_field(name="🪙 Monedas", value=f"**{pet.get('coins', 0)}**", inline=True)
        embed.add_field(name="📅 Adoptado", value=f"<t:{int(pet.get('created', time.time()))}:D>", inline=True)
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="michi_cuidar", description="Dale cariño y recupera felicidad")
    async def michi_cuidar(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await send_feedback(interaction, "Primero adopta un michi con /michi_adoptar.", title="Necesitas una mascota", tone="warning")
        if not self.cooldown_ok(interaction, "care", 30):
            return await send_feedback(interaction, "Tu michi necesita un descansito entre mimos. Prueba de nuevo en unos segundos.", title="Tiempo de descanso", tone="warning")
        pet["happiness"] = min(100, pet["happiness"] + 15)
        pet["energy"] = max(0, pet["energy"] - 2)
        pet["coins"] += 2
        pet["last_care"] = int(time.time())
        self.store()
        embed = branded_embed(title="💖 Momento de cariño", description=f"**{discord.utils.escape_mentions(pet['name'])}** ronronea contento.\n\n**+2 monedas** · felicidad +15 · energía −2", color=0xA78BFA, footer="Michi • Cuidado")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="michi_comida", description="Compra comida para tu michi por 5 monedas")
    async def michi_comida(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await send_feedback(interaction, "Primero adopta un michi con /michi_adoptar.", title="Necesitas una mascota", tone="warning")
        if pet["coins"] < 5:
            return await send_feedback(interaction, "Te faltan monedas. Cuida a tu michi para ganar algunas.", title="No hay monedas suficientes", tone="warning")
        pet["coins"] -= 5
        pet["hunger"] = min(100, pet["hunger"] + 25)
        pet["happiness"] = min(100, pet["happiness"] + 4)
        self.store()
        embed = branded_embed(title="🥣 ¡Hora de comer!", description=f"**{discord.utils.escape_mentions(pet['name'])}** se ha comido todo.\n\nHambre **+25** · felicidad **+4** · coste **5 monedas**", color=0xFDBA74, footer="Michi • Cuidado")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="michi_jugar", description="Juega con tu michi y gana una recompensa")
    async def michi_jugar(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await send_feedback(interaction, "Primero adopta un michi con /michi_adoptar.", title="Necesitas una mascota", tone="warning")
        if pet["energy"] < 10:
            return await send_feedback(interaction, "Tu michi está cansado; dale un rato de descanso.", title="Tu michi necesita descansar", tone="warning")
        if not self.cooldown_ok(interaction, "play", 60):
            return await send_feedback(interaction, "Jugar tiene un tiempo de espera de 60 segundos.", title="Pequeño descanso", tone="warning")
        prize = random.randint(1, 5)
        pet["energy"] -= 10
        pet["happiness"] = min(100, pet["happiness"] + 10)
        pet["coins"] += prize
        self.store()
        embed = branded_embed(title="🧶 ¡Hora de jugar!", description=f"**{discord.utils.escape_mentions(pet['name'])}** se divirtió un montón.\n\n**Recompensa:** +{prize} monedas\n**Felicidad:** +10 · **Energía:** −10", color=0x67E8F9, footer="Michi • Actividad")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    def cooldown_ok(self, interaction, action, seconds):
        key = (interaction.guild_id, interaction.user.id, action)
        now = time.monotonic()
        if now - self.cooldowns.get(key, 0) < seconds:
            return False
        self.cooldowns[key] = now
        return True

    @app_commands.command(name="ppt", description="Piedra, papel o tijera contra Papu")
    @app_commands.choices(eleccion=[
        app_commands.Choice(name="piedra", value="piedra"),
        app_commands.Choice(name="papel", value="papel"),
        app_commands.Choice(name="tijera", value="tijera")])
    async def ppt(self, interaction: discord.Interaction, eleccion: app_commands.Choice[str]):
        bot_pick = random.choice(["piedra", "papel", "tijera"])
        wins = {("piedra", "tijera"), ("papel", "piedra"), ("tijera", "papel")}
        result = "Empate :v" if eleccion.value == bot_pick else ("Ganaste, papu 🎉" if (eleccion.value, bot_pick) in wins else "Papu ganó esta ronda xd")
        embed = branded_embed(title="✊ Piedra, papel o tijera", description=f"**Tu elección:** {eleccion.value}\n**Papu:** {bot_pick}\n\n## {result}", color=0xA78BFA, footer="Papu Arcade • Ronda finalizada")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="dado", description="Tira un dado de seis caras")
    async def dado(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        embed = branded_embed(title="🎲 Dado", description=f"# {result}\n\n*Dado de seis caras*", color=0x67E8F9, footer="Papu Arcade • Resultado aleatorio")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="moneda", description="Lanza una moneda")
    async def moneda(self, interaction: discord.Interaction):
        result = random.choice(["Cara", "Cruz"])
        embed = branded_embed(title="🪙 Lanzamiento de moneda", description=f"# {result}", color=0xFDBA74, footer="Papu Arcade • Resultado aleatorio")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Pregunta a la bola 8")
    async def ball8(self, interaction: discord.Interaction, pregunta: app_commands.Range[str, 1, 300]):
        answer = random.choice(["Sí, papu.", "Ni de chiste xd.", "Puede ser.", "Las señales dicen que sí.",
                                "No hay datos suficientes :v", "Pregunta de nuevo más tarde."])
        embed = branded_embed(title="🎱 Bola 8", description=f"**Pregunta:** {discord.utils.escape_mentions(pregunta)}\n\n**Respuesta de Papu:** {answer}", color=0xA78BFA, footer="Papu Arcade • Solo por diversión")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="trivia", description="Pregunta de cultura general")
    async def trivia(self, interaction: discord.Interaction):
        question, options, answer = random.choice([
            ("¿Qué planeta es conocido como el planeta rojo?", ["Venus", "Marte", "Júpiter"], 1),
            ("¿Cuántos lados tiene un hexágono?", ["5", "6", "8"], 1),
            ("¿Cuál es el océano más grande?", ["Atlántico", "Índico", "Pacífico"], 2),
            ("¿Qué gas absorben principalmente las plantas?", ["Oxígeno", "Dióxido de carbono", "Helio"], 1)])
        view = TriviaView(answer, question, options)
        embed = branded_embed(
            title="🧠 Trivia de Papu",
            description=f"**{question}**\n\n" + "\n".join(f"**{i + 1}.** {option}" for i, option in enumerate(options)),
            color=0x67E8F9,
            footer="Elige una respuesta • una oportunidad por ronda",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())

class TriviaView(discord.ui.View):
    def __init__(self, answer, question, options):
        super().__init__(timeout=45)
        self.answer = answer
        self.question = question
        self.options = options
        self.used = False

    @discord.ui.button(label="1", style=discord.ButtonStyle.secondary)
    async def one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.respond(interaction, 0)

    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary)
    async def two(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.respond(interaction, 1)

    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary)
    async def three(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.respond(interaction, 2)

    async def respond(self, interaction, choice):
        if self.used:
            return await send_feedback(interaction, "Esta ronda ya terminó. Espera la siguiente trivia.", title="Ronda finalizada", tone="info")
        self.used = True
        for child in self.children:
            child.disabled = True
        lines = []
        for index, option in enumerate(self.options):
            if index == self.answer:
                lines.append(f"✅ **{index + 1}. {option}** — respuesta correcta")
            elif index == choice:
                lines.append(f"❌ ~~{index + 1}. {option}~~ — tu respuesta")
            else:
                lines.append(f"**{index + 1}.** {option}")
        result_title = "🏆 ¡Respuesta correcta!" if choice == self.answer else "🧠 Se revela la respuesta"
        embed = branded_embed(
            title=result_title,
            description=f"**{self.question}**\n\n" + "\n".join(lines),
            color=0x6EE7B7 if choice == self.answer else 0xFDBA74,
            footer=f"Respondió {interaction.user.display_name} • Papu Arcade",
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()



async def setup(bot):
    await bot.add_cog(Juegos(bot))
