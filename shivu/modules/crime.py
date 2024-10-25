import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from shivu import shivuu as app, user_collection

COOLDOWN_DURATION = 300  # 5 minutes in seconds

# Dictionaries for tracking cooldowns and ongoing explorations
user_cooldowns = {}
ongoing_explorations = {}

# Define exploration locations and animations
exploration_options = [
    "Dungeon 🏰", "Demon Village 😈", "Sonagachi 💃", "Russian Harem 💋", "Ambani House 🏦",
    "Sex City 🏙️", "Fusha Village 🏞️", "Mystic Forest 🌲", "Dragon's Lair 🐉",
    "Pirate Cove 🏴‍☠️", "Haunted Mansion 👻", "Enchanted Garden 🌸", "Lost City 🏙️",
    "Viking Stronghold ⚔️", "Samurai Dojo 🥋", "Wizard Tower 🧙‍♂️", "Crystal Cave 💎",
    "Mermaid Lagoon 🧜‍♀️", "Gnome Village 🧝", "Fairy Forest 🧚", "Goblin Camp 👺",
    "Minotaur Labyrinth 🐂", "Phoenix Nest 🔥", "Treasure Island 🏝️", "Jungle Temple 🏯"
]

exploration_animations = [
    "🔍 Scanning the area...", "👣 Moving stealthily...", "✨ Magical energy surrounds you...",
    "🕵️ Searching carefully...", "🧭 The compass spins wildly..."
]

# Command to start exploration
@app.on_message(filters.command("crime"))
async def explore_command(client, message):
    user_id = message.from_user.id

    # Restrict to group chats only
    if message.chat.type == "private":
        await message.reply_text("⚠️ 𝘛𝘩𝘪𝘴 𝘤𝘰𝘮𝘮𝘢𝘯𝘥 𝘤𝘢𝘯 𝘰𝘯𝘭𝘺 𝘣𝘦 𝘶𝘴𝘦𝘥 𝘪𝘯 𝘨𝘳𝘰𝘶𝘱 𝘤𝘩𝘢𝘵𝘴.", parse_mode="HTML")
        return

    # Check if user is already exploring or in cooldown
    if user_id in ongoing_explorations:
        await message.reply_text("🕰️ 𝗬𝗼𝘂'𝗿𝗲 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗼𝗻 𝗮𝗻 𝗮𝗱𝘃𝗲𝗻𝘁𝘂𝗿𝗲! 𝗦𝗲𝗲 𝗶𝘁 𝘁𝗵𝗿𝗼𝘂𝗴𝗵 𝗯𝗲𝗳𝗼𝗿𝗲 𝗲𝗺𝗯𝗮𝗿𝗸𝗶𝗻𝗴 𝗮𝗴𝗮𝗶𝗻!", parse_mode="HTML")
        return

    # Cooldown check
    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await message.reply_text(f"⏳ 𝗪𝗮𝗶𝘁 {int(remaining_time)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝗯𝗲𝗳𝗼𝗿𝗲 𝗲𝘅𝗽𝗹𝗼𝗿𝗶𝗻𝗴 𝗮𝗴𝗮𝗶𝗻.", parse_mode="HTML")
        return

    # Start exploration
    ongoing_explorations[user_id] = True
    options = random.sample(exploration_options, 2)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(options[0], callback_data=f"explore_{user_id}_{options[0]}")],
        [InlineKeyboardButton(options[1], callback_data=f"explore_{user_id}_{options[1]}")]
    ])
    await message.reply_text("🗺️ <b>Select your exploration path!</b>", reply_markup=keyboard, parse_mode="HTML")

# Handle exploration choices
@app.on_callback_query(filters.regex(r"^explore_"))
async def handle_explore_choice(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split("_")
    command_user_id = int(data_parts[1])
    exploration_place = "_".join(data_parts[2:])

    if user_id != command_user_id:
        await callback_query.answer("⚠️ Not your button to press!", show_alert=True)
        return

    # Check cooldown
    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await callback_query.answer(f"⏳ Please wait {int(remaining_time)} seconds before exploring again.", show_alert=True)
        return

    # Exploration animations
    for animation in exploration_animations:
        await callback_query.message.edit_text(animation, parse_mode="HTML")
        await asyncio.sleep(1)

    # Random reward between 1000 and 5000 tokens
    random_reward = random.randint(1000, 5000)
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': random_reward}})

    # End exploration
    ongoing_explorations.pop(user_id, None)
    user_cooldowns[user_id] = datetime.utcnow()

    # Enhanced result messages for different locations
    place_messages = {
        "Dungeon 🏰": "💀 You descended into the <b>Dungeon</b> and unearthed ancient coins!",
        "Demon Village 😈": "😈 The demons tried to stop you, but you escaped with their treasure!",
        "Sonagachi 💃": "💃 After a memorable time, you earned quite a sum!",
        "Russian Harem 💋": "💋 An adventure worth the coins you collected!",
        "Ambani House 🏦": "🏦 You breached Ambani's vault and struck gold!",
        "Sex City 🏙️": "🛤️ The streets held secrets and riches for the taking.",
        "Fusha Village 🏞️": "🍃 Fusha’s rare herbs earned you a fortune!",
        "Mystic Forest 🌲": "🌲 A mystical artifact was your reward from the forest!",
        "Dragon's Lair 🐉": "🔥 A daring escape from the dragon’s lair left you rich!",
        "Pirate Cove 🏴‍☠️": "🏴‍☠️ The pirates’ stash is now yours!",
        "Haunted Mansion 👻": "👻 Spooky! But the mansion yielded hidden treasure.",
        "Enchanted Garden 🌸": "🌸 The fairies gifted you magical gold coins!",
        "Lost City 🏙️": "🏙️ Treasures of the lost city are now in your hands.",
        "Viking Stronghold ⚔️": "⚔️ Vikings’ treasure chest is yours now!",
        "Samurai Dojo 🥋": "🥋 The dojo’s hidden treasures are now yours!",
        "Wizard Tower 🧙‍♂️": "🔮 Magical artifacts were your reward from the Wizard’s Tower!",
        "Crystal Cave 💎": "💎 Precious gems from the Crystal Cave are yours!",
        "Mermaid Lagoon 🧜‍♀️": "🧜‍♀️ A treasure chest lies beneath the waves!",
        "Gnome Village 🧝": "🧝 The gnomes shared their gold with you.",
        "Fairy Forest 🧚": "🧚 A treasure hidden by fairies was found!",
        "Goblin Camp 👺": "👺 You stole the goblins' stash and escaped!",
        "Minotaur Labyrinth 🐂": "🐂 After braving the maze, you found a hoard!",
        "Phoenix Nest 🔥": "🔥 Left with a treasure from the Phoenix Nest!",
        "Treasure Island 🏝️": "🏝️ X marks the spot! You found the treasure.",
        "Jungle Temple 🏯": "🏯 You uncovered riches hidden in the jungle temple!"
    }

    result_message = place_messages.get(exploration_place, f"✨ You explored the {exploration_place} and found hidden treasure.")
    await callback_query.message.edit_text(f"{result_message}\n\n🎉 <b>You gained {random_reward} tokens! 💰</b>", parse_mode="HTML")
