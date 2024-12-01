import time
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivu import shivuu as bot

# Weapons with damage ranges
weapons = {
    "M1014 (Shotgun)": {"damage": (20, 40), "emoji": "🔫"},
    "AWM (Sniper)": {"damage": (50, 80), "emoji": "🎯"},
    "M249 (Machine Gun)": {"damage": (30, 50), "emoji": "🔥"},
    "Grenade": {"damage": (70, 100), "emoji": "💣"},
    "Rocket Launcher": {"damage": (90, 150), "emoji": "🚀"}
}

# Zombies with health and attack power
zombies = {
    "Normal Zombie": {"hp": 100, "attack": (5, 15), "emoji": "🧟"},
    "Fast Zombie": {"hp": 150, "attack": (10, 20), "emoji": "⚡"},
    "Tank Zombie": {"hp": 200, "attack": (15, 25), "emoji": "💪"},
    "Exploding Zombie": {"hp": 120, "attack": (20, 30), "emoji": "💥", "special": "explodes"},
    "Boss Zombie": {"hp": 500, "attack": (30, 50), "emoji": "👹", "special": "spawns minions"}
}

# Zombie images
zombie_images = {
    "Normal Zombie": "https://files.catbox.moe/tvjhmj.jpg",
    "Fast Zombie": "https://files.catbox.moe/l387v7.jpg",
    "Tank Zombie": "https://files.catbox.moe/qr6ad9.jpg",
    "Exploding Zombie": "https://files.catbox.moe/1sipya.jpg",
    "Boss Zombie": "https://files.catbox.moe/hiniq5.jpg"
}

# Consumable items
items = {
    "Medkit": {"effect": "heal", "value": 50, "emoji": "🩹"},
    "Energy Drink": {"effect": "boost", "value": 20, "emoji": "⚡"},
    "Shield": {"effect": "shield", "value": 30, "emoji": "🛡️"}
}

# Free Fire-inspired characters
characters = {
    "DJ Alok": {"ability": "Heal Over Time", "value": 10, "duration": 3, "emoji": "🎵"},
    "Chrono": {"ability": "Damage Reduction", "value": 20, "duration": 3, "emoji": "🛡️"},
    "Hayato": {"ability": "Armor Pierce", "value": 25, "emoji": "⚔️"},
    "Kelly": {"ability": "Speed Boost", "value": 2, "emoji": "⚡"},
    "K": {"ability": "Max HP Boost", "value": 50, "emoji": "💪"}
}

# Player stats and active battles
player_stats = {}
active_battles = {}

# Function to generate health bar
def generate_health_bar(current_hp, max_hp, length=10):
    filled = int((current_hp / max_hp) * length)
    empty = length - filled
    return f"{'▰' * filled}{'▱' * empty} ({current_hp}/{max_hp})"

# Start battle
@bot.on_message(filters.command("startbattle"))
async def start_battle(_, message: Message):
    user_id = message.from_user.id
    if user_id in active_battles:
        await message.reply_text("You are already in a battle!")
        return

    if user_id not in player_stats:
        player_stats[user_id] = {"xp": 0, "level": 1, "hp": 100}

    character_buttons = [
        [InlineKeyboardButton(f"{data['emoji']} {char} ({data['ability']})", callback_data=f"choose_{char}")]
        for char, data in characters.items()
    ]
    await message.reply_text(
        f"🎮 Choose your character:\n\n"
        f"🧍 <b>Level:</b> {player_stats[user_id]['level']}\n"
        f"❤️ <b>HP:</b> {player_stats[user_id]['hp']}\n"
        f"⭐ <b>XP:</b> {player_stats[user_id]['xp']}\n\n"
        "Each character has a unique ability. Choose wisely!",
        reply_markup=InlineKeyboardMarkup(character_buttons)
    )

# Character selection
@bot.on_callback_query(filters.regex("^choose_"))
async def choose_character(_, callback_query):
    user_id = callback_query.from_user.id
    char_name = callback_query.data.split("_")[1]
    character = characters[char_name]
    first_zombie = random.choice(list(zombies.items()))
    battle_data = {
        "user_hp": player_stats[user_id]["hp"] + (character["value"] if character["ability"] == "Max HP Boost" else 0),
        "character": character,
        "character_name": char_name,
        "zombies": [{"name": first_zombie[0], **first_zombie[1], "current_hp": first_zombie[1]["hp"]}],
        "items": ["Medkit", "Shield"]
    }
    active_battles[user_id] = battle_data

    zombie_image = zombie_images.get(first_zombie[0])
    await callback_query.message.edit_text(
        f"You are facing:\n{generate_health_bar(first_zombie[1]['hp'], first_zombie[1]['hp'])} {first_zombie[1]['emoji']} <b>{first_zombie[0]}</b>\n\n"
        f"<b>Your HP:</b> {generate_health_bar(battle_data['user_hp'], player_stats[user_id]['hp'])}\n\n"
        f"Select your weapon or use an item:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{data['emoji']} {weapon}", callback_data=f"attack_{weapon}")
                    for weapon, data in weapons.items()
                ],
                [InlineKeyboardButton("🛑 Stop Battle", callback_data="stop_battle")]
            ]
        )
    )

# Stop battle
@bot.on_callback_query(filters.regex("^stop_battle"))
async def stop_battle(_, callback_query):
    user_id = callback_query.from_user.id
    if user_id in active_battles:
        del active_battles[user_id]
        await callback_query.message.edit_text("🛑 You have exited the battle.")
    else:
        await callback_query.answer("You are not in a battle!", show_alert=True)

# Handle attacks
@bot.on_callback_query(filters.regex("^attack_"))
async def attack_zombie(_, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in active_battles:
        await callback_query.answer("You are not in a battle!", show_alert=True)
        return

    weapon_name = callback_query.data.split("_")[1]
    weapon_data = weapons[weapon_name]
    battle = active_battles[user_id]
    target_zombie = battle["zombies"][0]

    damage = random.randint(*weapon_data["damage"])
    target_zombie["current_hp"] -= damage

    if target_zombie["current_hp"] <= 0:
        await callback_query.message.edit_text(f"⚔️ You defeated {target_zombie['emoji']} <b>{target_zombie['name']}</b>!")
        del active_battles[user_id]
    else:
        user_damage = random.randint(*target_zombie["attack"])
        battle["user_hp"] -= user_damage
        if battle["user_hp"] <= 0:
            await callback_query.message.edit_text("💀 You were defeated by the zombie. Better luck next time!")
            del active_battles[user_id]
        else:
            await callback_query.message.edit_text(
                f"⚔️ You attacked with {weapon_data['emoji']} <b>{weapon_name}</b> and dealt <b>{damage}</b> damage!\n\n"
                f"Zombie attacked back and dealt <b>{user_damage}</b> damage!\n\n"
                f"<b>Your HP:</b> {generate_health_bar(battle['user_hp'], 100)}\n\n"
                f"<b>Zombie HP:</b> {generate_health_bar(target_zombie['current_hp'], target_zombie['hp'])}"
    )
