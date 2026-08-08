import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@tree.command(name="livesb", description="Test live scoreboard")
async def livesb(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🏏 CPL Test Match",
        color=0x00BFFF
    )

    embed.add_field(
        name="St Lucia Kings",
        value="**176/4 (18.3)**",
        inline=False
    )

    embed.add_field(
        name="Guyana Amazon Warriors",
        value="**Yet to bat**",
        inline=False
    )

    embed.add_field(
        name="Status",
        value="SLK need 15 runs from 9 balls",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
