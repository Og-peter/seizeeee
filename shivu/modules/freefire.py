import time
import asyncio
import random
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Weapons with damage and upgrade levels
weapons = {
    "M1014 (Shotgun)": {"damage": (20, 40), "emoji": "🔫", "level": 1},
    "AWM (Sniper)": {"damage": (50, 80), "emoji": "🎯", "level": 1},
    "M249 (Machine Gun)": {"damage": (30, 50), "emoji": "🔥", "level": 1},
    "Grenade": {"damage": (70, 100), "emoji": "💣", "level": 1},
    "Rocket Launcher": {"damage": (90, 150), "emoji": "🚀", "level": 1},
}

# Zombies with health, attack, and images
zombies = {
    "Normal Zombie": {"hp": 100, "attack": (5, 15), "emoji": "🧟", "image": "https://files.catbox.moe/tvjhmj.jpg"},
    "Fast Zombie": {"hp": 150, "attack": (10, 20), "emoji": "⚡", "image": "https://files.catbox.moe/l387v7.jpg"},
    "Tank Zombie": {"hp": 200, "attack": (15, 25), "emoji": "💪", "image": "https://files.catbox.moe/qr6ad9.jpg"},
    "Exploding Zombie": {"hp": 120, "attack": (20, 30), "emoji": "💥", "special": "explodes", "image": "https://files.catbox.moe/1sipya.jpg"},
    "Boss Zombie": {"hp": 500, "attack": (30, 50), "emoji": "👹", "special": "spawns minions", "image": "https://files.catbox.moe/hiniq5.jpg"},
}

# Consumable items
items = {
    "Medkit": {"effect": "heal", "value": 50, "emoji": "🩹"},
    "Energy Drink": {"effect": "boost", "value": 20, "emoji": "⚡"},
    "Shield": {"effect": "shield", "value": 30, "emoji": "🛡️"},
}

# Free Fire-inspired characters
characters = {
    "DJ Alok": {"ability": "Heal Over Time", "value": 10, "duration": 3, "emoji": "🎵"},
    "Chrono": {"ability": "Damage Reduction", "value": 20, "duration": 3, "emoji": "🛡️"},
    "Hayato": {"ability": "Armor Pierce", "value": 25, "emoji": "⚔️"},
    "Kelly": {"ability": "Speed Boost", "value": 2, "emoji": "⚡"},
    "K": {"ability": "Max HP Boost", "value": 50, "emoji": "💪"},
}

active_battles = {}
user_stats = {}  # To track stats like level, XP, kills

# Initialize user stats if not present
def initialize_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"level": 1, "xp": 0, "kills": 0}

# Generate health bar
def generate_health_bar(current_hp, max_hp, length=10):
    filled = int((current_hp / max_hp) * length)
    empty = length - filled
    return f"{'▰' * filled}{'▱' * empty} ({current_hp}/{max_hp})"

# Calculate level based on XP
def calculate_level(xp):
    return 1 + xp // 100

# Start battle
@bot.on_message(filters.command("startbattle"))
async def start_battle(client, message: Message):
    user_id = message.from_user.id
    initialize_user_stats(user_id)

    if user_id in active_battles:
        await message.reply_text("You are already in a battle!")
        return

    character_buttons = [
        [InlineKeyboardButton(f"{data['emoji']} {char} ({data['ability']})", callback_data=f"choose_{char}")]
        for char, data in characters.items()
    ]
    await message.reply_text(
        "🎮 Choose your character:\n\n"
        "Each character has a unique ability. Choose wisely!",
        reply_markup=InlineKeyboardMarkup(character_buttons)
    )

# Choose character
@bot.on_callback_query(filters.regex("^choose_"))
async def choose_character(client, callback_query):
    user_id = callback_query.from_user.id
    char_name = callback_query.data.split("_")[1]
    initialize_user_stats(user_id)

    if user_id in active_battles:
        await callback_query.answer("You already chose your character!", show_alert=True)
        return

    character = characters[char_name]
    first_zombie = random.choice(list(zombies.items()))
    battle_data = {
        "user_hp": 100 + (character["value"] if character["ability"] == "Max HP Boost" else 0),
        "character": character,
        "character_name": char_name,
        "zombies": [{"name": first_zombie[0], **first_zombie[1], "current_hp": first_zombie[1]["hp"]}],
        "items": ["Medkit", "Shield"],
        "user_level": user_stats[user_id]["level"],
    }
    active_battles[user_id] = battle_data

    await callback_query.message.edit_text(
        f"🚨 Battle Started with {character['emoji']} <b>{char_name}</b>! 🚨\n\n"
        f"Facing Zombie:\n{generate_health_bar(first_zombie[1]['hp'], first_zombie[1]['hp'])} {first_zombie[1]['emoji']} <b>{first_zombie[0]}</b>\n\n"
        f"<b>Your Stats:</b> Level {battle_data['user_level']}, Kills {user_stats[user_id]['kills']}\n"
        f"<b>Your HP:</b> {generate_health_bar(battle_data['user_hp'], 100)}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{data['emoji']} {weapon}", callback_data=f"attack_{weapon}")
                    for weapon, data in weapons.items()
                ],
                [
                    InlineKeyboardButton("🛑 Stop Battle", callback_data="stop_battle")
                ],
            ]
        ),
    )

# Stop battle
@bot.on_callback_query(filters.regex("^stop_battle"))
async def stop_battle(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in active_battles:
        del active_battles[user_id]
        await callback_query.message.edit_text("🛑 You have exited the battle.")
    else:
        await callback_query.answer("You are not in a battle!", show_alert=True)

# Handle attacks
@bot.on_callback_query(filters.regex("^attack_"))
async def attack_zombie(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in active_battles:
        await callback_query.answer("You are not in a battle!", show_alert=True)
        return

    weapon_name = callback_query.data.split("_")[1]
    weapon_data = weapons[weapon_name]
    battle = active_battles[user_id]
    target_zombie = battle["zombies"][0]

    # Calculate damage
    base_damage = random.randint(*weapon_data["damage"])
    damage = base_damage
    target_zombie["current_hp"] -= damage

    if target_zombie["current_hp"] <= 0:
        # Zombie defeated
        await callback_query.message.edit_text(
            f"⚔️ You defeated {target_zombie['emoji']} <b>{target_zombie['name']}</b>!"
        )
        del active_battles[user_id]  # End the battle
    else:
        # Zombie attacks back
        user_damage = random.randint(*target_zombie["attack"])
        battle["user_hp"] -= user_damage

        if battle["user_hp"] <= 0:
            # User defeated
            await callback_query.message.edit_text(
                "💀 You were defeated by the zombie. Better luck next time!"
            )
            del active_battles[user_id]
        else:
            # Continue battle
            await callback_query.message.edit_text(
                f"⚔️ You attacked with {weapon_data['emoji']} <b>{weapon_name}</b> and dealt <b>{damage}</b> damage!\n\n"
                f"Zombie attacked back and dealt <b>{user_damage}</b> damage!\n\n"
                f"<b>Your HP:</b> {generate_health_bar(battle['user_hp'], 100)}\n\n"
                f"<b>Zombie HP:</b> {generate_health_bar(target_zombie['current_hp'], target_zombie['hp'])}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"{data['emoji']} {weapon}",
                                callback_data=f"attack_{weapon}",
                            )
                            for weapon, data in list(weapons.items())[:3]
                        ],
                        [
                            InlineKeyboardButton(
                                f"{data['emoji']} {weapon}",
                                callback_data=f"attack_{weapon}",
                            )
                            for weapon, data in list(weapons.items())[3:6]
                        ],
                        [
                            InlineKeyboardButton(
                                f"{items[item]['emoji']} {item}",
                                callback_data=f"item_{item}",
                            )
                            for item in battle["items"][:3]
                        ],
                        [
                            InlineKeyboardButton(
                                f"{items[item]['emoji']} {item}",
                                callback_data=f"item_{item}",
                            )
                            for item in battle["items"][3:6]
                        ],
                        [
                            InlineKeyboardButton(
                                "🛑 Stop Battle", callback_data="stop_battle"
                            )
                        ],
                    ]
                ),
            )


# Handle item usage
@bot.on_callback_query(filters.regex("^item_"))
async def use_item(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in active_battles:
        await callback_query.answer("You are not in a battle!", show_alert=True)
        return

    item_name = callback_query.data.split("_")[1]
    battle = active_battles[user_id]
    item = items[item_name]

    # Apply item effect
    if item["effect"] == "heal":
        battle["user_hp"] = min(100, battle["user_hp"] + item["value"])
    elif item["effect"] == "shield":
        battle["user_hp"] += item["value"]  # Temporary shield effect

    # Remove item after use
    battle["items"].remove(item_name)

    await callback_query.message.edit_text(
        f"🧰 You used {item['emoji']} <b>{item_name}</b>! Effect applied.\n\n"
        f"<b>Your HP:</b> {generate_health_bar(battle['user_hp'], 100)}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{data['emoji']} {weapon}",
                        callback_data=f"attack_{weapon}",
                    )
                    for weapon, data in list(weapons.items())[:3]
                ],
                [
                    InlineKeyboardButton(
                        f"{data['emoji']} {weapon}",
                        callback_data=f"attack_{weapon}",
                    )
                    for weapon, data in list(weapons.items())[3:6]
                ],
                [
                    InlineKeyboardButton(
                        f"{items[item]['emoji']} {item}",
                        callback_data=f"item_{item}",
                    )
                    for item in battle["items"][:3]
                ],
                [
                    InlineKeyboardButton(
                        f"{items[item]['emoji']} {item}",
                        callback_data=f"item_{item}",
                    )
                    for item in battle["items"][3:6]
                ],
            ]
        ),
    )

# Function to handle end-of-battle cleanup
def end_battle(user_id):
    if user_id in active_battles:
        del active_battles[user_id]
