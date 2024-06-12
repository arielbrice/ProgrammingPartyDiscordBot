# bot.py
import os

import discord
from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('TEST_TOKEN')


client = discord.Client(intents=discord.Intents.default())

TEST_GUILD = discord.Object(os.getenv('TEST_GUILD'))
MAIN_GUILD = discord.Object(os.getenv('5S_GUILD'))
MY_GUILD = MAIN_GUILD
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
    


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


client.run(TOKEN)