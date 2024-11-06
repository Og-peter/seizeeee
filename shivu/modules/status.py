from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu, SUPPORT_CHAT, user_collection, collection
from datetime import datetime

# Retrieve or initialize user balance
async def get_user_balance(user_id):
    user = await user_collection.find_one({"id": user_id})
    return user.get("balance", 0) if user else 0

# XP and Level Calculator
def calculate_level(xp):
    return xp // 120

# Progress bar generator for collection tracking
def progress_bar(current, total, length=10):
    filled_length = int((current / total) * length) if total > 0 else 0
    return "⬜" * filled_length + "⬛" * (length - filled_length)

# Rarity Counter for user's character collection (display all rarities)
async def rarity_summary(characters):
    rarity_icons = {
        "Common": "⚪️", "Limited": "🔮", "Premium": "🫧", "Exotic": "🌸",
        "Exclusive": "💮", "Chibi": "👶", "Legendary": "🟡", "Rare": "🟠",
        "Medium": "🔵", "Astral": "🎐", "Valentine": "💞"
    }
    rarity_count = {rarity: 0 for rarity in rarity_icons}

    for char in characters:
        rarity = char.get("rarity", "Common")
        if rarity in rarity_count:
            rarity_count[rarity] += 1

    return "\n".join(f"{emoji} {rarity}: {count}" for rarity, count in rarity_count.items())

# Fetch global rank based on waifu count
async def global_rank(user_id):
    users = await user_collection.find({"total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    return next((rank + 1 for rank, user in enumerate(users) if user["id"] == user_id), "N/A")

# Fetch chat-specific rank
async def chat_rank(user_id, chat_id):
    chat_users = await user_collection.find({"chat_id": chat_id, "total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    return next((rank + 1 for rank, user in enumerate(chat_users) if user["id"] == user_id), "N/A")

# Retrieve and display profile info
async def profile_info(user_id, chat_id):
    user = await shivuu.get_users(user_id)
    if not user or not user.first_name:
        return "⚠️ User not found.", None

    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        return "⚠️ User not found in the database.", None

    waifu_count = len(user_data.get("characters", []))
    total_characters = await collection.count_documents({})
    progress = progress_bar(waifu_count, total_characters)
    rarity_stats = await rarity_summary(user_data.get("characters", []))

    rank_global = await global_rank(user_id)
    rank_chat = await chat_rank(user_id, chat_id)
    balance = await get_user_balance(user_id)
    xp = user_data.get("xp", 0)
    level = calculate_level(xp)

    last_login = user_data.get("last_login")
    streak = user_data.get("login_streak", 0) + 1 if last_login else 1
    await user_collection.update_one({'id': user_id}, {'$set': {'last_login': datetime.now(), 'login_streak': streak}})

    profile_text = f"""
**User Profile**
👤 **Name:** [{user.first_name}](tg://user?id={user_id})
🆔 **ID:** `{user_id}`
💰 **Balance:** {balance}
🕹 **Waifus:** {waifu_count}/{total_characters}
📊 **Progress:** `{progress}`
🌟 **Level:** {level}
📈 **Rarities:**
{rarity_stats}

🌍 **Global Rank:** {rank_global}
🌿 **Chat Rank:** {rank_chat}
"""

    media_id = user_data.get("custom_photo")
    media_type = user_data.get("custom_media_type", "photo")

    return profile_text.strip(), media_id, media_type

# Display user profile with media and buttons
@shivuu.on_message(filters.command("status"))
async def show_profile(client, message: Message):
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id
    chat_id = message.chat.id
    loading_msg = await message.reply_text("🔍 Loading profile...")

    profile_text, media_id, media_type = await profile_info(user_id, chat_id)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")]
    ])

    await loading_msg.delete()

    try:
        if media_id:
            if media_type == "photo":
                await message.reply_photo(media_id, caption=profile_text, reply_markup=buttons)
            elif media_type == "video":
                await message.reply_video(media_id, caption=profile_text, reply_markup=buttons)
            elif media_type == "animation":
                await message.reply_animation(media_id, caption=profile_text, reply_markup=buttons)
            elif media_type == "sticker":
                await message.reply_sticker(media_id)
                await message.reply_text(profile_text, reply_markup=buttons)
        else:
            await message.reply_text(profile_text, disable_web_page_preview=True, reply_markup=buttons)
    except Exception as e:
        print(f"Error displaying media: {e}")
        await message.reply_text(profile_text, disable_web_page_preview=True, reply_markup=buttons)

# Command to set user profile picture with supported media
@shivuu.on_message(filters.command("setpic") & filters.reply)
async def set_profile_pic(client, message: Message):
    reply = message.reply_to_message
    user_id = message.from_user.id

    media = None
    if reply.photo:
        media, media_type = reply.photo.file_id, "photo"
    elif reply.video:
        media, media_type = reply.video.file_id, "video"
    elif reply.animation:
        media, media_type = reply.animation.file_id, "animation"
    elif reply.sticker:
        media, media_type = reply.sticker.file_id, "sticker"

    if not media:
        return await message.reply_text("⚠️ Reply with an image, video, GIF, or sticker.")

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'custom_photo': media, 'custom_media_type': media_type}},
        upsert=True
    )
    await message.reply_text("✅ Profile picture updated successfully!")
