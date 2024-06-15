# Trading card discord bot

import datetime
import os
import random
from typing import Set

import discord
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

commandprefix = "!"

embed_msg_color_standard = 0x44a0ff
embed_msg_color_error = 0xff0000
embed_msg_color_success = 0x00ff00

# How often can the user claim in minutes
timely_claim_cooldown = 0.5

# Timely card claim weights
timely_claim_common_weight = 300
timely_claim_rare_weight = 40
timely_claim_epic_weight = 5
timely_claim_legendary_weight = 1


# Set up the database
def get_database():
    conn_string = os.getenv('MONGO_CONNECTION_STRING')
    client = None
    try:
        # This connects to the Database Server
        client = MongoClient(conn_string)
        print("Connected to database")
    except Exception as e:
        print("Error connecting to database: ", e)
    # This creates the database
    return client["trading_card_system"]


database = get_database()
if database is None:
    print("Error connecting to database")
    exit(1)


class Card:
    def __init__(self, card_id: int, name: str, rarity: str, description: str):
        self.card_id = card_id
        self.name = name
        self.rarity = rarity
        self.description = description


class User:
    def __init__(self, discord_id: int, registration_date: datetime, level: int, exp: int, balance: int,
                 cards: Set[Card]):
        self.discord_id = discord_id
        self.registration_date = registration_date
        self.level = level
        self.exp = exp
        self.balance = balance
        self.cards = cards


class UserStaff:
    def __init__(self, discord_id: int, access_type: str):
        # access_type can be "owner", "admin", or "moderator"
        # owner is similar to admin, but cannot be demoted
        self.discord_id = discord_id
        self.access_type = access_type


# User Collection stores a collection of users, their stats, and their inventories
user_collection = database["users"]

# Stores all the possible cards that could be obtained in the game
card_collection = database["cards"]

# Staff Collection stores a collection of staff members and their access levels
staff_collection = database["staff"]

# Initialize the user collection if it doesn't exist
# This is likely to be updated very frequently as new users join the game and their stats are updated
if user_collection.count_documents({}) == 0:
    user = {
        "discord_id": 0,
        "registration_date": datetime.datetime.now(),
        "claim_date": datetime.datetime.now(),
        "level": 1,
        "exp": 0,
        "balance": 0,
        "cards": [],
        "card_packs": []
    }
    user_collection.insert_one(user)
    print("User collection initialized")
# Initialize the card collection if it doesn't exist
# This is less likely to be updated frequently as it only needs to be updated when new cards are added

if card_collection.count_documents({}) == 0:
    # Loads up CSVs, converts them into dicts, 1st row is header.
    cardid = 0
    with open("cardslist_bootstrap_commons.csv", "r") as file:
        for line in file:
            card = line.split(",")
            card = {
                "card_id": cardid,
                "name": card[0],
                "type": card[1],
                "rarity": "common",
                "description": card[2]
            }
            card_collection.insert_one(card)
            cardid += 1
    with open("cardslist_bootstrap_rares.csv", "r") as file:
        for line in file:
            card = line.split(",")
            card = {
                "card_id": cardid,
                "name": card[0],
                "type": card[1],
                "rarity": "rare",
                "description": card[2]
            }
            card_collection.insert_one(card)
            cardid += 1
    with open("cardslist_bootstrap_epics.csv", "r") as file:
        for line in file:
            card = line.split(",")
            card = {
                "card_id": cardid,
                "name": card[0],
                "type": card[1],
                "rarity": "epic",
                "description": card[2]
            }
            card_collection.insert_one(card)
            cardid += 1
    with open("cardslist_bootstrap_legendaries.csv", "r") as file:
        for line in file:
            card = line.split(",")
            card = {
                "card_id": cardid,
                "name": card[0],
                "type": card[1],
                "rarity": "legendary",
                "description": card[2]
            }
            card_collection.insert_one(card)
            cardid += 1

    #cards = [
    #    {
    #        "card_id": 0,
    #        "name": "Card 1",
    #        "type": "Meta",
    #        "rarity": "common",
    #        "description": "This is a common card"
    #    }
    #]
    print("Card collection initialized")
if staff_collection.count_documents({}) == 0:
    staff = {
        "discord_id": 166001619735937024,
        "access_type": "owner"
    }
    staff_collection.insert_one(staff)
    print("Staff collection initialized")


### Basic Permission System
def checkperms(user_id: int, access_type: str):
    # Admin > Moderator > None
    useraccess = getperms(user_id)
    if useraccess == "None":
        return False
    if access_type == "owner":
        if useraccess == "owner":
            return True
        return False
    if access_type == "admin":
        if useraccess == "owner":
            return True
        if useraccess == "admin":
            return True
        return False
    if access_type == "moderator":
        if useraccess == "owner":
            return True
        if useraccess == "admin":
            return True
        if useraccess == "moderator":
            return True
        return False


def getperms(user_id: int):
    user = staff_collection.find_one({"discord_id": user_id})
    if user is not None:
        return user["access_type"]
    else:
        return "None"


def get_user(user_id: int):
    user = user_collection.find_one({"discord_id": user_id})
    if user is not None:
        return User(user["discord_id"], user["registration_date"], user["level"], user["exp"], user["balance"],
                    user["cards"])
    else:
        return None


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(commandprefix):
        command = message.content.split(" ")[0][1:]
        args = message.content.split(" ")[1:]

        if command == "pingme":
            embedmsg = discord.Embed(title="Pong!", description="You have been pinged", color=embed_msg_color_standard)
            await message.channel.send(embed=embedmsg)
            return
        if command == "help":
            await message.channel.send(embed=help(args[0] if len(args) > 0 else None))
            return
        if command == "checkperms":
            userperms = getperms(message.author.id)
            # If moderator, 1st arg can be used to check perms of another user, otherwise, it will check the perms of the user
            if not checkperms(message.author.id, "moderator") or len(args) == 0:
                embedmsg = discord.Embed(title="User Permissions", description=f'Your permissions: {userperms}',
                                         color=embed_msg_color_standard)
                await message.channel.send(embed=embedmsg)
                return
            # reformat the 1st arg to be an integer
            targetid = int(args[0].replace("<@", "").replace(">", ""))
            targetperms = getperms(targetid)
            embedmsg = discord.Embed(title="User Permissions",
                                     description=f'User permissions of {targetid}: {targetperms}',
                                     color=embed_msg_color_standard)
            await message.channel.send(embed=embedmsg)
            return
        if command == "register":
            user = get_user(message.author.id)
            if user is not None:
                embedmsg = discord.Embed(title="Error", description="You are already registered",
                                         color=embed_msg_color_error)
                await message.channel.send(embed=embedmsg)
                return
            user = {
                "discord_id": message.author.id,
                "registration_date": datetime.datetime.now(),
                "level": 1,
                "exp": 0,
                "balance": 0,
                "cards": [],
                "card_packs": []
            }
            user_collection.insert_one(user)
            embedmsg = discord.Embed(title="Success", description="You have been registered",
                                     color=embed_msg_color_success)
            await message.channel.send(embed=embedmsg)
        if command == "inventory":
            user = get_user(message.author.id)
            userperms = getperms(message.author.id)
            if not checkperms(message.author.id, "moderator") or len(args) == 0:
                if user is None:
                    embedmsg = discord.Embed(title="Error", description="You are not registered.\nUse !register to register",
                                             color=embed_msg_color_error)
                    await message.channel.send(embed=embedmsg)
                    return
                embedmsg = discord.Embed(title="Inventory", description="Your inventory",
                                         color=embed_msg_color_standard)
                for card in user.cards:
                    embedmsg.add_field(name=f"Card ID: {card['card_id']}",
                                       value=f"Name: {card['name']}\nRarity: {card['rarity']}\nDescription: {card['description']}",
                                       inline=False)
                await message.channel.send(embed=embedmsg)
                return
            # reformat the 1st arg to be an integer
            targetid = int(args[0].replace("<@", "").replace(">", ""))
            targetuser = get_user(targetid)
            if targetuser is None:
                embedmsg = discord.Embed(title="Error", description="User is not registered",
                                         color=embed_msg_color_error)
                await message.channel.send(embed=embedmsg)
                return
            embedmsg = discord.Embed(title="Inventory", description="User inventory",
                                     color=embed_msg_color_standard)
            for card in targetuser.cards:
                embedmsg.add_field(name=f"Card ID: {card['card_id']}",
                                   value=f"Name: {card['name']}\nRarity: {card['rarity']}\nDescription: {card['description']}",
                                   inline=False)
            await message.channel.send(embed=embedmsg)
            return
        if command == "claim":
            user = get_user(message.author.id)
            if user is None:
                embedmsg = discord.Embed(title="Error",
                                         description="You are not registered.\nUse !register to register",
                                         color=embed_msg_color_error)
                await message.channel.send(embed=embedmsg)
                return
            # Check if the user has already claimed their daily card
            if user["claim_date"] + datetime.timedelta(minutes=timely_claim_cooldown) > datetime.datetime.now():
                embedmsg = discord.Embed(title="Error", description="You have already claimed your daily card",
                                         color=embed_msg_color_error)
                await message.channel.send(embed=embedmsg)
                return
            # Claim the card
            # Generate a random number between 0 and the sum of all the weights
            # If the number is between 0 and the common weight, the user gets a common card
            # If the number is between the common weight and the sum of the common and rare weights, the user gets a rare card
            # If the number is between the sum of the common and rare weights and the sum of the common, rare, and epic weights, the user gets an epic card
            # If the number is between the sum of the common, rare, and epic weights and the sum of the common, rare, epic, and legendary weights, the user gets a legendary card
            card_rarity = weightedpick(["common", "rare", "epic", "legendary"],
                                        [timely_claim_common_weight, timely_claim_rare_weight, timely_claim_epic_weight,
                                         timely_claim_legendary_weight])
            card = card_collection.find_one({"rarity": card_rarity})
            user_collection.update_one({"discord_id": message.author.id}, {"$push": {"cards": card}})
            user_collection.update_one({"discord_id": message.author.id}, {"$set": {"claim_date": datetime.datetime.now()}})
            embedmsg = discord.Embed(title="Success", description=f"You have claimed a {card_rarity} card: {card['name']}",
                                     color=embed_msg_color_success)
            await message.channel.send(embed=embedmsg)
            return


        if command == "debug":
            if not checkperms(message.author.id, "admin"):
                embedmsg = discord.Embed(title="Error", description="You do not have permission to use this command",
                                         color=embed_msg_color_error)
                await message.channel.send(embed=embedmsg)
                return
            # subcommand is either args[0] or None
            subcommand = None
            if len(args) > 0:
                subcommand = args[0]
            if subcommand == "args":
                embedmsg = discord.Embed(title="Debug Information", description="Arguments:",
                                         color=embed_msg_color_standard)
                for (i, arg) in enumerate(args):
                    embedmsg.add_field(name=f"Argument {i}", value=arg, inline=False)
                await message.channel.send(embed=embedmsg)
                return
            if subcommand == "cardslist":
                if not checkperms(message.author.id, "admin"):
                    return
                cards = card_collection.find({})
                embedmsg = discord.Embed(title="Card List", description="List of all cards in the game",
                                         color=embed_msg_color_standard)
                for card in cards:
                    embedmsg.add_field(name=f"Card ID: {card['card_id']}",
                                       value=f"Name: {card['name']}\nRarity: {card['rarity']}\nDescription: {card['description']}",
                                       inline=False)
                await message.channel.send(embed=embedmsg)
                return
            if subcommand == "userslist":
                if not checkperms(message.author.id, "admin"):
                    return
                users = user_collection.find({})
                embedmsg = discord.Embed(title="User List", description="List of all users in the game",
                                         color=embed_msg_color_standard)
                for user in users:
                    embedmsg.add_field(name=f"Discord ID: {user['discord_id']}",
                                       value=f"Registration Date: {user['registration_date']}\nLevel: {user['level']}\nExp: {user['exp']}\nBalance: {user['balance']}",
                                       inline=False)
                await message.channel.send(embed=embedmsg)
                return
            if subcommand == "stafflist":
                if not checkperms(message.author.id, "admin"):
                    return
                staff = staff_collection.find({})
                embedmsg = discord.Embed(title="Staff List", description="List of all staff members",
                                         color=embed_msg_color_standard)
                for user in staff:
                    embedmsg.add_field(name=f"Discord ID: {user['discord_id']}",
                                       value=f"Access Type: {user['access_type']}", inline=False)
                await message.channel.send(embed=embedmsg)
                return

            # No subcommand was given, whoops
            embedmsg = discord.Embed(title="Error", description="Invalid subcommand", color=embed_msg_color_error)
            await message.channel.send(embed=embedmsg)
            return


def weightedpick(options, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for i, w in enumerate(weights):
        if upto + w >= r:
            return options[i]
        upto += w
    return options[-1]


def help(category):
    if category == "debug":
        embedmsg = discord.Embed(title="Debug Command Reference", description="List of commands for the debug command",
                                 color=embed_msg_color_standard)
        embedmsg.add_field(name="!debug args", value="Displays the arguments given to the debug command", inline=True)
        embedmsg.add_field(name="!debug cardslist", value="Displays a list of all cards in the game", inline=True)
        embedmsg.add_field(name="!debug userslist", value="Displays a list of all users in the game", inline=True)
        embedmsg.add_field(name="!debug stafflist", value="Displays a list of all staff members", inline=True)
        return embedmsg

    if category is not None:
        embedmsg = discord.Embed(title="Error", description="Invalid category", color=embed_msg_color_error)
        return embedmsg

    embedmsg = discord.Embed(title="Command Reference", description="List of commands for the trading card bot",
                             color=embed_msg_color_standard)
    embedmsg.add_field(name="!pingme", value="Pings the user", inline=True)
    embedmsg.add_field(name="!help", value="Displays this message", inline=True)
    embedmsg.add_field(name="!register", value="Registers the user into the game", inline=True)
    embedmsg.add_field(name="!checkperms", value="Checks the permissions of the user", inline=True)

    return embedmsg


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


client.run(token)
