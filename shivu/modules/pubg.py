import time
import asyncio
import random
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Database collection for users
from shivu import user_collection

# PUBG Game Variables
AUTHORIZED_USER_ID = 7011990425
COOLDOWN_TIME = 60  # 1 minute cooldown for missions
RANKS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ace", "Conqueror"]

# Weapon Prices and Inventory
weapon_prices = {
    "Pistol": {"price": 500, "emoji": "🔫", "aliases": ["pistol", "p"]},
    "Rifle": {"price": 2000, "emoji": "🔫", "aliases": ["rifle", "r"]},
    "Sniper": {"price": 5000, "emoji": "🎯", "aliases": ["sniper", "s"]},
    "Grenade": {"price": 1000, "emoji": "💣", "aliases": ["grenade", "g"]},
    "Health Kit": {"price": 800, "emoji": "🩹", "aliases": ["healthkit", "hk"]}
}

# Mission Types
missions = {
    "daily": [
        {"name": "Win 3 Matches", "reward": {"coins": 100, "xp": 50}},
        {"name": "Kill 10 Enemies", "reward": {"coins": 200, "xp": 100}},
    ],
    "weekly": [
        {"name": "Play 20 Matches", "reward": {"coins": 500, "xp": 300}},
        {"name": "Kill 50 Enemies", "reward": {"coins": 1000, "xp": 500}},
    ],
}

ranks = [
    {"name": "Bronze", "min_xp": 0},
    {"name": "Silver", "min_xp": 500},
    {"name": "Gold", "min_xp": 1500},
    {"name": "Platinum", "min_xp": 3000},
    {"name": "Diamond", "min_xp": 5000},
    {"name": "Crown", "min_xp": 8000},
    {"name": "Ace", "min_xp": 12000},
    {"name": "Conqueror", "min_xp": 20000},
]

crates = {
    "basic_crate": {"price": 100, "contents": ["Weapon Skin", "Coins", "UC", "XP"]},
    "premium_crate": {"price": 500, "contents": ["Rare Skin", "Legendary Skin", "Coins", "XP"]},
}

# Command to display inventory
@Client.on_message(filters.command(["inventory"]))
async def inventory_command(client, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'inventory': 1})
    
    if user_data and user_data.get('inventory'):
        inventory = user_data['inventory']
        inventory_text = "<b>Your Inventory:</b>\n"
        for item, quantity in inventory.items():
            emoji = weapon_prices[item]["emoji"]
            inventory_text += f"{emoji} <b>{item}</b>: <b>{quantity}</b>\n"
        await message.reply_text(inventory_text)
    else:
        await message.reply_text("Your inventory is empty! Complete missions or buy items to fill it.")

# Command to buy items
@Client.on_message(filters.command(["buy"]))
async def buy_command(client, message):
    user_id = message.from_user.id
    command_parts = message.text.split()
    
    if len(command_parts) != 3:
        return await message.reply_text("Usage: /buy <item name> <quantity>")
    
    item_name = command_parts[1]
    quantity = int(command_parts[2])
    
    found_item = None
    for weapon, details in weapon_prices.items():
        if item_name.lower() in [weapon.lower()] + details["aliases"]:
            found_item = weapon
            break
    
    if not found_item:
        return await message.reply_text("Invalid item name.")
    
    user_data = await user_collection.find_one({'id': user_id}, projection={'tokens': 1, 'inventory': 1})
    tokens = user_data.get('tokens', 0)
    total_cost = weapon_prices[found_item]["price"] * quantity
    
    if tokens < total_cost:
        return await message.reply_text(f"You don't have enough tokens. You need {total_cost - tokens} more.")
    
    # Deduct tokens and add items to inventory
    await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -total_cost}})
    inventory = user_data.get('inventory', {})
    inventory[found_item] = inventory.get(found_item, 0) + quantity
    await user_collection.update_one({'id': user_id}, {'$set': {'inventory': inventory}})
    
    await message.reply_text(f"You bought {quantity} {weapon_prices[found_item]['emoji']} {found_item}!")

# Command to start a mission
@bot.on_message(filters.command(["missions"]))
async def show_missions(_, message: t.Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'completed_missions': 1})
    completed_missions = user_data.get('completed_missions', [])
    
    mission_text = "<b>Your Missions:</b>\n\n"
    for mission_type, mission_list in missions.items():
        mission_text += f"<b>{mission_type.capitalize()} Missions:</b>\n"
        for mission in mission_list:
            status = "✅" if mission["name"] in completed_missions else "❌"
            mission_text += f"{status} {mission['name']} - Reward: {mission['reward']['coins']} Coins, {mission['reward']['xp']} XP\n"
        mission_text += "\n"
    await message.reply_text(mission_text)

@bot.on_message(filters.command(["complete_mission"]))
async def complete_mission(_, message: t.Message):
    user_id = message.from_user.id
    mission_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not mission_name:
        return await message.reply_text("Specify the mission name to complete it.")

    for mission_list in missions.values():
        for mission in mission_list:
            if mission_name.lower() == mission["name"].lower():
                # Mark mission as complete
                await user_collection.update_one(
                    {'id': user_id},
                    {'$push': {'completed_missions': mission["name"]}, '$inc': {
                        'coins': mission["reward"]["coins"],
                        'xp': mission["reward"]["xp"]
                    }}
                )
                return await message.reply_text(f"Mission '{mission_name}' completed! Rewards added.")
    await message.reply_text("Mission not found.")
    
# Admin Command: Reset inventory
@Client.on_message(filters.user(AUTHORIZED_USER_ID) & filters.command(["reset_inventory"]))
async def reset_inventory(client, message):
    await user_collection.update_many({}, {'$unset': {'inventory': 1}})
    await message.reply_text("All inventories have been reset!")

# Command to display rank
@Client.on_message(filters.command(["rank"]))
async def rank_command(client, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'xp': 1})
    xp = user_data.get('xp', 0)
    rank_index = min(xp // 1000, len(RANKS) - 1)
    rank = RANKS[rank_index]
    
    await message.reply_text(f"Your Rank: {rank}\nXP: {xp}/1000 for next rank.")

# Admin Command: Add tokens to a user
@Client.on_message(filters.user(AUTHORIZED_USER_ID) & filters.command(["add_tokens"]))
async def add_tokens(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 3:
        return await message.reply_text("Usage: /add_tokens <user_id> <amount>")
    
    target_user_id = int(command_parts[1])
    amount = int(command_parts[2])
    
    await user_collection.update_one({'id': target_user_id}, {'$inc': {'tokens': amount}})
    await message.reply_text(f"Added {amount} tokens to user {target_user_id}.")

@bot.on_message(filters.command(["rank"]))
async def show_rank(_, message: t.Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'xp': 1})
    xp = user_data.get('xp', 0)

    user_rank = "Unranked"
    for rank in ranks:
        if xp >= rank["min_xp"]:
            user_rank = rank["name"]

    next_rank = next((rank for rank in ranks if xp < rank["min_xp"]), None)
    next_rank_text = f"Next Rank: {next_rank['name']} ({next_rank['min_xp'] - xp} XP needed)" if next_rank else "Max Rank Achieved"

    await message.reply_text(f"Your Rank: {user_rank}\nXP: {xp}\n{next_rank_text}")

@bot.on_message(filters.command(["open_crate"]))
async def open_crate(_, message: t.Message):
    user_id = message.from_user.id
    crate_type = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if crate_type not in crates:
        return await message.reply_text("Invalid crate type. Available crates: basic_crate, premium_crate.")

    user_data = await user_collection.find_one({'id': user_id}, projection={'coins': 1})
    coins = user_data.get('coins', 0)

    if coins < crates[crate_type]["price"]:
        return await message.reply_text("Not enough coins to open this crate.")

    # Deduct coins and give random reward
    reward = random.choice(crates[crate_type]["contents"])
    await user_collection.update_one({'id': user_id}, {'$inc': {'coins': -crates[crate_type]["price"]}})
    await message.reply_text(f"You opened a {crate_type} and got: {reward}!")

@bot.on_message(filters.command(["match"]))
async def match(_, message: t.Message):
    user_id = message.from_user.id
    opponent_id = random.choice([123456, 7891011])  # Example IDs for opponents
    await message.reply_text(f"Matched with opponent: User {opponent_id}!\nFight begins...")
    await asyncio.sleep(2)
    
    if random.randint(1, 100) > 50:
        await message.reply_text("You won the match! Reward: 100 Coins")
        await user_collection.update_one({'id': user_id}, {'$inc': {'coins': 100}})
    else:
        await message.reply_text("You lost the match! Better luck next time.")
