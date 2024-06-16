# bot.py
import os

import discord
from dotenv import load_dotenv
from discord import app_commands ##command tree function and allows discord commands to rec command

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


MY_GUILD = discord.Object(os.getenv('5S_GUILD')) ## convert to discord token

class MyClient(discord.Client):
    ##constructor
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents = intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')



##feel like an event needs to be here or method
##start a command with a tree
##function async def 

@client.tree.command() ##slash command
async def reply(interaction: discord.Interaction, hobby: str):
    print("Hello, there") ## have to use a send message instead to console
    await interaction.response.send_message(f'How is it going {interaction.user.mention}. Thats a cool hobby TFTI: your hobby is {hobby}') ##await interaction sends to discord w/e inside {} is value sent 



##discord calls a slash a command a tree command

client.run(TOKEN) ##this always goes at bottom of code