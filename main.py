import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Commands synced")

bot = Bot()

@bot.tree.command(name="pingbot", description="Test command")
async def pingbot(interaction: discord.Interaction):
    await interaction.response.send_message("🏏 Working!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
