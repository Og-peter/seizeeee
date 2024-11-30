import random
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Bot instance
bot = Client("zombie_game_bot")

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

# Consumable items
items = {
    "Medkit": {"effect": "heal", "value": 50, "emoji": "🩹"},
    "Energy Drink": {"effect": "boost", "value": 20, "emoji": "⚡"},
    "Shield": {"effect": "shield", "value": 30, "emoji": "🛡️"}
}

# Free Fire-inspired characters
characters = {
    "DJ Alok": {"ability": "heal_over_time", "value": 10, "duration": 3, "emoji": "🎵", "description": "Heals 10 HP for 3 turns."},
    "Chrono": {"ability": "damage_reduction", "value": 20, "duration": 3, "emoji": "🛡️", "description": "Reduces incoming damage by 20% for 3 turns."},
    "Hayato": {"ability": "armor_pierce", "value": 25, "emoji": "⚔️", "description": "Increases damage by 25%."},
    "Kelly": {"ability": "speed_boost", "value": 2, "emoji": "⚡", "description": "Allows two attacks per turn."},
    "K": {"ability": "max_hp_boost", "value": 50, "emoji": "💪", "description": "Increases max HP by 50."}
}

# Active battles
active_battles = {}

# Function to generate a health bar ▰▱ style
def generate_health_bar(current_hp, max_hp, length=10):
    filled = int((current_hp / max_hp) * length)
    empty = length - filled
    return f"{'▰' * filled}{'▱' * empty} ({current_hp}/{max_hp})"

# Start the battle with character selection
@bot.on_message(filters.command("startbattle"))
async def start_battle(client, message: Message):
    user_id = message.from_user.id
    if user_id in active_battles:
        await message.reply_text("You are already in a battle!")
        return

    # Character selection
    character_buttons = [
        [InlineKeyboardButton(f"{data['emoji']} {char} - {data['description']}", callback_data=f"choose_{char}")]
        for char, data in characters.items()
    ]
    await message.reply_text(
        "🎮 Choose your character:\n\n"
        "Each character has a unique ability. Choose wisely!",
        reply_markup=InlineKeyboardMarkup(character_buttons)
    )

# Handle character selection
@bot.on_callback_query(filters.regex("^choose_"))
async def choose_character(client, callback_query):
    user_id = callback_query.from_user.id
    char_name = callback_query.data.split("_")[1]
    if user_id in active_battles:
        await callback_query.answer("You already chose your character!", show_alert=True)
        return

    character = characters[char_name]
    zombie_list = random.sample(list(zombies.items()), k=random.randint(2, 3))
    battle_data = {
        "user_hp": 100 + (character["value"] if character["ability"] == "max_hp_boost" else 0),
        "character": character,
        "character_name": char_name,
        "character_uses": character.get("duration", 0),
        "zombies": [
            {"name": name, **data, "current_hp": data["hp"]} for name, data in zombie_list
        ],
        "items": ["Medkit", "Shield"]
    }
    active_battles[user_id] = battle_data

    zombie_details = "\n".join(
        f"{z['emoji']} <b>{z['name']}</b>: {generate_health_bar(z['current_hp'], z['hp'])}"
        for z in battle_data["zombies"]
    )
    await callback_query.message.edit_text(
        f"🚨 Battle Started with {character['emoji']} <b>{char_name}</b>! 🚨\n\n"
        f"You are facing:\n{zombie_details}\n\n"
        f"<b>Your HP:</b> {generate_health_bar(battle_data['user_hp'], 100)}\n\n"
        f"Select your weapon or use an item:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"{data['emoji']} {weapon}", callback_data=f"attack_{weapon}")]
                for weapon, data in weapons.items()
            ] + [
                [InlineKeyboardButton(f"{items[item]['emoji']} {item}", callback_data=f"item_{item}")]
                for item in battle_data["items"]
            ]
        )
    )

# Apply character abilities during attacks
def apply_character_ability(battle, damage):
    character = battle["character"]
    if character["ability"] == "heal_over_time" and battle["character_uses"] > 0:
        battle["user_hp"] = min(100, battle["user_hp"] + character["value"])
        battle["character_uses"] -= 1
    elif character["ability"] == "damage_reduction" and battle["character_uses"] > 0:
        damage = max(0, damage - (damage * character["value"] // 100))
        battle["character_uses"] -= 1
    elif character["ability"] == "armor_pierce":
        damage = damage + (damage * character["value"] // 100)
    elif character["ability"] == "speed_boost":
        damage *= 2
    return damage

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
    zombies_alive = [z for z in battle["zombies"] if z["current_hp"] > 0]

    if not zombies_alive:
        del active_battles[user_id]
        await callback_query.message.edit_text("🎉 You defeated all the zombies! 🏆")
        return

    target_zombie = random.choice(zombies_alive)
    base_damage = random.randint(*weapon_data["damage"])
    damage = apply_character_ability(battle, base_damage)
    target_zombie["current_hp"] -= damage

    if target_zombie["current_hp"] <= 0 and target_zombie.get("special") == "explodes":
        battle["user_hp"] -= 20

    if battle["user_hp"] <= 0:
        del active_battles[user_id]
        await callback_query.message.edit_text("💀 You were defeated by the zombies. Better luck next time!")
        return

    zombie_details = "\n".join(
        f"{z['emoji']} <b>{z['name']}</b>: {generate_health_bar(z['current_hp'], z['hp'])}"
        for z in battle["zombies"] if z["current_hp"] > 0
    )
    await callback_query.message.edit_text(
        f"⚔️ You attacked with {weapon_data['emoji']} <b>{weapon_name}</b> and dealt <b>{damage}</b> damage!\n\n"
        f"You are facing:\n{zombie_details}\n\n"
        f"<b>Your HP:</b> {generate_health_bar(battle['user_hp'], 100)}",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"{data['emoji']} {weapon}", callback_data=f"attack_{weapon}")]
                for weapon, data in weapons.items()
            ] + [
                [InlineKeyboardButton(f"{items[item]['emoji']} {item}", callback_data=f"item_{item}")]
                for item in battle["items"]
            ]
        )
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
                [InlineKeyboardButton(f"{data['emoji']} {weapon}", callback_data=f"attack_{weapon}")]
                for weapon, data in weapons.items()
            ] + [
                [InlineKeyboardButton(f"{items[item]['emoji']} {item}", callback_data=f"item_{item}")]
                for item in battle["items"]
            ]
        )
    )

# Function to handle end-of-battle cleanup
def end_battle(user_id):
    if user_id in active_battles:
        del active_battles[user_id]
