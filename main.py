import os
import requests
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1521111741193523432

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
    url = "https://corsproxy.io/?https://site.api.espncricinfo.com/apis/site/v2/sports/cricket/scoreboard"
    data = requests.get(url, timeout=20).json()

    matches = []
    for event in data.get("events", []):
        if event.get("id") and event.get("name"):
            matches.append({
                "id": str(event["id"]),
                "name": event["name"]
            })
    return matches

@app_commands.command(name="livesb", description="Choose a live cricket match")
async def livesb(interaction: discord.Interaction):
    matches = get_live_matches()

    if not matches:
        await interaction.response.send_message(
            "❌ No live matches found.",
            ephemeral=True
        )
        return

    text = "🏏 **Live Matches**\n\n"
    for i, m in enumerate(matches[:10], 1):
        text += f"{i}. {m['name']}\n"

    await interaction.response.send_message(text, ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
