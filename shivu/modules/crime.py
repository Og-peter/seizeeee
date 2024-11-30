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
    "🔍 Scanning the area for hidden treasures...",
    "👣 Treading carefully through uncharted paths...",
    "✨ A mysterious energy envelops your journey...",
    "🕵️ Unearthing secrets with precision...",
    "🧭 Following the compass to the unknown..."
]

# Command to start exploration
@app.on_message(filters.command("crime"))
async def explore_command(client, message):
    user_id = message.from_user.id

    # Restrict to group chats only
    if message.chat.type == "private":
        await message.reply_text("⚠️ <b>This command is restricted to group chats only!</b>")
        return

    # Check if user is already exploring or in cooldown
    if user_id in ongoing_explorations:
        await message.reply_text("🕰️ <b>You're already on an adventure! Complete it before starting a new one.</b>")
        return

    # Cooldown check
    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await message.reply_text(f"⏳ <b>You need to wait {int(remaining_time)} seconds before exploring again.</b>")
        return

    # Start exploration
    ongoing_explorations[user_id] = True
    options = random.sample(exploration_options, 2)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(options[0], callback_data=f"explore_{user_id}_{options[0]}")],
        [InlineKeyboardButton(options[1], callback_data=f"explore_{user_id}_{options[1]}")]
    ])
    await message.reply_text("🗺️ <b>Choose your path to embark on an unforgettable adventure:</b>", reply_markup=keyboard)

# Handle exploration choices
@app.on_callback_query(filters.regex(r"^explore_"))
async def handle_explore_choice(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split("_")
    command_user_id = int(data_parts[1])
    exploration_place = "_".join(data_parts[2:])

    if user_id != command_user_id:
        await callback_query.answer("⚠️ This is not your adventure to explore!", show_alert=True)
        return

    # Check cooldown
    if user_id in user_cooldowns and (datetime.utcnow() - user_cooldowns[user_id]) < timedelta(seconds=COOLDOWN_DURATION):
        remaining_time = COOLDOWN_DURATION - (datetime.utcnow() - user_cooldowns[user_id]).total_seconds()
        await callback_query.answer(f"⏳ Hold on! You need to wait {int(remaining_time)} seconds.", show_alert=True)
        return

    # Exploration animations
    for animation in exploration_animations:
        await callback_query.message.edit_text(animation)
        await asyncio.sleep(1)

    # Random reward between 1000 and 5000 tokens
    random_reward = random.randint(1000, 5000)
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': random_reward}})

    # End exploration
    ongoing_explorations.pop(user_id, None)
    user_cooldowns[user_id] = datetime.utcnow()

    # Enhanced result messages for different locations
    place_messages = {
        "Dungeon 🏰": "💀 <b>You braved the Dungeon and discovered ancient treasures hidden for centuries!</b>",
        "Demon Village 😈": "😈 <b>Despite the demons' wrath, you escaped with a chest of rare jewels!</b>",
        "Sonagachi 💃": "💃 <b>A wild night led to unexpected riches in your hands!</b>",
        "Russian Harem 💋": "💋 <b>An exotic adventure rewarded you with priceless artifacts!</b>",
        "Ambani House 🏦": "🏦 <b>Cracking the vault was no easy feat, but you're now richer than ever!</b>",
        "Sex City 🏙️": "🌆 <b>The city's dark alleys revealed hidden wealth beyond imagination!</b>",
        "Fusha Village 🏞️": "🍃 <b>Nature's secrets became your fortune in this serene village!</b>",
        "Mystic Forest 🌲": "🌲 <b>Amidst the mystical fog, you found enchanted coins of power!</b>",
        "Dragon's Lair 🐉": "🔥 <b>Dodging flames, you emerged victorious with the dragon's hoard!</b>",
        "Pirate Cove 🏴‍☠️": "🏴‍☠️ <b>The pirates' gold is now safely in your hands. Well played!</b>",
        "Haunted Mansion 👻": "👻 <b>Even ghosts couldn't stop you from claiming the hidden treasure!</b>",
        "Enchanted Garden 🌸": "🌸 <b>The fairies' blessing gifted you a fortune of magical gold!</b>",
        "Lost City 🏙️": "🏙️ <b>The city's ruins concealed treasures beyond your wildest dreams!</b>",
        "Viking Stronghold ⚔️": "⚔️ <b>Victory over the Vikings left you with their legendary treasure chest!</b>",
        "Samurai Dojo 🥋": "🥋 <b>Honor and stealth helped you uncover the dojo's hidden gems!</b>",
        "Wizard Tower 🧙‍♂️": "🔮 <b>The wizard's lair rewarded you with mystical artifacts of great value!</b>",
        "Crystal Cave 💎": "💎 <b>You emerged from the cave with dazzling crystals and riches untold!</b>",
        "Mermaid Lagoon 🧜‍♀️": "🧜‍♀️ <b>Beneath the waves, you found the mermaids' hidden treasure trove!</b>",
        "Gnome Village 🧝": "🧝 <b>The gnomes shared their ancient gold, trusting your valor!</b>",
        "Fairy Forest 🧚": "🧚 <b>Fairies unveiled a secret stash of glittering wealth for you!</b>",
        "Goblin Camp 👺": "👺 <b>You raided the goblins' camp and escaped with their loot!</b>",
        "Minotaur Labyrinth 🐂": "🐂 <b>After outwitting the Minotaur, you claimed the labyrinth's treasure!</b>",
        "Phoenix Nest 🔥": "🔥 <b>Rising from the ashes, you secured a fiery bounty!</b>",
        "Treasure Island 🏝️": "🏝️ <b>The island's legendary treasure is now yours. X marks the spot indeed!</b>",
        "Jungle Temple 🏯": "🏯 <b>The temple's secrets revealed wealth beyond measure!</b>"
    }

    result_message = place_messages.get(exploration_place, f"✨ <b>You explored {exploration_place} and uncovered hidden riches!</b>")
    await callback_query.message.edit_text(f"{result_message}\n\n🎉 <b>You earned {random_reward} tokens! 💰</b>")
