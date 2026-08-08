import os
import requests
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
PROXY = os.getenv("PROXY_URL")
GUILD_ID = 1521111741193523432

proxies = {
    "http": PROXY,
    "https": PROXY,
}

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)

        self.tree.clear_commands(guild=guild)
        self.tree.clear_commands(guild=None)

        self.tree.add_command(livesb, guild=guild)

        await self.tree.sync(guild=guild)
        print("Guild commands synced")

bot = Bot()

@app_commands.command(name="livesb", description="Test proxy with timeout")
async def livesb(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        r = requests.get(
            "https://api.ipify.org?format=json",
            proxies=proxies,
            timeout=(5, 10),  # 5s connect, 10s read
            headers={"User-Agent": "Mozilla/5.0"}
        )

        await interaction.followup.send(
            f"✅ Proxy works\\nStatus: {r.status_code}\\nIP: {r.text}",
            ephemeral=True
        )

    except requests.exceptions.ConnectTimeout:
        await interaction.followup.send(
            "❌ Proxy connection timed out (cannot reach proxy server)",
            ephemeral=True
        )

    except requests.exceptions.ReadTimeout:
        await interaction.followup.send(
            "❌ Proxy connected but response timed out",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Proxy failed: {type(e).__name__}: {e}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
