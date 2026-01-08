import os
from typing import Any

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from json_handler import load_json, save_json
from bracket_drawer import get_latest_bracket

# Load the token from the .env file
load_dotenv()
DISCORD_BOT_TOKEN: str | None = os.getenv('DISCORD_BOT_TOKEN')

# Get bracketId
user_data: dict[str, Any] = load_json()
bracket_id: str | None = user_data.get("bracket_id")

# Setup permissions
intents: discord.Intents = discord.Intents.default()
intents.message_content = True # Read commands

# Define the command prefix
bot: commands.Bot = commands.Bot(command_prefix='c!', intents=intents)

@bot.tree.command(name="bracket", description="Choose which bracket to draw from")
@app_commands.describe(id="ID of the bracket")
async def bracket(interaction: discord.Interaction, id: str) -> None:
    """Command: /bracket -> Update the current bracket ID and save to JSON."""
    global bracket_id
    bracket_id = id
    user_data["bracket_id"] = id
    save_json(user_data)

    await interaction.response.send_message(f"Requesting bracket from https://challonge.com/{bracket_id}.svg")

@bot.tree.command(name="info", description="Display the bracket ID currently in use.")
async def info(interaction: discord.Interaction) -> None:
    """Command: /info -> Display the URL of the bracket currently in use."""
    await interaction.response.send_message(f"Currently requesting bracket from https://challonge.com/{bracket_id}.svg")

@bot.command()
async def update(ctx: commands.Context) -> None:
    """Command: c!update -> Update discord slash commands"""
    if ctx.guild is None:
        await ctx.send("This command must be used within a server.")
        return
    
    print("[c!update] Updating commands...")
    bot.tree.copy_global_to(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)

    await ctx.send("Slash commands updated!")

@bot.event
async def on_ready() -> None:
    """Event: Runs when the bot successfully connects"""
    print(f'--------------------------------')
    print(f'Logged in as: {bot.user.name}') # type: ignore
    print(f'ID: {bot.user.id}') # type: ignore
    print(f'--------------------------------')

# Run the bot
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
