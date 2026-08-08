import os
import requests
from bs4 import BeautifulSoup
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
        print("Commands synced")

bot = Bot()

def fetch_live_matches():
    url = "https://www.cricbuzz.com/cricket-match/live-scores"
    html = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0"
    }, timeout=20).text

    soup = BeautifulSoup(html, "html.parser")

    matches = []

    for a in soup.select("a.cb-lv-scrs-well")[:10]:
        title = a.select_one("div.text-bold")
        score = a.select_one("div.cb-lv-scrs-col.text-black")

        if title:
            matches.append({
                "title": title.get_text(" ", strip=True),
                "score": score.get_text(" ", strip=True) if score else "Live"
            })

    return matches

@app_commands.command(name="livesb", description="Show live cricket matches")
async def livesb(interaction: discord.Interaction):
    try:
        matches = fetch_live_matches()

        if not matches:
            await interaction.response.send_message(
                "❌ No live matches found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏏 Live Cricket Matches",
            color=0x00BFFF
        )

        for m in matches:
            embed.add_field(
                name=m["title"][:256],
                value=m["score"][:1024],
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            f"Error: {e}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
