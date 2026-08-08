import os
import requests
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
SPORTSMONKS = os.getenv("SPORTSMONKS_TOKEN")
GUILD_ID = 1521111741193523432

BASE = "https://api.sportmonks.com/v3/cricket"

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)

        # Remove old commands
        self.tree.clear_commands(guild=guild)
        self.tree.clear_commands(guild=None)

        # Register fresh command
        self.tree.add_command(livesb, guild=guild)

        await self.tree.sync(guild=guild)
        print("Guild commands synced")

bot = Bot()

@app_commands.command(name="livesb", description="Test SportsMonks API")
async def livesb(interaction: discord.Interaction):
    try:
        url = f"{BASE}/fixtures/live?api_token={SPORTSMONKS}"
        r = requests.get(url, timeout=20)

        text = r.text[:1800]  # keep under Discord limit

        await interaction.response.send_message(
            f"Status: {r.status_code}\n```json\n{text}\n```",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"Error: {e}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
