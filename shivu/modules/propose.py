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
WIN_RATE_PERCENTAGE = 5  # Win rate in percentage
FIGHT_FEE = 200000  # Proposal fee
COOLDOWN_TIME = 600  # Cooldown time (10 minutes)
SPAM_THRESHOLD = 5  # Spam threshold in seconds
MUST_JOIN = 'dynamic_gangs'
OWNER_ID = 6402009857  # Owner ID

# Message Templates
START_MESSAGES = [
    "✨『𝑻𝒉𝒆 𝒎𝒐𝒎𝒆𝒏𝒕 𝒉𝒂𝒔 𝒂𝒓𝒓𝒊𝒗𝒆𝒅』✨",
    "💫『𝑳𝒆𝒕'𝒔 𝒈𝒐!』💫",
    "🌟『𝑻𝒊𝒎𝒆 𝒇𝒐𝒓 𝒚𝒐𝒖𝒓 𝒍𝒖𝒄𝒌𝒚 𝒔𝒉𝒐𝒕』🌟"
]
REJECTION_CAPTIONS = [
    "💔『𝑺𝒉𝒆 𝒔𝒍𝒂𝒑𝒑𝒆𝒅 𝒂𝒏𝒅 𝒓𝒂𝒏!』 😂",
    "💀『𝑺𝒉𝒆 𝒔𝒂𝒊𝒅 '𝒏𝒐'!』 😂",
    "😞『𝑺𝒐𝒓𝒓𝒚, 𝒃𝒖𝒕 𝒊𝒕'𝒔 𝒂 𝒓𝒆𝒋𝒆𝒄𝒕!』 😂"
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

# Track cooldowns and last command usage
user_cooldowns = {}
user_last_command_times = {}

# Fetch random characters with specific rarities
async def get_random_characters():
    target_rarities = ['🔮 Limited Edition', '💞 Valentine']
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Log user interaction to a group
async def log_interaction(user_id):
    group_id = -1001992198513  # Replace with your group ID
    await bot.send_message(group_id, f"👤 𝑼𝒔𝒆𝒓: {user_id} used the propose command at {datetime.now()}")

# Reset cooldown for a user (admin only)
@bot.on_message(filters.command("cd"))
async def reset_cooldown_command(_: bot, message: t.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("🚫 You lack permission to use this command.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to a user's message to reset their cooldown.")
    target_user_id = message.reply_to_message.from_user.id
    user_cooldowns.pop(target_user_id, None)
    await message.reply_text(f"✅ Cooldown reset for user {target_user_id}.")

# Propose Command with Cooldown and Retry
@bot.on_message(filters.command("propose"))
async def propose_command(_: bot, message: t.Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    current_time = time.time()

    # Check group membership
    try:
        await bot.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        link = f"https://t.me/{MUST_JOIN}"
        return await message.reply_text(
            "🔔 Join the support group to use this command!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=link)]]),
            disable_web_page_preview=True
        )

    # Group restriction check
    allowed_group_id = -1002104939708  # Replace with your group ID
    if chat_id != allowed_group_id:
        return await message.reply_text("⚠️ This command only works in @dynamic_gangs")

    # Cooldown check
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < COOLDOWN_TIME:
        remaining_time = COOLDOWN_TIME - (current_time - user_cooldowns[user_id])
        minutes, seconds = divmod(int(remaining_time), 60)
        return await message.reply_text(f"⏳ Cooldown active. Wait for {minutes}:{seconds}")

    # Spam prevention
    if user_id in user_last_command_times and current_time - user_last_command_times[user_id] < SPAM_THRESHOLD:
        return await message.reply_text("🚨 Command spam detected. Please wait.")

    # Balance check
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)
    if user_balance < FIGHT_FEE:
        return await message.reply_text("⚠️ Insufficient balance. You need 200,000 tokens.")

    # Deduct proposal fee
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -FIGHT_FEE}})
    user_cooldowns[user_id] = current_time
    user_last_command_times[user_id] = current_time

    # Log the interaction
    await log_interaction(user_id)

    # Proposal start message
    start_message = random.choice(START_MESSAGES)
    await bot.send_photo(chat_id, photo=random.choice(ACCEPTANCE_IMAGES), caption=start_message)

    # Animated steps of proposal
    for step in ["💍 Kneeling down...", "💞 Extending the ring...", "🎉 Asking the big question..."]:
        await message.reply_text(step)
        await asyncio.sleep(1)

    # Win/lose calculation
    if random.random() < (WIN_RATE_PERCENTAGE / 100):
        random_characters = await get_random_characters()
        for character in random_characters:
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        await asyncio.sleep(2)
        for character in random_characters:
            await message.reply_photo(
                photo=character['img_url'],
                caption=(f"😍 <b>{character['name']}</b> accepted! 🌹\n"
                         f"『𝑵𝒂𝒎𝒆』: {character['name']}\n"
                         f"『𝑹𝒂𝒓𝒊𝒕𝒚』: {character['rarity']}\n"
                         f"『𝑨𝒏𝒊𝒎𝒆』: {character['anime']}")
            )
        await message.reply_text(
            "💖 Try again or view your characters!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Retry Proposal", callback_data="retry_proposal")],
                [InlineKeyboardButton("📜 View Characters", url=f"https://t.me/{MUST_JOIN}")]
            ])
        )
    else:
        await asyncio.sleep(2)
        await message.reply_photo(
            photo=random.choice(REJECTION_IMAGES),
            caption=random.choice(REJECTION_CAPTIONS)
        )

# Retry proposal callback
@bot.on_callback_query(filters.regex("retry_proposal"))
async def retry_proposal(_, callback_query: t.CallbackQuery):
    await propose_command(_, callback_query.message)
