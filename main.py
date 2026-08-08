import os
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
        self.tree.clear_commands(guild=None)
        self.tree.add_command(pingbot, guild=guild)
        await self.tree.sync(guild=guild)
        print("Guild commands synced")

bot = Bot()

@app_commands.command(name="pingbot", description="Test command")
async def pingbot(interaction: discord.Interaction):
    await interaction.response.send_message("🏏 Working!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
