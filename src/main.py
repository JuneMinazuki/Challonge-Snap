import os
import io
from typing import Any

import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

from json_handler import load_json, save_json
from bracket_drawer import get_latest_bracket

# Load the token from the .env file
load_dotenv()
DISCORD_BOT_TOKEN: str | None = os.getenv('DISCORD_BOT_TOKEN')

class TournamentCog(commands.Cog):
    def __init__(self, bot: "DiscordBot"):
        self.bot = bot

    # Slash Command: /bracket
    @app_commands.command(name="bracket", description="Choose which bracket to draw from")
    @app_commands.describe(id="ID of the bracket")
    async def bracket(self, interaction: discord.Interaction, id: str):
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

        # Start the loop
        if self.bot.refresh_bracket_loop.is_running():
            self.bot.refresh_bracket_loop.restart()
        else:
            self.bot.refresh_bracket_loop.start()

        await interaction.response.send_message(f"Now tracking: https://challonge.com/{id}.svg")

    # Slash Command: /info
    @app_commands.command(name="info", description="Get tracking info")
    async def info(self, interaction: discord.Interaction):
        if self.bot.bracket_id:
            await interaction.response.send_message(f"Currently tracking: https://challonge.com/{self.bot.bracket_id}.svg")
        else:
            await interaction.response.send_message("No bracket is currently being tracked. Use `/bracket` to set one.")

    # Prefix Command: c!update -> Update discord slash commands
    @commands.command(name="update")
    async def update(self, ctx: commands.Context):
        print("[c!update] Syncing slash commands...")
        # Since 'tree' belongs to the bot, we use self.bot.tree
        await self.bot.tree.sync() 
        await ctx.send("Slash commands updated!")

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

        if not self.is_complete:
            print(f"[System] Starting bracket loop for {self.bracket_id}...")
            self.refresh_bracket_loop.start()
    
    async def update_and_send_bracket(self, channel: discord.abc.Messageable) -> None:
        """Logic to fetch SVG, convert, and send to Discord"""
        if not self.bracket_id:
            return

        try:
            image_bytes, is_complete = await get_latest_bracket(self.bracket_id)

            if is_complete:
                print(f"[Challonge Snap] Tournament {self.bracket_id} finished.")

                # Update internal state
                self.is_complete = True
                self.bracket_id = None
                self.last_channel_id = None
                
                # Update and save JSON
                self.user_data.update({
                    "bracket_id": self.bracket_id ,
                    "last_channel_id": self.last_channel_id,
                    "is_complete": self.is_complete
                })
                save_json(self.user_data)

                self.refresh_bracket_loop.stop()
                return
            
            if image_bytes:
                with io.BytesIO(image_bytes) as image_binary:
                    file = discord.File(fp=image_binary, filename="bracket.png")
                    last_msg: discord.Message | None = None

                    if self.msg_id:
                        try:
                            last_msg = await channel.fetch_message(self.msg_id)
                        except discord.NotFound:
                            last_msg = None # Message was deleted, send new message

                    if last_msg:
                        await last_msg.edit(attachments=[file]) # Edit existing message with the new image
                    else:
                        # Send new message and save message ID
                        new_msg = await channel.send(file=file)
                        self.msg_id = new_msg.id

                        # Update json
                        self.user_data["last_message_id"] = self.msg_id
                        save_json(self.user_data)
            else:
                print(f"[Challonge Snap] No updates for {self.bracket_id}")
        except Exception as e:
            print(f"[Error] Failed to update bracket: {e}")

    async def on_ready(self) -> None:
        """Event: Runs when the bot successfully connects"""
        print(f'--------------------------------')
        print(f'Logged in as: {bot.user.name}') # type: ignore
        print(f'ID: {bot.user.id}') # type: ignore
        print(f'--------------------------------')

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
                print(f"[Error] Channel {self.last_channel_id} no longer exists.")
                self.refresh_bracket_loop.stop()
                return

        if isinstance(channel, discord.abc.Messageable):
            print(f"[Challonge Snap] Auto-refreshing bracket: {self.bracket_id}")
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
    bot.run(DISCORD_BOT_TOKEN)
