import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Variable
bracketId = ''

# Setup permissions
intents = discord.Intents.default()
intents.message_content = True # Read commands

# Define the command prefix
bot = commands.Bot(command_prefix='c!', intents=intents)

# Command: /bracket
@bot.tree.command(name="bracket", description="Choose which bracket to draw from")
@app_commands.describe(id="ID of the bracket")
async def greet(interaction: discord.Interaction, id: str):
    global bracketId
    bracketId = id
    await interaction.response.send_message(f"Requesting bracket from https://challonge.com/{bracketId}.svg")

# Command: c!update -> Update discord slash commands
@bot.command()
async def update(ctx):
    print("[c!update] Updating commands...")
    bot.tree.copy_global_to(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send("Slash commands updated!")

# Event: Runs when the bot successfully connects
@bot.event
async def on_ready():
    print(f'--------------------------------')
    print(f'Logged in as: {bot.user.name}') # type: ignore
    print(f'ID: {bot.user.id}') # type: ignore
    print(f'--------------------------------')


# Run the bot
if TOKEN:
    bot.run(TOKEN)
