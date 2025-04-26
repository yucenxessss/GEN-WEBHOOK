import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

# ─── Setup ─────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Events ────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# ─── Slash Command ─────────────────────────────────────────────────
@bot.tree.command(name="gen_webhooks", description="Regenerate server with channels and webhooks inside a red embed.")
async def gen_webhooks(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("❌ This command can only be used inside a server.", ephemeral=True)
        return

    # ─── Step 1: Move channels out of categories ───
    for channel in guild.channels:
        try:
            if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel):
                await channel.edit(category=None)
        except Exception as e:
            print(f"❗ Error moving channel {channel.name}: {e}")

    # ─── Step 2: Delete all channels ───
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"❗ Error deleting channel {channel.name}: {e}")

    # ─── Step 3: Delete all categories ───
    for category in guild.categories:
        try:
            await category.delete()
        except Exception as e:
            print(f"❗ Error deleting category {category.name}: {e}")

    # ─── Step 4: Wait to make sure Discord finishes ───
    await asyncio.sleep(3)

    # ─── Step 5: Define Structure ───
    structure = {
        ".": ["〔🕸️〕saved webhook", "〔🌐〕site"],
        ".2": ["〔🚪〕visit"],
        ".3": ["〔🔓〕nbc", "〔🔓〕premium", "〔🔐〕v-nbc", "〔🔐〕v-premium"],
        ".4": ["〔📈〕success", "〔📉〕failed"],
        ".5": ["〔📜〕acc-with-group", "〔📜〕acc-for-spam"]
    }

    created_channels = {}
    saved_webhook_channel = None

    # ─── Step 6: Create new categories and channels ───
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

    # ─── Step 7: Create Webhooks and Build Embed ───
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

    # ─── Step 8: Send the embed ───
    await saved_webhook_channel.send(embed=webhook_embed)

    # ─── Step 9: Final follow-up ───
    await interaction.followup.send("✅ Server reset and webhooks generated successfully!", ephemeral=True)

# ─── Run the Bot ─────────────────────────────────────────────────
bot.run(os.getenv("TOKEN"))
