import random
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from shivu import shivuu as app, user_collection

COOLDOWN_DURATION = 300  # 5 minutes in seconds

# Create dictionaries to store cooldown information
user_cooldowns = {}
ongoing_explorations = {}

exploration_options = [
    "Dungeon 🏰",
    "Demon Village 😈",
    "Sonagachi 💃",
    "Russian Harem 💋",
    "Ambani House 🏦",
    "Sex City 🏙️",
    "Fusha Village 🏞️",
    "Mystic Forest 🌲",
    "Dragon's Lair 🐉",
    "Pirate Cove 🏴‍☠️",
    "Haunted Mansion 👻",
    "Enchanted Garden 🌸",
    "Lost City 🏙️",
    "Viking Stronghold ⚔️",
    "Samurai Dojo 🥋",
    "Wizard Tower 🧙‍♂️",
    "Crystal Cave 💎",
    "Mermaid Lagoon 🧜‍♀️",
    "Gnome Village 🧝",
    "Fairy Forest 🧚",
    "Goblin Camp 👺",
    "Minotaur Labyrinth 🐂",
    "Phoenix Nest 🔥",
    "Treasure Island 🏝️",
    "Jungle Temple 🏯"
]

exploration_animations = [
    "🔍 Scanning the area...",
    "👣 Walking cautiously...",
    "✨ Magic fills the air...",
    "🕵️ Searching every corner...",
    "🧭 Your compass spins wildly...",
]

# Command to start exploration
@app.on_message(filters.command("crime"))
async def explore_command(client, message):
    user_id = message.from_user.id

    if message.chat.type == "private":
        await message.reply_text("This command can only be used in group chats.")
        return

    if user_id in ongoing_explorations:
        await message.reply_text("You are already exploring. Wait until your current adventure ends!")
        return

    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await message.reply_text(f"Please wait {int(remaining_time)} seconds before exploring again.")
        return

    ongoing_explorations[user_id] = True

    options = random.sample(exploration_options, 2)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(options[0], callback_data=f"explore_{user_id}_{options[0]}")],
        [InlineKeyboardButton(options[1], callback_data=f"explore_{user_id}_{options[1]}")]
    ])
    await message.reply_text("Choose where you'd like to explore!", reply_markup=keyboard)

# Callback query handler for exploration choices
@app.on_callback_query(filters.regex(r"^explore_"))
async def handle_explore_choice(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split("_")
    command_user_id = int(data_parts[1])
    exploration_place = "_".join(data_parts[2:])

    if user_id != command_user_id:
        await callback_query.answer("It's not your button to press!", show_alert=True)
        return

    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await callback_query.answer(f"Please wait {int(remaining_time)} seconds before exploring again.", show_alert=True)
        return

    # Simulate exploration animation with emojis
    for animation in exploration_animations:
        await callback_query.message.edit_text(animation)
        await asyncio.sleep(1)

    # Generate a random reward between 1000 and 5000 tokens
    random_reward = random.randint(1000, 5000)

    # Update user balance in the database
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': random_reward}})

    # End exploration
    if user_id in ongoing_explorations:
        del ongoing_explorations[user_id]

    # Set the user cooldown
    user_cooldowns[user_id] = datetime.utcnow()

    # Exploration result messages based on the place
    place_messages = {
        "Dungeon 🏰": "You ventured deep into the Dungeon and uncovered an ancient chest filled with gold!",
        "Demon Village 😈": "The demons were fierce, but you outsmarted them and stole their treasure!",
        "Sonagachi 💃": "It was a wild night, but you earned a small fortune in the end!",
        "Russian Harem 💋": "Well, that was quite an experience... You left with a heavy purse.",
        "Ambani House 🏦": "You managed to sneak into Ambani's vault! Jackpot!",
        "Sex City 🏙️": "You explored the streets of Sex City and found a hidden stash of coins!",
        "Fusha Village 🏞️": "You visited Fusha Village and found some rare herbs worth a lot of money.",
        "Mystic Forest 🌲": "In the Mystic Forest, you found a magical artifact worth a fortune!",
        "Dragon's Lair 🐉": "You bravely entered the Dragon's Lair and escaped with a treasure hoard!",
        "Pirate Cove 🏴‍☠️": "The pirates were no match for you, and you sailed away with their treasure!",
        "Haunted Mansion 👻": "Spooky! But you managed to find hidden treasure in the Haunted Mansion!",
        "Enchanted Garden 🌸": "The Enchanted Garden rewarded you with magical gold coins!",
        "Lost City 🏙️": "The Lost City held many secrets, and you uncovered valuable treasures.",
        "Viking Stronghold ⚔️": "The Vikings' stronghold was no match for you. You looted their treasure!",
        "Samurai Dojo 🥋": "You found hidden treasures in the Samurai Dojo after a fierce battle!",
        "Wizard Tower 🧙‍♂️": "The Wizard's Tower held many magical items, and you left with a rare gem.",
        "Crystal Cave 💎": "In the depths of the Crystal Cave, you uncovered precious jewels!",
        "Mermaid Lagoon 🧜‍♀️": "The mermaids guided you to a hidden underwater treasure!",
        "Gnome Village 🧝": "The gnomes were generous and shared some of their gold with you.",
        "Fairy Forest 🧚": "The fairies of the forest rewarded you with enchanted gold coins!",
        "Goblin Camp 👺": "You raided the Goblin Camp and escaped with their treasure!",
        "Minotaur Labyrinth 🐂": "You navigated the Minotaur's Labyrinth and found a stash of gold!",
        "Phoenix Nest 🔥": "The Phoenix left behind a pile of gold in its nest!",
        "Treasure Island 🏝️": "X marks the spot! You found the buried treasure on Treasure Island!",
        "Jungle Temple 🏯": "In the heart of the Jungle Temple, you found a forgotten treasure!"
    }

    result_message = place_messages.get(exploration_place, f"You explored the {exploration_place} and found a hidden treasure.")

    await callback_query.message.edit_text(f"{result_message}\nYou gained {random_reward} tokens! 💰")
