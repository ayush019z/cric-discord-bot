import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@tree.command(name="livesb", description="Test command")
async def livesb(interaction: discord.Interaction):
    await interaction.response.send_message("🏏 Bot is working!", ephemeral=True)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
