from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from datetime import datetime, timedelta
import random
import time

# Constants
WIN_RATE_PERCENTAGE = 5  # Set the win rate percentage here
FIGHT_FEE = 200000  # Set the fee for the propose command
COOLDOWN_TIME = 600  # Cooldown time in seconds (10 minutes)
SPAM_THRESHOLD = 5  # Time between successive commands to prevent spamming
MUST_JOIN = 'dynamic_gangs'
OWNER_ID = 6402009857  # Replace with the actual owner ID

# Message Templates
START_MESSAGES = [
    "✨ Finally, the time has come ✨",
    "💫 The moment you've been waiting for 💫",
    "🌟 The stars align for this proposal 🌟"
]
REJECTION_CAPTIONS = [
    "💔 She slapped you and ran away! 😂",
    "💀 She rejected you outright! 😂",
    "😞 You got a harsh 'NO!' 😂"
]
ACCEPTANCE_IMAGES = [
    "https://te.legra.ph/file/4fe133737bee4866a3549.png",
    "https://te.legra.ph/file/28d46e4656ee2c3e7dd8f.png",
    "https://te.legra.ph/file/d32c6328c6d271dd00816.png"
]
REJECTION_IMAGES = [
    "https://te.legra.ph/file/d6e784e5cda62ac27541f.png",
    "https://te.legra.ph/file/e4e1ba60b4e79359bf9e7.png",
    "https://te.legra.ph/file/81d011398da3a6f49fa7f.png"
]

# Track user cooldowns and last command times
user_cooldowns = {}
user_last_command_times = {}

# Function to fetch random characters from the database
async def get_random_characters():
    target_rarities = ['🔮 Limited Edition', '💞 Valentine']
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Function to log user interaction
async def log_interaction(user_id):
    group_id = -1001992198513  # Replace with your group ID
    await bot.send_message(group_id, f"User {user_id} used the propose command at {datetime.now()}")

# Command to reset cooldown for a user
@bot.on_message(filters.command("cd"))
async def reset_cooldown_command(_: bot, message: t.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("🚫 You do not have permission to use this command.")

    if not message.reply_to_message:
        return await message.reply_text("❌ You must reply to a user's message to reset their cooldown.")

    target_user_id = message.reply_to_message.from_user.id
    user_cooldowns.pop(target_user_id, None)
    await message.reply_text(f"✅ Cooldown for user {target_user_id} has been reset.")

# Command for proposing
@bot.on_message(filters.command("propose"))
async def propose_command(_: bot, message: t.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    current_time = time.time()

    # Check if user is a member of the required group/channel
    try:
        await bot.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        link = f"https://t.me/{MUST_JOIN}"
        return await message.reply_text(
            "🔔 You must join the support group/channel to use this command.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=link)]]),
            disable_web_page_preview=True
        )

    # Ensure command is only used in the allowed group
    allowed_group_id = -1002104939708  # Replace with your group ID
    if chat_id != allowed_group_id:
        return await message.reply_text("⚠️ This command only works in @dynamic_gangs")

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < COOLDOWN_TIME:
        remaining_time = COOLDOWN_TIME - (current_time - user_cooldowns[user_id])
        minutes, seconds = divmod(int(remaining_time), 60)
        return await message.reply_text(f"⏳ You're on cooldown. Please wait for {minutes}:{seconds}.")

    # Prevent command spamming
    if user_id in user_last_command_times and current_time - user_last_command_times[user_id] < SPAM_THRESHOLD:
        return await message.reply_text("🚨 You're sending commands too quickly. Please wait.")

    # Deduct the fight fee from the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)
    if user_balance < FIGHT_FEE:
        return await message.reply_text("⚠️ You don't have enough tokens to proceed. You need 200,000.")

    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -FIGHT_FEE}})
    user_cooldowns[user_id] = current_time
    user_last_command_times[user_id] = current_time

    # Log user interaction
    await log_interaction(user_id)

    # Send initial proposal message
    start_message = random.choice(START_MESSAGES)
    photo_path = random.choice(ACCEPTANCE_IMAGES)
    await bot.send_photo(chat_id, photo=photo_path, caption=start_message)

    # Animated proposal message
    animated_steps = [
        "💍 Getting down on one knee...",
        "💞 Holding out the ring...",
        "🎉 Preparing for the big question..."
    ]
    for step in animated_steps:
        await message.reply_text(step)
        await asyncio.sleep(1)

    # Handle win/lose logic
    if random.random() < (WIN_RATE_PERCENTAGE / 100):
        random_characters = await get_random_characters()
        for character in random_characters:
            try:
                await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
            except Exception as e:
                print(f"Error updating user characters: {e}")

        await asyncio.sleep(2)
        img_urls = [character['img_url'] for character in random_characters]
        captions = [
            f"😍 <b>{character['name']}</b> has accepted your proposal! 😇\n"
            f"Name: {character['name']}\n"
            f"Rarity: {character['rarity']}\n"
            f"Anime: {character['anime']}\n"
            for character in random_characters
        ]

        for img_url, caption in zip(img_urls, captions):
            await message.reply_photo(photo=img_url, caption=caption)

        # Send retry option
        await message.reply_text(
            "💖 Want to try again or view your characters?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Retry Proposal", callback_data="retry_proposal")],
                [InlineKeyboardButton("📜 View Characters", url=f"https://t.me/{MUST_JOIN}")]
            ])
        )
    else:
        await asyncio.sleep(2)
        rejection_caption = random.choice(REJECTION_CAPTIONS)
        rejection_image = random.choice(REJECTION_IMAGES)
        await message.reply_photo(photo=rejection_image, caption=rejection_caption)

# Callback handler for retry proposal
@bot.on_callback_query(filters.regex("retry_proposal"))
async def retry_proposal(_, callback_query: t.CallbackQuery):
    await propose_command(_, callback_query.message)
