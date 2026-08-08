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
        self.tree.clear_commands(guild=guild)
        self.tree.add_command(livesb, guild=guild)
        await self.tree.sync(guild=guild)
        print("Guild commands synced")

bot = Bot()

def get_live_matches():
    url = f"{BASE}/fixtures/live?api_token={SPORTSMONKS}"
    r = requests.get(url, timeout=20)
    data = r.json()

    matches = []

    for m in data.get("data", []):
        name = m.get("name")
        match_id = m.get("id")

        if name and match_id:
            matches.append(f"• {name} (ID: {match_id})")

    return matches

@app_commands.command(name="livesb", description="Show live matches")
async def livesb(interaction: discord.Interaction):
    matches = get_live_matches()

    if not matches:
        await interaction.response.send_message(
            "❌ No live matches found.",
            ephemeral=True
        )
        return

    text = "🏏 **Live Matches**\n\n" + "\n".join(matches[:15])

    await interaction.response.send_message(text, ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
