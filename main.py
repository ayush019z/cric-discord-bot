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

        # Remove old commands
        self.tree.clear_commands(guild=guild)
        self.tree.clear_commands(guild=None)

        # Add fresh command
        self.tree.add_command(livesb, guild=guild)

        await self.tree.sync(guild=guild)
        print("Guild commands synced")

bot = Bot()

def get_live_matches():
    url = "https://site.api.espncricinfo.com/apis/site/v2/sports/cricket/scoreboard"

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    data = r.json()

    matches = []

    for event in data.get("events", []):
        name = event.get("name")

        status = (
            event.get("status", {})
            .get("type", {})
            .get("description", "Live")
        )

        if name:
            matches.append(f"• {name} — {status}")

    return matches

@app_commands.command(name="livesb", description="Show Cricinfo live matches")
async def livesb(interaction: discord.Interaction):
    try:
        matches = get_live_matches()

        if not matches:
            await interaction.response.send_message(
                "❌ No matches found.",
                ephemeral=True
            )
            return

        text = "🏏 **Cricinfo Live Matches**\n\n" + "\n".join(matches[:15])

        await interaction.response.send_message(text, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            f"Error: {e}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
