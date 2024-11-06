from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import shivuu, SUPPORT_CHAT, user_collection, collection
from datetime import datetime

# Fetch user's balance from the database
async def fetch_user_balance(user_id):
    user_data = await user_collection.find_one({"id": user_id})
    return user_data.get("balance", 0) if user_data else 0

# Calculate user level from XP
def calculate_level(xp):
    return xp // 100

# Generate a visual progress bar for character collection
def create_progress_bar(current, total):
    percentage = (current / total) * 100 if total > 0 else 0
    filled = int(percentage // 10)
    return "▰" * filled + "▱" * (10 - filled)

# Count character rarities in user collection
async def rarity_counter(character_list):
    rarity_map = {
        "Common": "⚪️", "Limited Edition": "🔮", "Premium": "🫧", "Exotic": "🌸",
        "Exclusive": "💮", "Chibi": "👶", "Legendary": "🟡", "Rare": "🟠",
        "Medium": "🔵", "Astral": "🎐", "Valentine": "💞"
    }
    rarity_counts = {rarity: 0 for rarity in rarity_map}

    for char in character_list:
        rarity = char.get("rarity", "Common")
        if rarity in rarity_counts:
            rarity_counts[rarity] += 1

    return {rarity: f"{emoji} {rarity}: {count}" for rarity, count in rarity_counts.items() if count > 0}

# Get global ranking for the user based on waifu count
async def fetch_global_rank(user_id):
    users = await user_collection.find({"total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    for rank, user in enumerate(users):
        if user["id"] == user_id:
            return rank + 1
    return None

# Get rank within a specific chat
async def fetch_chat_rank(user_id, chat_id):
    chat_users = await user_collection.find({"chat_id": chat_id, "total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    for rank, user in enumerate(chat_users):
        if user["id"] == user_id:
            return rank + 1
    return None

# Retrieve detailed user information for display
async def retrieve_user_info(user_id, chat_id, user_obj=None):
    user_data = await shivuu.get_users(user_id) if not user_obj else user_obj

    if not user_data or not user_data.first_name:
        return "⚠️ Deleted or Unknown User", None

    user_id = user_data.id
    stored_data = await user_collection.find_one({'id': user_id})
    if not stored_data:
        return "⚠️ User not found in the database.", None

    total_characters = await collection.count_documents({})
    waifu_count = len(stored_data.get("characters", []))
    progress_bar = create_progress_bar(waifu_count, total_characters)
    rarity_summary = await rarity_counter(stored_data.get("characters", []))
    
    rank_global = await fetch_global_rank(user_id)
    rank_chat = await fetch_chat_rank(user_id, chat_id)
    balance = await fetch_user_balance(user_id)
    xp = stored_data.get("xp", 0)
    level = calculate_level(xp)

    last_login = stored_data.get("last_login")
    current_login = datetime.now()
    streak = stored_data.get("login_streak", 0) + 1 if last_login else 1

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}}
    )

    rarity_text = "\n".join(rarity_summary.values())
    profile_info = f"""
┌───⦿ **User Profile** ⦿───┐
│ 👤 **Name:** [{user_data.first_name}](tg://user?id={user_id})
│ 🆔 **User ID:** `{user_id}`
│ 🍀 **Waifus Collected:** {waifu_count}/{total_characters}
│ 📊 **Progress Bar:** `{progress_bar}`
│ 🎖 **Level:** {level}
│
│ 🌟 **Rarities:**
{rarity_text}
│
│ 🌍 **Global Rank:** {rank_global or 'N/A'}
│ 🍃 **Chat Rank:** {rank_chat or 'N/A'}
└─────────────────────────────┘
"""

    return profile_info.strip(), stored_data.get("custom_photo"), stored_data.get("custom_media_type", "photo")

# Command handler to show user profile
@shivuu.on_message(filters.command("status"))
async def show_profile(client, message: Message):
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id

    loading_msg = await message.reply_text("Fetching profile information...")

    profile_text, media_id, media_type = await retrieve_user_info(user_id, chat_id)

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

# Command handler to set profile picture
@shivuu.on_message(filters.command("setpic") & filters.reply)
async def update_profile_picture(client, message: Message):
    reply = message.reply_to_message
    user_id = message.from_user.id

    if reply.photo:
        media_id, media_type = reply.photo.file_id, "photo"
    elif reply.video:
        media_id, media_type = reply.video.file_id, "video"
    elif reply.sticker:
        media_id, media_type = reply.sticker.file_id, "sticker"
    elif reply.animation:
        media_id, media_type = reply.animation.file_id, "animation"
    else:
        return await message.reply_text("⚠️ Please reply with a supported media (photo, video, sticker, or GIF).")

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'custom_photo': media_id, 'custom_media_type': media_type}},
        upsert=True
    )

    await message.reply_text("✅ Profile picture updated successfully!")
