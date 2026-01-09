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

    async def setup_hook(self) -> None:
        """Start the 10-minute background loop"""
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
                    "bracket_id": None,
                    "last_channel_id": None,
                    "is_complete": True
                })
                save_json(self.user_data)

                self.refresh_bracket_loop.stop()
                return
            
            if image_bytes:
                with io.BytesIO(image_bytes) as image_binary:
                    file = discord.File(fp=image_binary, filename="bracket.png")
                    await channel.send(file=file)
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

    @tasks.loop(minutes=10)
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

# Slash Command: /bracket
@bot.tree.command(name="bracket", description="Choose which bracket to draw from")
@app_commands.describe(id="ID of the bracket")
async def bracket(interaction: discord.Interaction, id: str):
    client: DiscordBot = interaction.client # type: ignore

    # Update internal state
    client.bracket_id = id
    client.last_channel_id = interaction.channel_id
    
    # Update and save JSON
    client.user_data["bracket_id"] = id
    client.user_data["last_channel_id"] = interaction.channel_id
    save_json(client.user_data)

    await interaction.response.send_message(f"Now tracking: https://challonge.com/{id}.svg")

# Slash Command: /info
@bot.tree.command(name="info", description="Get current bracket that the bot is drawing from")
async def info(interaction: discord.Interaction):
    client: DiscordBot = interaction.client # type: ignore

    if client.bracket_id:
        await interaction.response.send_message(f"Currently tracking: https://challonge.com/{client.bracket_id}.svg")
    else:
        await interaction.response.send_message("No bracket is currently being tracked. Use `/bracket` to set one.")

# Prefix Command: c!update -> Update discord slash commands
@bot.command()
async def update(ctx: commands.Context):
    print("[c!update] Updating commands...")

    await bot.tree.sync()
    await ctx.send("Slash commands updated!")

# Run the bot
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
