from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
from datetime import datetime

# Fetch user balance from the database
async def get_user_balance(user_id):
    user = await user_collection.find_one({"id": user_id})
    return user.get("balance", 0) if user else 0

# Calculate user level based on XP
def calculate_user_level(xp):
    return xp // 100

# Generate a progress bar based on characters collected
def generate_character_progress_bar(total_waifus, total_characters):
    progress_percentage = (total_waifus / total_characters) * 100 if total_characters > 0 else 0
    filled_bars = int(progress_percentage // 10)
    empty_bars = 10 - filled_bars
    return "▰" * filled_bars + "▱" * empty_bars

# Count rarities in user's collection
async def count_rarities(characters):
    rarities = {
        "Common": {"count": 0, "emoji": "⚪️"},
        "Limited Edition": {"count": 0, "emoji": "🔮"},
        "Premium": {"count": 0, "emoji": "🫧"},
        "Exotic": {"count": 0, "emoji": "🌸"},
        "Exclusive": {"count": 0, "emoji": "💮"},
        "Chibi": {"count": 0, "emoji": "👶"},
        "Legendary": {"count": 0, "emoji": "🟡"},
        "Rare": {"count": 0, "emoji": "🟠"},
        "Medium": {"count": 0, "emoji": "🔵"},
        "Astral": {"count": 0, "emoji": "🎐"},
        "Valentine": {"count": 0, "emoji": "💞"}
    }

    for character in characters:
        rarity = character.get("rarity", "Common")  # Default to "Common" if not specified
        if rarity in rarities:
            rarities[rarity]["count"] += 1

    return {rarity: data for rarity, data in rarities.items() if data["count"] > 0}

# Calculate global rank based on waifu count
async def get_global_rank(user_id):
    all_users = await user_collection.find({"total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    for idx, user in enumerate(all_users):
        if user["id"] == user_id:
            return idx + 1
    return None

# Calculate chat rank based on waifu count within the current chat
async def get_chat_rank(user_id, chat_id):
    chat_users = await user_collection.find({"chat_id": chat_id, "total_waifus": {"$exists": True}}).sort("total_waifus", -1).to_list(None)
    for idx, user in enumerate(chat_users):
        if user["id"] == user_id:
            return idx + 1
    return None

async def get_user_info(user, chat_id, already=False):
    try:
        if not already:
            user = await shivuu.get_users(user)
        if not user or not user.first_name:
            return ["⚠️ Deleted account", None]

        user_id = user.id
        existing_user = await user_collection.find_one({'id': user_id})
        if not existing_user:
            return ["⚠️ User not found in the database.", None]

        first_name = user.first_name
        global_rank = await get_global_rank(user_id)
        chat_rank = await get_chat_rank(user_id, chat_id)
        total_waifus = len(existing_user.get('characters', []))
        total_characters = await collection.count_documents({})
        custom_photo = existing_user.get('custom_photo')
        media_type = existing_user.get('custom_media_type', 'photo')
        balance = await get_user_balance(user_id)
        xp = existing_user.get('xp', 0)
        level = calculate_user_level(xp)
        progress_bar = generate_character_progress_bar(total_waifus, total_characters)
        current_login = datetime.now()
        last_login_date = existing_user.get('last_login')
        streak = existing_user.get('login_streak', 0) + 1 if last_login_date else 1

        rarities = await count_rarities(existing_user.get('characters', []))

        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}}
        )

        rarity_text = "\n".join(
            [f"{data['emoji']} {rarity}: {data['count']}" for rarity, data in rarities.items()]
        )

        info_text = f"""
┌───⦿ **Grabber Status** ⦿───┐
│ 🧑‍💼 **User:** [{first_name}](tg://user?id={user_id})
│ 🆔 **User ID:** `{user_id}`
│ 🍀 **Total Waifus:** {total_waifus}/{total_characters}
│ 🏆 **Harem:** {total_waifus}/{total_characters} ({round((total_waifus / total_characters) * 100, 2)}%)
│ 📚 **Experience Level:** {level}
│ 📊 **Progress Bar:** `{progress_bar}`
│
│ 🌟 **Rarity:** 
{rarity_text}
│
│ 🌍 **Position Globally:** {global_rank or 'N/A'}
│ 🍃 **Chat Position:** {chat_rank or 'N/A'}
└─────────────────────────────┘
"""

        return info_text.strip(), custom_photo, media_type
    except Exception as e:
        print(f"⚠️ Error in get_user_info: {e}")
        return ["⚠️ Error fetching user information.", None, 'photo']

@shivuu.on_message(filters.command("status"))
async def profile(client, message: Message):
    user = None
    chat_id = message.chat.id
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif len(message.command) == 1:
        user = message.from_user.id
    else:
        user = message.text.split(None, 1)[1]

    m = await message.reply_text("✨ Fetching Your Grabber Status...")

    try:
        info_text, custom_photo, media_type = await get_user_info(user, chat_id)
    except Exception as e:
        import traceback
        print(f"❌ Something went wrong: {e}\n{traceback.format_exc()}")
        return await m.edit(f"⚠️ Sorry, something went wrong. Please report at @{SUPPORT_CHAT}.")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")]
    ])
    
    if custom_photo is None:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    
    try:
        await m.delete()
        if media_type == "photo":
            await message.reply_photo(custom_photo, caption=info_text, reply_markup=keyboard)
        elif media_type == "video":
            await message.reply_video(custom_photo, caption=info_text, reply_markup=keyboard)
        elif media_type == "animation":
            await message.reply_animation(custom_photo, caption=info_text, reply_markup=keyboard)
        elif media_type == "sticker":
            await message.reply_sticker(custom_photo)
            await message.reply_text(info_text, reply_markup=keyboard)
    except Exception as e:
        print(f"⚠️ Error displaying custom media: {e}")
        await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)

@shivuu.on_message(filters.command("setpic") & filters.reply)
async def set_profile_pic(client, message: Message):
    # Check if the reply message contains a media type we support
    if message.reply_to_message.photo:
        custom_media_id = message.reply_to_message.photo.file_id
        media_type = "photo"
    elif message.reply_to_message.video:
        custom_media_id = message.reply_to_message.video.file_id
        media_type = "video"
    elif message.reply_to_message.sticker:
        custom_media_id = message.reply_to_message.sticker.file_id
        media_type = "sticker"
    elif message.reply_to_message.animation:
        custom_media_id = message.reply_to_message.animation.file_id
        media_type = "animation"
    else:
        # If no valid media type is found, prompt the user to reply with supported media
        return await message.reply_text("⚠️ Please reply with a photo, video, sticker, or GIF to set it as your profile picture.")

    user_id = message.from_user.id

    # Update the user's custom profile picture and media type in the database
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'custom_photo': custom_media_id, 'custom_media_type': media_type}},
        upsert=True
    )
    
    # Confirm to the user that the profile picture has been updated
    await message.reply_text("✅ Your profile picture has been set successfully!")
