import os
import requests
import discord
from discord import app_commands
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

active = {}

def get_live_matches():
    url = "https://site.api.espncricinfo.com/apis/site/v2/sports/cricket/scoreboard"
    r = requests.get(url, timeout=15)
    data = r.json()

    matches = []

    for event in data.get("events", []):
        match_id = event.get("id")
        name = event.get("name")

        if match_id and name:
            matches.append({
                "id": str(match_id),
                "name": name
            })

    return matches

def get_match(match_id):
    url = f"https://site.api.espncricinfo.com/apis/site/v2/sports/cricket/summary?event={match_id}"
    r = requests.get(url, timeout=15)
    return r.json()

def build_embed(data):
    header = data.get("header", {})
    status = data.get("status", {})
    match = data.get("match", {})

    title = header.get("name", "Live Match")

    embed = discord.Embed(title=f"🏏 {title}", color=0x00BFFF)

    teams = match.get("teams", [])

    if not teams:
        embed.description = "Score data not available yet."
        return embed

    for t in teams[:2]:
        team_name = t.get("team", {}).get("displayName", "Team")
        score = t.get("score") or "Yet to bat"

        embed.add_field(name=team_name, value=f"**{score}**", inline=False)

    embed.add_field(
        name="Status",
        value=status.get("type", {}).get("detail", "Live"),
        inline=False
    )

    embed.set_footer(text="Updates every 30s • ESPN feed")
    return embed

class MatchSelect(discord.ui.Select):
    def __init__(self, matches):
        self.map = {m["id"]: m["name"] for m in matches}

        options = [
            discord.SelectOption(label=m["name"][:100], value=m["id"])
            for m in matches[:25]
        ]

        super().__init__(placeholder="Choose a live match...", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            match_id = self.values[0]
            match_name = self.map[match_id]

            thread = await interaction.channel.create_thread(
                name=f"🏏 {match_name[:70]}",
                type=discord.ChannelType.public_thread
            )

            data = get_match(match_id)

            msg = await thread.send(embed=build_embed(data))

            active[msg.id] = {
                "match_id": match_id,
                "channel_id": thread.id
            }

            await interaction.response.send_message(
                f"📡 Started in {thread.mention}",
                ephemeral=True
            )

        except Exception as e:
            print("Callback error:", e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error: {e}",
                    ephemeral=True
                )

class MatchView(discord.ui.View):
    def __init__(self, matches):
        super().__init__(timeout=60)
        self.add_item(MatchSelect(matches))

@tree.command(name="livesb", description="Choose a live cricket match")
async def livesb(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)

        matches = get_live_matches()

        if not matches:
            await interaction.followup.send("❌ No live matches found.")
            return

        await interaction.followup.send(
            "Select a live match:",
            view=MatchView(matches)
        )

    except Exception as e:
        print("Command error:", e)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

@tasks.loop(seconds=30)
async def updater():
    for msg_id, info in list(active.items()):
        channel = client.get_channel(info["channel_id"])

        if channel is None:
            continue

        try:
            msg = await channel.fetch_message(msg_id)
            data = get_match(info["match_id"])
            await msg.edit(embed=build_embed(data))
        except Exception as e:
            print("Update error:", e)

@client.event
async def on_ready():
    await tree.sync()
    updater.start()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
