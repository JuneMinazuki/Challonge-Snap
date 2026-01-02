import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Setup permissions
intents = discord.Intents.default()
intents.message_content = True # Read commands

# Define the command prefix
bot = commands.Bot(command_prefix='c!', intents=intents)

# Command: /hello
@bot.tree.command(name="hello", description="Test command")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}! This is a slash command.")

# Command: c!update -> Update discord slash commands
@bot.command()
async def update(ctx):
    print("Updating commands...")
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
