import os
import requests
import discord
from discord import app_commands
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
SPORTSMONKS = os.getenv("SPORTSMONKS_TOKEN")
GUILD_ID = 1521111741193523432

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.active = {}

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.clear_commands(guild=guild)
        self.tree.add_command(livesb, guild=guild)
        await self.tree.sync(guild=guild)
        self.updater.start()
        print("Guild commands synced")

bot = Bot()

BASE = "https://api.sportmonks.com/v3/cricket"

def get_live_matches():
    url = f"{BASE}/fixtures/live?api_token={SPORTSMONKS}"
    data = requests.get(url, timeout=20).json()

    matches = []

    for m in data.get("data", []):
        name = m.get("name")
        match_id = m.get("id")

        if name and match_id:
            matches.append({
                "id": str(match_id),
                "name": name
            })

    return matches

def get_match(match_id):
    url = f"{BASE}/fixtures/{match_id}?api_token={SPORTSMONKS}&include=runs,scoreboards,participants"
    return requests.get(url, timeout=20).json().get("data", {})

def build_embed(data):
    embed = discord.Embed(
        title=f"🏏 {data.get('name', 'Live Match')}",
        color=0x00BFFF
    )

    runs = data.get("runs", [])

    if runs:
        for r in runs[:2]:
            team = r.get("team", {}).get("name", "Team")
            score = f"{r.get('score',0)}/{r.get('wickets',0)} ({r.get('overs',0)})"
            embed.add_field(name=team, value=f"**{score}**", inline=False)
    else:
        embed.description = "Score not available yet."

    embed.add_field(
        name="Status",
        value=data.get("status", "Live"),
        inline=False
    )

    embed.set_footer(text="Updates every 30 seconds • SportsMonks")
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
        match_id = self.values[0]
        match_name = self.map[match_id]

        thread = await interaction.channel.create_thread(
            name=f"🏏 {match_name[:70]}",
            type=discord.ChannelType.public_thread
        )

        data = get_match(match_id)

        msg = await thread.send(embed=build_embed(data))

        bot.active[msg.id] = {
            "match_id": match_id,
            "channel_id": thread.id
        }

        await interaction.response.send_message(
            f"📡 Live scoreboard started in {thread.mention}",
            ephemeral=True
        )

class MatchView(discord.ui.View):
    def __init__(self, matches):
        super().__init__(timeout=60)
        self.add_item(MatchSelect(matches))

@app_commands.command(name="livesb", description="Choose a live cricket match")
async def livesb(interaction: discord.Interaction):
    matches = get_live_matches()

    if not matches:
        await interaction.response.send_message(
            "❌ No live matches found.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Select a live match:",
        view=MatchView(matches),
        ephemeral=True
    )

@tasks.loop(seconds=30)
async def updater():
    for msg_id, info in list(bot.active.items()):
        channel = bot.get_channel(info["channel_id"])

        if channel is None:
            continue

        try:
            msg = await channel.fetch_message(msg_id)
            data = get_match(info["match_id"])
            await msg.edit(embed=build_embed(data))
        except Exception as e:
            print("Update error:", e)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
