import os
import requests
import discord
from discord import app_commands
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

active = {}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}


def get_live_matches():
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"

    r = requests.get(url, headers=HEADERS, timeout=15)
    data = r.json()

    print("API RESPONSE:", data)

    matches = []

    for type_match in data.get("typeMatches", []):
        for series_match in type_match.get("seriesMatches", []):

            wrapper = series_match.get("seriesAdWrapper")
            if not wrapper:
                continue

            for match in wrapper.get("matches", []):
                info = match.get("matchInfo", {})

                team1 = info.get("team1", {}).get("teamName")
                team2 = info.get("team2", {}).get("teamName")
                match_id = info.get("matchId")

                if team1 and team2 and match_id:
                    matches.append({
                        "id": str(match_id),
                        "name": f"{team1} vs {team2}"
                    })

    print("FOUND MATCHES:", matches)
    return matches


def get_score(match_id):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}"

    r = requests.get(url, headers=HEADERS, timeout=15)
    return r.json()


def build_embed(data):
    info = data.get("matchInfo", {})
    scorecard = data.get("scoreCard", [])

    t1 = info.get("team1", {}).get("teamName", "Team 1")
    t2 = info.get("team2", {}).get("teamName", "Team 2")

    embed = discord.Embed(
        title=f"🏏 {t1} vs {t2}",
        color=0x00BFFF
    )

    if scorecard:
        for innings in scorecard[:2]:
            team = innings.get("batTeamDetails", {}).get("batTeamName", "Team")
            score = innings.get("scoreDetails", {})

            runs = score.get("runs", 0)
            wickets = score.get("wickets", 0)
            overs = score.get("overs", 0)

            embed.add_field(
                name=team,
                value=f"**{runs}/{wickets} ({overs})**",
                inline=False
            )

    embed.add_field(
        name="Status",
        value=info.get("status", "Live"),
        inline=False
    )

    embed.set_footer(text="Unofficial Cricbuzz via RapidAPI • Updates every 30s")
    return embed


class MatchSelect(discord.ui.Select):
    def __init__(self, matches):
        self.match_map = {m["id"]: m["name"] for m in matches}

        options = [
            discord.SelectOption(
                label=m["name"][:100],
                value=m["id"]
            )
            for m in matches[:25]
        ]

        super().__init__(
            placeholder="Choose a live match...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        match_id = self.values[0]
        match_name = self.match_map[match_id]

        thread = await interaction.channel.create_thread(
            name=f"🏏 {match_name[:70]}",
            type=discord.ChannelType.public_thread
        )

        data = get_score(match_id)

        msg = await thread.send(embed=build_embed(data))

        active[msg.id] = {
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


@tree.command(name="livesb", description="Choose a live cricket match")
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
    for msg_id, data in list(active.items()):

        channel = client.get_channel(data["channel_id"])

        if channel is None:
            continue

        try:
            msg = await channel.fetch_message(msg_id)

            score = get_score(data["match_id"])

            await msg.edit(embed=build_embed(score))

        except Exception as e:
            print("Update failed:", e)


@client.event
async def on_ready():
    await tree.sync()
    updater.start()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
