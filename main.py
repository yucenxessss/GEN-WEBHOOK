import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import requests
import webbrowser

# ─── Webserver ─────────────────────────────────────────────
from flask import Flask, render_template_string
from threading import Thread

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bot Status</title>
    <style>
        body {
            background-color: #1e1e2f;
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            text-align: center;
            margin-top: 100px;
        }
        h1 {
            font-size: 48px;
            color: #ff4b5c;
        }
        p {
            font-size: 24px;
            color: #c4c4c4;
        }
    </style>
</head>
<body>
    <h1>✅ Bot is Online!</h1>
    <p>Everything is working perfectly.</p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ─── Discord Bot ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# ─── Roblox Play Command ─────────────────────────────────────
@bot.tree.command(name="play", description="Auto launch a Roblox game using cookie and game ID")
@app_commands.describe(cookie="Your .ROBLOSECURITY cookie", game_id="The Roblox game ID to launch")
async def play(interaction: discord.Interaction, cookie: str, game_id: str):
    await interaction.response.defer(thinking=True, ephemeral=True)

    try:
        session = requests.Session()
        session.cookies.set(".ROBLOSECURITY", cookie, domain=".roblox.com")
        session.headers.update({
            "User-Agent": "Roblox/WinInet",
            "Referer": "https://www.roblox.com/"
        })

        # Get Auth Ticket
        auth_res = session.post(
            "https://auth.roblox.com/v1/authentication-ticket",
            headers={
                "Accept": "application/json",
                "RBX-Request-Identifier": "GetAuthenticationTicket"
            }
        )

        if auth_res.status_code != 200:
            await interaction.followup.send(f"❌ Failed to get authentication ticket: {auth_res.text}", ephemeral=True)
            return

        auth_ticket = auth_res.headers.get("rbx-authentication-ticket")
        if not auth_ticket:
            await interaction.followup.send("❌ Authentication ticket not found.", ephemeral=True)
            return

        # Launch Roblox
        url = (
            f"roblox-player:1+launchmode:play+gameinfo:{auth_ticket}"
            f"+placelauncherurl:https://assetgame.roblox.com/game/PlaceLauncher.ashx"
            f"?request=RequestGame&placeId={game_id}+browserTrackerId:0"
            f"+robloxLocale:en_us+gameLocale:en_us"
        )

        webbrowser.open(url)

        await interaction.followup.send("✅ Roblox game launching...", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Failed to launch: {e}", ephemeral=True)

# ─── Webhook Gen Command ─────────────────────────────────────────
@bot.tree.command(name="gen_webhooks", description="Regenerate server with channels and webhooks inside a red embed.")
async def gen_webhooks(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("❌ This command can only be used inside a server.", ephemeral=True)
        return

    # Move channels out of categories
    for channel in guild.channels:
        try:
            if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel):
                await channel.edit(category=None)
        except Exception as e:
            print(f"❗ Error moving channel {channel.name}: {e}")

    # Delete all channels
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"❗ Error deleting channel {channel.name}: {e}")

    # Delete all categories
    for category in guild.categories:
        try:
            await category.delete()
        except Exception as e:
            print(f"❗ Error deleting category {category.name}: {e}")

    await asyncio.sleep(3)

    structure = {
        ".": ["〔🕸️〕saved webhook", "〔🌐〕site"],
        ".2": ["〔🚪〕visit"],
        ".3": ["〔🔓〕nbc", "〔🔓〕premium", "〔🔐〕v-nbc", "〔🔐〕v-premium"],
        ".4": ["〔📈〕success", "〔📉〕failed"],
        ".5": ["〔📜〕acc-with-group", "〔📜〕acc-for-spam"]
    }

    created_channels = {}
    saved_webhook_channel = None

    for category_name, channels in structure.items():
        category = await guild.create_category(category_name)
        for chan_name in channels:
            channel = await guild.create_text_channel(chan_name, category=category)
            created_channels[chan_name] = channel
            if chan_name == "〔🕸️〕saved webhook":
                saved_webhook_channel = channel

    if not saved_webhook_channel:
        await interaction.followup.send("❌ Failed to create the saved webhook channel.", ephemeral=True)
        return

    webhook_embed = discord.Embed(
        title="🕸️ Saved Webhooks",
        description="Here are your generated webhooks.",
        color=discord.Color.red()
    )

    for chan_name, channel in created_channels.items():
        if channel.id == saved_webhook_channel.id:
            continue
        try:
            webhook = await channel.create_webhook(name=f"Webhook - {chan_name}")
            webhook_embed.add_field(name=f"#{chan_name}", value=webhook.url, inline=False)
        except Exception as e:
            print(f"❗ Failed to create webhook in {chan_name}: {e}")

    webhook_embed.set_image(
        url="https://fiverr-res.cloudinary.com/images/f_auto,q_auto,t_main1/v1/attachments/delivery/asset/aa0d9d6c8813f5f65a00b2968ce75272-1668785195/Comp_1/do-a-cool-custom-animated-discord-profile-picture-or-banner-50-clients.gif"
    )

    await saved_webhook_channel.send(embed=webhook_embed)
    await interaction.followup.send("✅ Server reset and webhooks generated successfully!", ephemeral=True)

# ─── Start everything ─────────────────────────────────────────────────
keep_alive()  # start webserver
bot.run(os.getenv("TOKEN"))  # run bot
