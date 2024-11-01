from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
from datetime import datetime

# Global rank based on user balance
async def get_global_rank(user_id):
    user_balance = await get_user_balance(user_id)
    higher_balance_count = await user_collection.count_documents({'balance': {'$gt': user_balance}})
    return higher_balance_count + 1

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
    filled_bars = int(progress_percentage // 10)  # Number of "filled" segments
    empty_bars = 10 - filled_bars  # Number of "empty" segments
    return "▰" * filled_bars + "▱" * empty_bars

async def get_user_info(user, already=False):
    try:
        # Ensure user is fetched if `already` is False
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
        total_waifus = len(existing_user.get('characters', []))
        total_characters = await collection.count_documents({})
        custom_photo = existing_user.get('custom_photo')
        balance = await get_user_balance(user_id)
        xp = existing_user.get('xp', 0)
        level = calculate_user_level(xp)
        progress_bar = generate_character_progress_bar(total_waifus, total_characters)
        current_login = datetime.now()
        last_login_date = existing_user.get('last_login')
        streak = existing_user.get('login_streak', 0) + 1 if last_login_date else 1

        # Update last login and streak in the database
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}}
        )

        # Profile Information Message Formatting with user mention and progress bar
        info_text = f"""
┌───⦿ **Hunter License** ⦿───┐
│ **Name:** [{first_name}](tg://user?id={user_id})
│ **User ID:** `{user_id}`
│ **Total Waifus:** {total_waifus}/{total_characters}
│ **Waifu Percentage:** `{round((total_waifus / total_characters) * 100, 2)}%`
│ **Progress:** `{progress_bar}` ({total_waifus}/{total_characters})
│ **Level:** `{level}`
│ **XP:** `{xp}`
│ **Global Position:** `{global_rank}`
│ **Login Streak:** `{streak} days`
│
│ You can set your favorite profile picture using `/setpic` by replying to an image.
└─────────────────────────────┘
"""

        return info_text.strip(), custom_photo
    except Exception as e:
        print(f"⚠️ Error in get_user_info: {e}")
        return ["⚠️ Error fetching user information.", None]

@shivuu.on_message(filters.command("status"))
async def profile(client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif len(message.command) == 1:
        user = message.from_user.id
    else:
        user = message.text.split(None, 1)[1]

    m = await message.reply_text("✨ Fetching Your Hunter License...")

    try:
        info_text, custom_photo = await get_user_info(user)
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
        await m.delete()  # Delete the loading message before sending the photo
        await message.reply_photo(custom_photo, caption=info_text, reply_markup=keyboard)
    except Exception as e:
        print(f"⚠️ Error displaying custom photo: {e}")
        await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)

@shivuu.on_message(filters.command("setpic") & filters.reply)
async def set_profile_pic(client, message: Message):
    # Check if the reply has a photo, video, sticker, or animation (GIF)
    if message.reply_to_message.photo:
        custom_media_id = message.reply_to_message.photo.file_id
    elif message.reply_to_message.video:
        custom_media_id = message.reply_to_message.video.file_id
    elif message.reply_to_message.sticker:
        custom_media_id = message.reply_to_message.sticker.file_id
    elif message.reply_to_message.animation:  # This is for GIFs
        custom_media_id = message.reply_to_message.animation.file_id
    else:
        return await message.reply_text("⚠️ Please reply with a photo, video, sticker, or GIF to set it as your profile picture.")
    
    user_id = message.from_user.id

    # Save the custom media ID to the user's document in the database
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'custom_photo': custom_media_id}},
        upsert=True
    )
    await message.reply_text("✅ Profile picture has been set successfully!")
