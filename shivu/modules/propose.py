from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from datetime import datetime
import random
import time

# Constants
SUCCESS_PROBABILITY = 0.15  # 15% success rate
PROPOSAL_COST = 180000  # Tokens required per proposal
COOLDOWN_DURATION = 7 * 60  # Cooldown of 7 minutes
ANTI_SPAM_TIME = 4  # Prevent spam: 4 seconds
MANDATORY_GROUP = "Dyna_community"  # Group user must join
ADMIN_ID = 6835013483  # Bot owner/admin

# Dynamic content
PROPOSAL_STEPS = [
    "✨ Preparing your speech...",
    "💌 Writing heartfelt words...",
    "💍 Presenting the ring..."
]
FAILURE_MESSAGES = [
    "💔 They walked away, leaving you in the rain... 🌧️",
    "😔 Not this time. Try again with more charm! 🪷",
    "🛑 A harsh 'NO!' echoes... but don't lose hope. 🌟"
]
SUCCESS_MESSAGES = [
    "🎉 They said YES! A magical journey begins! 🌹",
    "🌟 You won their heart! Cherish this bond forever! 💖",
    "💌 It's a perfect match! A bond written in the stars! ✨"
]
IMAGES = {
    "success": [
        "https://te.legra.ph/file/6e1234abcd5678ef9012.png",
        "https://te.legra.ph/file/09876cdeff56789a1234.png"
    ],
    "failure": [
        "https://te.legra.ph/file/bc12345ed67890ff1234.png",
        "https://te.legra.ph/file/abc67890def1234gh567.png"
    ]
}

# Cooldown and spam tracking
user_last_action = {}
cooldown_tracker = {}

# Get random characters
async def fetch_character():
    rarity_filter = ["🎀 Rare Edition", "✨ Ultra Rare"]
    return await collection.aggregate([
        {"$match": {"rarity": {"$in": rarity_filter}}},
        {"$sample": {"size": 1}}
    ]).to_list(length=1)

# Join group verification
async def verify_membership(user_id):
    try:
        await bot.get_chat_member(MANDATORY_GROUP, user_id)
    except UserNotParticipant:
        join_link = f"https://t.me/{MANDATORY_GROUP}"
        return False, join_link
    return True, None

# Log activity
async def record_action(user_id, description):
    log_group = -1001992198513
    await bot.send_message(log_group, f"📋 User {user_id} action: {description} at {datetime.now()}")

# Propose command
@bot.on_message(filters.command("propose"))
async def propose(_, message: Message):
    user_id = message.from_user.id
    target_user = message.reply_to_message.from_user if message.reply_to_message else None
    current_time = time.time()

    # Group membership check
    is_member, join_link = await verify_membership(user_id)
    if not is_member:
        return await message.reply_text(
            "📢 Please join our support group to use this feature!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Now", url=join_link)]])
        )

    # Cooldown validation
    if user_id in cooldown_tracker and current_time - cooldown_tracker[user_id] < COOLDOWN_DURATION:
        remaining = int(COOLDOWN_DURATION - (current_time - cooldown_tracker[user_id]))
        minutes, seconds = divmod(remaining, 60)
        return await message.reply_text(f"⏳ Cooldown active. Wait {minutes}m {seconds}s.")

    # Anti-spam
    if user_id in user_last_action and current_time - user_last_action[user_id] < ANTI_SPAM_TIME:
        return await message.reply_text("⚠️ You're sending commands too quickly!")

    # Check balance
    user_data = await user_collection.find_one({"id": user_id}, {"balance": 1})
    user_balance = user_data.get("balance", 0)
    if user_balance < PROPOSAL_COST:
        return await message.reply_text(f"💰 Not enough tokens! You need {PROPOSAL_COST}.")

    # Deduct cost and record cooldown
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -PROPOSAL_COST}})
    cooldown_tracker[user_id] = current_time
    user_last_action[user_id] = current_time

    # Log action
    await record_action(user_id, "Attempted proposal")

    # If targeting another user
    if target_user:
        accept_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💖 Accept", callback_data=f"accept_{user_id}_{target_user.id}"),
              InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{target_user.id}")]]
        )
        return await bot.send_message(
            target_user.id,
            f"💌 {message.from_user.mention} has proposed to you! Will you accept?",
            reply_markup=accept_button
        )

    # Single propose process
    for step in PROPOSAL_STEPS:
        await message.reply_text(step)
        await asyncio.sleep(1.5)

    # Outcome determination
    if random.random() < SUCCESS_PROBABILITY:
        # Successful proposal
        characters = await fetch_character()
        for char in characters:
            await user_collection.update_one({"id": user_id}, {"$push": {"characters": char}})
            await message.reply_photo(
                char["img_url"],
                caption=(
                    f"💖 Success! {char['name']} accepted your proposal! 🌹\n"
                    f"🏷️ **Rarity**: {char['rarity']}\n"
                    f"📺 **Anime**: {char['anime']}"
                )
            )
        await message.reply_text(
            random.choice(SUCCESS_MESSAGES),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="retry_proposal")],
                [InlineKeyboardButton("📂 View Collection", url=f"https://t.me/{MANDATORY_GROUP}")]
            ])
        )
    else:
        # Failed proposal
        await message.reply_photo(
            random.choice(IMAGES["failure"]),
            caption=random.choice(FAILURE_MESSAGES)
        )

# Callback for accept/reject
@bot.on_callback_query(filters.regex("accept_"))
async def accept_proposal(_, callback_query: t.CallbackQuery):
    data = callback_query.data.split("_")
    proposer_id = int(data[1])
    target_id = int(data[2])
    if callback_query.from_user.id != target_id:
        return await callback_query.answer("This proposal is not for you!", show_alert=True)
    await bot.send_message(proposer_id, f"🎉 {callback_query.from_user.mention} has accepted your proposal!")

@bot.on_callback_query(filters.regex("reject_"))
async def reject_proposal(_, callback_query: t.CallbackQuery):
    data = callback_query.data.split("_")
    proposer_id = int(data[1])
    target_id = int(data[2])
    if callback_query.from_user.id != target_id:
        return await callback_query.answer("This proposal is not for you!", show_alert=True)
    await bot.send_message(proposer_id, f"❌ {callback_query.from_user.mention} has rejected your proposal.")
