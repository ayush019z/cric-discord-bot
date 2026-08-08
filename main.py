import os
import discord
from discord import app_commands
from discord.ext import tasks
from pycricbuzz import Cricbuzz

TOKEN = os.getenv("DISCORD_TOKEN") or "PASTE_YOUR_BOT_TOKEN"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

cb = Cricbuzz()

# msg_id -> data
active = {}
last_status = {}


def get_live_matches():
    matches = cb.matches()
    live = []

    for m in matches:
        status = (m.get("status") or "").lower()

        if any(x in status for x in ["live", "innings", "need", "won", "trail"]):
            live.append({
                "id": m["id"],
                "name": f"{m['team1']['name']} vs {m['team2']['name']}"
            })

    return live


def balls_to_emojis(text: str):
    mapping = {
        "0": "⚪",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣",
        "W": "❌",
    }
    out = []
    for part in text.split():
        out.append(mapping.get(part, part))
    return " ".join(out)


def build_embed(match_id: str):
    info = cb.livescore(match_id)

    t1 = info["team1"]["name"]
    t2 = info["team2"]["name"]

    embed = discord.Embed(
        title=f"🏏 {t1} vs {t2}",
        color=0x00BFFF
    )

    scores = info.get("score", [])

    if len(scores) >= 1:
        s = scores[0]
        embed.add_field(
            name=f"🇦 {t1}",
            value=f"**{s.get('runs',0)}/{s.get('wickets',0)} ({s.get('overs',0)})**",
            inline=False
        )

    if len(scores) >= 2:
        s = scores[1]
        embed.add_field(
            name=f"🇧 {t2}",
            value=f"**{s.get('runs',0)}/{s.get('wickets',0)} ({s.get('overs',0)})**",
            inline=False
        )

    status = info.get("status", "Live")

    # last over if available
    commentary = info.get("commentary", {})
    last_over = commentary.get("last_over")

    if last_over:
        embed.add_field(
            name="🎯 Last over",
            value=balls_to_emojis(last_over),
            inline=False
        )

    batsmen = commentary.get("batsmen", [])
    if batsmen:
        text = []
        for b in batsmen[:2]:
            text.append(f"**{b['name']}** {b['runs']} ({b['balls']})")
        embed.add_field(
            name="🏏 Batters",
            value="\n".join(text),
            inline=False
        )

    bowler = commentary.get("bowler")
    if bowler:
        embed.add_field(
            name="🎳 Bowler",
            value=f"**{bowler['name']}**  {bowler['overs']}-{bowler['maidens']}-{bowler['runs']}-{bowler['wickets']}",
            inline=False
        )

    rr = commentary.get("required_rate")
    target = commentary.get("target")

    if rr or target:
        txt = []
        if target:
            txt.append(f"🎯 **Target:** {target}")
        if rr:
            txt.append(f"📈 **Req RR:** {rr}")
        embed.add_field(
            name="📊 Chase",
            value="\n".join(txt),
            inline=False
        )

    embed.add_field(
        name="📢 Status",
        value=status,
        inline=False
    )

    if "won" in status.lower():
        embed.color = 0x2ECC71
    elif "need" in status.lower():
        embed.color = 0xE67E22

    embed.set_footer(text="Unofficial Cricbuzz • Updates every 30s")

    return embed, status


class StopView(discord.ui.View):
    def __init__(self, msg_id):
        super().__init__(timeout=None)
        self.msg_id = msg_id

    @discord.ui.button(label="Stop Updates", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        active.pop(self.msg_id, None)
        last_status.pop(self.msg_id, None)

        button.disabled = True
        await interaction.response.edit_message(view=self)

        await interaction.followup.send("⏹️ Live updates stopped.", ephemeral=True)


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

        embed, status = build_embed(match_id)

        msg = await thread.send(embed=embed)

        active[msg.id] = {
            "match_id": match_id,
            "channel_id": thread.id
        }

        last_status[msg.id] = status

        await msg.edit(view=StopView(msg.id))

        await interaction.response.send_message(
            f"📡 Live scoreboard started in {thread.mention}",
            ephemeral=True
        )


class MatchView(discord.ui.View):
    def __init__(self, matches):
        super().__init__(timeout=60)
        self.add_item(MatchSelect(matches))


@tree.command(name="livesb", description="Choose a live Cricbuzz match")
async def livesb(interaction: discord.Interaction):

    matches = get_live_matches()

    if not matches:
        await interaction.response.send_message(
            "❌ No live matches found right now.",
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

            embed, status = build_embed(data["match_id"])

            old = last_status.get(msg_id, "")

            if status != old:
                if "four" in status.lower():
                    await channel.send("🟦 **FOUR!**")
                elif "six" in status.lower():
                    await channel.send("🟪 **SIX!**")
                elif "out" in status.lower() or "wicket" in status.lower():
                    await channel.send("❌ **WICKET!**")
                elif "won" in status.lower():
                    await channel.send(f"🏆 **{status}**")

                last_status[msg_id] = status

            await msg.edit(embed=embed, view=StopView(msg_id))

            if "won" in status.lower():
                active.pop(msg_id, None)

        except Exception as e:
            print("Update failed:", e)


@client.event
async def on_ready():
    await tree.sync()
    updater.start()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
