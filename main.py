import os
import requests
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
SPORTSMONKS = os.getenv("SPORTSMONKS_TOKEN")
GUILD_ID = 1521111741193523432

BASE = "https://api.sportmonks.com/v3/cricket"

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
    url = (
        f"{BASE}/fixtures?api_token={SPORTSMONKS}"
        "&filter[status]=LIVE,IN_PROGRESS,1ST_INNINGS,2ND_INNINGS,3RD_INNINGS,4TH_INNINGS"
        "&include=participants"
    )

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
    url = (
        f"{BASE}/fixtures/{match_id}?api_token={SPORTSMONKS}"
        "&include=runs,participants"
    )

    data = requests.get(url, timeout=20).json()

    return data.get("data", {})

def build_embed(data):
    embed = discord.Embed(
        title=f"🏏 {data.get('name', 'Live Match')}",
        color=0x00BFFF
    )

    runs = data.get("runs", [])

    if runs:
        for r in runs[:2]:
            team = r.get("team", {}).get("name", "Team")

            score = (
                f"{r.get('score', 0)}/"
                f"{r.get('wickets', 0)} "
                f"({r.get('overs', 0)})"
            )

            embed.add_field(
                name=team,
                value=f"**{score}**",
                inline=False
            )
    else:
        embed.description = "Score not available yet."

    embed.add_field(
        name="Status",
        value=str(data.get("status", "In Progress")),
        inline=False
    )

    embed.set_footer(text="SportsMonks • Ongoing cricket matches")

    return embed

class MatchSelect(discord.ui.Select):
    def __init__(self, matches):
        self.map = {m["id"]: m["name"] for m in matches}

        options = [
            discord.SelectOption(
                label=m["name"][:100],
                value=m["id"]
            )
            for m in matches[:25]
        ]

        super().__init__(
            placeholder="Choose an ongoing match...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        match_id = self.values[0]
        match_name = self.map[match_id]

        thread = await interaction.channel.create_thread(
            name=f"🏏 {match_name[:70]}",
            type=discord.ChannelType.public_thread
        )

        data = get_match(match_id)

        await thread.send(embed=build_embed(data))

        await interaction.response.send_message(
            f"📡 Scoreboard posted in {thread.mention}",
            ephemeral=True
        )

class MatchView(discord.ui.View):
    def __init__(self, matches):
        super().__init__(timeout=60)
        self.add_item(MatchSelect(matches))

@app_commands.command(
    name="livesb",
    description="Choose an ongoing cricket match"
)
async def livesb(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Token starts with: {SPORTSMONKS[:5] if SPORTSMONKS else 'NONE'}",
        ephemeral=True
    )

    except Exception as e:
        await interaction.response.send_message(
            f"Error: {e}",
            ephemeral=True
        )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
