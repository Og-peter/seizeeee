from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
import os
from datetime import datetime

# Placeholder function for global rank
async def get_global_rank(user_id):
    # Implement logic to calculate global rank
    return await user_collection.count_documents({'id': {'$lt': user_id}})

# Placeholder function for user balance
async def get_user_balance(user_id):
    user = await user_collection.find_one({'id': user_id})
    return user.get('balance', 0) if user else 0

# Placeholder function for calculating user level
def calculate_user_level(xp):
    return xp // 100  # Example logic

# Function to get detailed user information
async def get_user_info(user, already=False):
    try:
        if not already:
            user = await shivuu.get_users(user)
        if not user.first_name:
            return ["Deleted account", None]

        user_id = user.id
        existing_user = await user_collection.find_one({'id': user_id})
        if not existing_user:
            return ["User not found in the database.", None]

        first_name = user.first_name
        global_rank = await get_global_rank(user_id)
        global_count = await collection.count_documents({})
        total_count = len(existing_user.get('characters', []))
        photo_id = user.photo.big_file_id if user.photo else None
        balance = await get_user_balance(user_id)
        global_coin_rank = await user_collection.count_documents({'balance': {'$gt': balance}}) + 1
        xp = existing_user.get('xp', 0)
        level = calculate_user_level(xp)
        current_login = datetime.now()
        last_login_date = existing_user.get('last_login')
        streak = existing_user.get('login_streak', 0) if last_login_date else 1

        # Update login info and streak logic
        await user_collection.update_one({'id': user_id}, {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}})

        # Formatting data
        tokens = existing_user.get('tokens', 0)
        tokens_formatted = f"{tokens:,}"
        balance_formatted = f"{balance:,}"

        # Profile display
        info_text = f"""
╭─★ User's Profile ★─╮
┃
┣ 👤 **Name:** {first_name}
┣ 🆔 **ID:** `{user_id}`
┃
┣━━━━━━━━━━━━━━━━━
┣ 🌟 **Total Waifus:** {total_count} / {global_count}
┣ 📊 **Waifu Percentage:** `{round((total_count / global_count) * 100, 2)}%`
┣ 📈 **Level:** `{level}`
┣ 🎮 **XP:** `{xp}`
┣ 💰 **Tokens:** `{tokens_formatted}`
┃
┣ 🏆 **Global Position:** `{global_rank}`
┣ 🌐 **Chat Position:** `{global_coin_rank}`
┣ 🔥 **Login Streak:** {streak} days
┃
╰──────────────────╯
"""
        return info_text, photo_id
    except Exception as e:
        print(f"Error in get_user_info: {e}")
        return ["Error fetching user information.", None]

# Command to show user profile/status
@shivuu.on_message(filters.command("status"))
async def profile(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif len(message.command) == 1:
        user = message.from_user.id
    else:
        user = message.text.split(None, 1)[1]

    m = await message.reply_text("✨ Fetching Your Hunter License...")

    try:
        info_text, photo_id = await get_user_info(user)
    except Exception as e:
        import traceback
        print(f"Something went wrong: {e}\n{traceback.format_exc()}")
        return await m.edit(f"❌ Sorry, something went wrong. Report at @{SUPPORT_CHAT}.")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")]
    ])
    
    if photo_id is None:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    
    try:
        photo = await shivuu.download_media(photo_id)
        await message.reply_photo(photo, caption=info_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error downloading photo: {e}")
        await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    finally:
        if os.path.exists(photo):
            os.remove(photo)
    await m.delete()
