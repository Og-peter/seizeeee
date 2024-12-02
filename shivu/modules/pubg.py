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
    "loot": {"description": "Find loot in Pochinki", "reward": 1000, "chance": 90},
    "kill": {"description": "Eliminate 3 enemies", "reward": 1500, "chance": 70},
    "survival": {"description": "Survive for 5 minutes", "reward": 2000, "chance": 50}
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
@Client.on_message(filters.command(["mission"]))
async def mission_command(client, message):
    user_id = message.from_user.id
    mission = random.choice(list(missions.values()))
    
    result = random.randint(1, 100)
    if result <= mission["chance"]:
        # Success
        reward = mission["reward"]
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': reward}})
        await message.reply_text(f"Mission Success! {mission['description']}\nReward: {reward} tokens.")
    else:
        # Failure
        await message.reply_text(f"Mission Failed! {mission['description']}\nTry again later.")

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
