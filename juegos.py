"""Minijuegos, caos controlado y mascota persistente de Papu."""
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from papu_store import load_json, save_json

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
            return await interaction.response.send_message("Ya tienes un michi, papu. Cuídalo con /michi.", ephemeral=True)
        self.pets[key] = fresh_pet(nombre)
        self.store()
        await interaction.response.send_message(f"🐈 ¡Adoptaste a **{discord.utils.escape_mentions(self.pets[key]['name'])}**! Empieza con 25 monedas.")

    @app_commands.command(name="michi", description="Consulta el estado de tu mascota")
    async def michi(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await interaction.response.send_message("Todavía no tienes michi. Usa /michi_adoptar.", ephemeral=True)
        embed = discord.Embed(title=f"🐈 {pet['name']}", color=discord.Color.orange())
        embed.add_field(name="Hambre", value=f"{pet['hunger']}/100")
        embed.add_field(name="Energía", value=f"{pet['energy']}/100")
        embed.add_field(name="Felicidad", value=f"{pet['happiness']}/100")
        embed.add_field(name="Monedas", value=f"🪙 {pet['coins']}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="michi_cuidar", description="Dale cariño y recupera felicidad")
    async def michi_cuidar(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await interaction.response.send_message("Primero adopta un michi con /michi_adoptar.", ephemeral=True)
        if not self.cooldown_ok(interaction, "care", 30):
            return await interaction.response.send_message("Tu michi necesita un descansito entre mimos. Intenta en 30 segundos.", ephemeral=True)
        pet["happiness"] = min(100, pet["happiness"] + 15)
        pet["energy"] = max(0, pet["energy"] - 2)
        pet["coins"] += 2
        pet["last_care"] = int(time.time())
        self.store()
        await interaction.response.send_message(f"💖 {pet['name']} ronronea. +2 monedas.")

    @app_commands.command(name="michi_comida", description="Compra comida para tu michi por 5 monedas")
    async def michi_comida(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await interaction.response.send_message("Primero adopta un michi con /michi_adoptar.", ephemeral=True)
        if pet["coins"] < 5:
            return await interaction.response.send_message("Te faltan monedas. Cuida a tu michi para ganar algunas.", ephemeral=True)
        pet["coins"] -= 5
        pet["hunger"] = min(100, pet["hunger"] + 25)
        pet["happiness"] = min(100, pet["happiness"] + 4)
        self.store()
        await interaction.response.send_message(f"🥣 {pet['name']} se ha comido todo. ¡Buen michi!")

    @app_commands.command(name="michi_jugar", description="Juega con tu michi y gana una recompensa")
    async def michi_jugar(self, interaction: discord.Interaction):
        pet = self.get_pet(interaction)
        if not pet:
            return await interaction.response.send_message("Primero adopta un michi con /michi_adoptar.", ephemeral=True)
        if pet["energy"] < 10:
            return await interaction.response.send_message("Tu michi está cansado; dale un rato de descanso.", ephemeral=True)
        if not self.cooldown_ok(interaction, "play", 60):
            return await interaction.response.send_message("Jugar tiene un cooldown de 60 segundos.", ephemeral=True)
        prize = random.randint(1, 5)
        pet["energy"] -= 10
        pet["happiness"] = min(100, pet["happiness"] + 10)
        pet["coins"] += prize
        self.store()
        await interaction.response.send_message(f"🧶 ¡Diversión michística! {pet['name']} ganó {prize} monedas.")

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
        await interaction.response.send_message(f"Tú: **{eleccion.value}** · Papu: **{bot_pick}**\n{result}")

    @app_commands.command(name="dado", description="Tira un dado de seis caras")
    async def dado(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🎲 Salió **{random.randint(1, 6)}**.")

    @app_commands.command(name="moneda", description="Lanza una moneda")
    async def moneda(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🪙 **{random.choice(['Cara', 'Cruz'])}**")

    @app_commands.command(name="8ball", description="Pregunta a la bola 8")
    async def ball8(self, interaction: discord.Interaction, pregunta: app_commands.Range[str, 1, 300]):
        answer = random.choice(["Sí, papu.", "Ni de chiste xd.", "Puede ser.", "Las señales dicen que sí.",
                                "No hay datos suficientes :v", "Pregunta de nuevo más tarde."])
        await interaction.response.send_message(f"🎱 **{discord.utils.escape_mentions(pregunta)}**\n{answer}")

    @app_commands.command(name="trivia", description="Pregunta de cultura general")
    async def trivia(self, interaction: discord.Interaction):
        question, options, answer = random.choice([
            ("¿Qué planeta es conocido como el planeta rojo?", ["Venus", "Marte", "Júpiter"], 1),
            ("¿Cuántos lados tiene un hexágono?", ["5", "6", "8"], 1),
            ("¿Cuál es el océano más grande?", ["Atlántico", "Índico", "Pacífico"], 2),
            ("¿Qué gas absorben principalmente las plantas?", ["Oxígeno", "Dióxido de carbono", "Helio"], 1)])
        view = TriviaView(answer)
        await interaction.response.send_message("🧠 **" + question + "**\n" + "\n".join(f"{i+1}. {o}" for i, o in enumerate(options)), view=view, ephemeral=False)

class TriviaView(discord.ui.View):
    def __init__(self, answer):
        super().__init__(timeout=45)
        self.answer = answer
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
            return await interaction.response.send_message("Esta trivia ya terminó.", ephemeral=True)
        self.used = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("¡Correcto! 🧠" if choice == self.answer else f"Nope :v La respuesta era la opción {self.answer + 1}.", ephemeral=True)
        self.stop()


async def setup(bot):
    await bot.add_cog(Juegos(bot))
