import os
import io
from datetime import datetime
from typing import Any
import logging

import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import colorlog

from json_handler import load_json, save_json
from bracket_drawer import get_latest_bracket

# Create logs folder
if not os.path.exists('logs'):
    os.makedirs('logs')

# Setup color formater
color_formatter = colorlog.ColoredFormatter(
    fmt='%(black)s%(asctime)s %(log_color)s%(levelname)-8s %(reset)s%(blue)s%(name)-15s %(reset)s%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Setup stream handler
stream_handler = colorlog.StreamHandler()
stream_handler.setFormatter(color_formatter)

# Setup file handler
file_handler = logging.FileHandler(filename='logs/challonge-snap.log', encoding='utf-8', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)-15s %(message)s'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[stream_handler, file_handler]
)
logger = logging.getLogger('challonge-snap')

# Load the token from the .env file
load_dotenv()
DISCORD_BOT_TOKEN: str | None = os.getenv('DISCORD_BOT_TOKEN')
CHALLONGE_API_KEY: str | None = os.getenv('CHALLONGE_API_KEY')

class TournamentCog(commands.Cog):
    def __init__(self, bot: "DiscordBot"):
        self.bot = bot

    # Slash Command: /bracket
    @app_commands.command(name="bracket", description="Choose which bracket to draw from")
    @app_commands.describe(id="ID of the bracket")
    async def bracket(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.channel or not isinstance(interaction.channel, discord.abc.Messageable):
            await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
            return

        # Update internal state
        self.bot.bracket_id = id
        self.bot.last_channel_id = interaction.channel_id
        self.bot.is_complete = False
        
        # Update and save JSON
        self.bot.user_data.update({
            "bracket_id": self.bot.bracket_id ,
            "last_channel_id": self.bot.last_channel_id,
            "is_complete": self.bot.is_complete
        })
        save_json(self.bot.user_data)

        try:
            await self.bot.update_and_send_bracket(interaction.channel)
            await interaction.followup.send(f"Now tracking: https://challonge.com/{id}", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Error tracking bracket: {e}", ephemeral=True)

        # Start the loop
        if self.bot.refresh_bracket_loop.is_running():
            self.bot.refresh_bracket_loop.restart()
        else:
            self.bot.refresh_bracket_loop.start()

    # Slash Command: /info
    @app_commands.command(name="info", description="Get tracking info")
    async def info(self, interaction: discord.Interaction):
        if self.bot.bracket_id:
            await interaction.response.send_message(f"Currently tracking: https://challonge.com/{self.bot.bracket_id}.svg", ephemeral=True)
        else:
            await interaction.response.send_message("No bracket is currently being tracked. Use `/bracket` to set one.", ephemeral=True)

    # Slash Command: /update
    @app_commands.command(name="update", description="Update the bracket immediately")
    async def update(self, interaction: discord.Interaction):
        if not self.bot.bracket_id:
            await interaction.response.send_message("No bracket is currently being tracked.", ephemeral=True)
            return
        
        self.bot.refresh_bracket_loop.restart()
        await interaction.response.send_message("Bracket updated", ephemeral=True)

    # Slash Command: /clear
    @app_commands.command(name="clear", description="Clear bot data and stop tracking bracket")
    async def clear(self, interaction: discord.Interaction):
        logger.info("[/clear] Clearing data.json")

        # Stop the loop
        if self.bot.refresh_bracket_loop.is_running():
            self.bot.refresh_bracket_loop.cancel()
        
        # Update internal state
        self.bot.bracket_id = None
        self.bot.last_channel_id = None
        self.bot.is_complete = True
        self.bot.msg_id = None

        # Update and save JSON
        self.bot.user_data.update({
            "bracket_id": self.bot.bracket_id ,
            "last_channel_id": self.bot.last_channel_id,
            "is_complete": self.bot.is_complete,
            "last_message_id": self.bot.msg_id
        })
        save_json(self.bot.user_data)

        await interaction.response.send_message("Data clear!", ephemeral=True)

    # Prefix Command: c!sync -> Update discord slash commands
    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str | None = None):
        if ctx.guild is None:
            await ctx.send("This command must be used in a server.")
            return

        if spec == "guild":
            # Syncs commands only to the current server
            logger.info("[c!sync] Syncing slash commands")
            self.bot.tree.copy_global_to(guild = ctx.guild)
            synced = await self.bot.tree.sync(guild = ctx.guild)
            await ctx.send(f"Synced {len(synced)} commands to this server.")
            
        elif spec == "clear":
            # Clears all commands from server
            logger.info("[c!sync] Clearing slash commands")
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send("Guild commands cleared.")

        else:
            # Syncs commands globally 
            synced = await self.bot.tree.sync()
            await ctx.send(f"Synced {len(synced)} commands globally.")

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # Read commands
        
        # Define the command prefix
        super().__init__(command_prefix='c!', intents=intents)
        
        # Load initial state
        self.user_data: dict[str, Any] = load_json()
        self.bracket_id: str | None = self.user_data.get("bracket_id")
        self.last_channel_id: int | None = self.user_data.get("last_channel_id")
        self.is_complete: bool = self.user_data.get("is_complete", True)
        self.msg_id: int | None = self.user_data.get("last_message_id")

    async def setup_hook(self) -> None:
        """Start the 10-minute background loop"""
        await self.add_cog(TournamentCog(self))

        if (not self.is_complete) and (CHALLONGE_API_KEY):
            logger.info(f"Starting bracket loop for {self.bracket_id}")
            self.refresh_bracket_loop.start()
    
    async def update_and_send_bracket(self, channel: discord.abc.Messageable) -> None:
        """Logic to fetch SVG, convert, and send to Discord"""
        if not self.bracket_id:
            return

        try:
            image_bytes, is_complete = await get_latest_bracket(self.bracket_id)
            
            if image_bytes:
                # Get current time 
                current_time: str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                current_time_text: str = f"-# Last update: {current_time}"

                with io.BytesIO(image_bytes) as image_binary:
                    file = discord.File(fp=image_binary, filename="bracket.png")
                    last_msg: discord.Message | None = None

                    if self.msg_id:
                        try:
                            last_msg = await channel.fetch_message(self.msg_id)
                        except discord.NotFound:
                            last_msg = None # Message was deleted, send new message

                    if last_msg:
                        await last_msg.edit(content=current_time_text, attachments=[file]) # Edit existing message with the new image
                    else:
                        # Send new message and save message ID
                        new_msg = await channel.send(content=current_time_text, file=file)
                        self.msg_id = new_msg.id

                        # Update json
                        self.user_data["last_message_id"] = self.msg_id
                        save_json(self.user_data)
            else:
                logger.info(f"No updates for {self.bracket_id}")

            if is_complete:
                logger.info(f"Tournament {self.bracket_id} finished")

                # Update internal state
                self.is_complete = True
                self.bracket_id = None
                self.last_channel_id = None
                self.msg_id = None
                
                # Update and save JSON
                self.user_data.update({
                    "bracket_id": self.bracket_id ,
                    "last_channel_id": self.last_channel_id,
                    "is_complete": self.is_complete,
                    "last_message_id": self.msg_id
                })
                save_json(self.user_data)

                self.refresh_bracket_loop.stop()
                return
            
        except Exception as e:
            logger.error(f"Failed to update bracket: {e}")

    async def on_ready(self) -> None:
        """Event: Runs when the bot successfully connects"""
        logger.info(f"{bot.user.name} (ID: {bot.user.id}) successfully connects") # type: ignore

    @tasks.loop(minutes=15)
    async def refresh_bracket_loop(self) -> None:
        """Refresh the bracket every 10 minutes"""
        # Check if there is a bracket id and channel id
        if not (self.bracket_id and self.last_channel_id):
            return
        
        channel = self.get_channel(self.last_channel_id)
        if not channel:
            try:
                channel = await self.fetch_channel(self.last_channel_id)
            except discord.NotFound:
                logger.warning(f"Channel {self.last_channel_id} no longer exists")
                self.refresh_bracket_loop.stop()
                return

        if isinstance(channel, discord.abc.Messageable):
            logger.info(f"Auto-refreshing bracket: {self.bracket_id}")
            await self.update_and_send_bracket(channel)

    @refresh_bracket_loop.before_loop
    async def before_refresh_loop(self) -> None:
        await self.wait_until_ready()

    async def close(self) -> None:
        self.refresh_bracket_loop.stop()
        await super().close()

# Initialize bot
bot = DiscordBot()

# Run the bot
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN, log_handler=None)
