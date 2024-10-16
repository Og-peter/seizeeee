from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
import os
from datetime import datetime, timedelta
import random

# Function to get all user collections
async def get_user_collection():
    return await user_collection.find({}).to_list(length=None)

# Function to get the global rank of a user
async def get_global_rank(user_id: int) -> int:
    pipeline = [
        {"$project": {
            "id": 1,
            "characters_count": {"$cond": {"if": {"$isArray": "$characters"}, "then": {"$size": "$characters"}, "else": 0}}
        }},
        {"$sort": {"characters_count": -1}}
    ]
    
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('id') == user_id:
            return i
    
    return 0

# Function to get the balance of a user
async def get_user_balance(user_id: int) -> int:
    user_balance = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    if user_balance:
        return user_balance.get('balance', 0)
    else:
        return 0

# Function to calculate user level based on experience points (XP)
def calculate_user_level(xp: int) -> int:
    return int(xp ** 0.5)  # Example level calculation formula based on square root of XP

# Function to get detailed user information
async def get_user_info(user, already=False):
    if not already:
        user = await shivuu.get_users(user)
    if not user.first_name:
        return ["Deleted account", None]

    user_id = user.id
    username = user.username
    existing_user = await user_collection.find_one({'id': user_id})
    first_name = user.first_name
    mention = user.mention("Link")
    global_rank = await get_global_rank(user_id)
    global_count = await collection.count_documents({})
    total_count = len(existing_user.get('characters', []))
    photo_id = user.photo.big_file_id if user.photo else None
    balance = await get_user_balance(user_id)
    global_coin_rank = await user_collection.count_documents({'balance': {'$gt': balance}}) + 1
    xp = existing_user.get('xp', 0)
    level = calculate_user_level(xp)
    last_login = existing_user.get('last_login', 'Unknown')
    
    # Calculate rarity counts
    rarity_counts = {
        "🫧 Premium": 0,
        "💮 Exclusive": 0,
        "🔮 Limited Edition": 0,
        "🌸 Exotic": 0,
        "👶 Chibi": 0,
        "🟡 Legendary": 0,
        "🟠 Rare": 0,
        "🔵 Medium": 0,
        "⚪️ Common": 0,
        "🎐 Astral": 0,
        "💞 Valentine": 0
    }

    for char in existing_user.get('characters', []):
        rarity = char.get('rarity', '⚪️ Common')
        if rarity in rarity_counts:
            rarity_counts[rarity] += 1

    rarity_message = "\n".join([
        f"⌠{rarity.split()[0]}⌡ Rarity: {' '.join(rarity.split()[1:])}: {count}"
        for rarity, count in rarity_counts.items()
    ])

    has_pass = "✅" if existing_user.get('pass') else "❌"
    tokens = existing_user.get('tokens', 0)
    
    # Format balance and tokens with commas
    balance_formatted = f"{balance:,}"
    tokens_formatted = f"{tokens:,}"

    # Additional achievements and badges (example)
    badges = []
    if total_count > 100:
        badges.append("🎖 Character Master")
    if balance > 100000:
        badges.append("💰 Wealthy Hunter")
    badges_message = " | ".join(badges) if badges else "No badges earned yet."

    # Adding login streak feature
    current_login = datetime.now()
    last_login_date = existing_user.get('last_login')
    if last_login_date:
        last_login_date = datetime.strptime(last_login_date, '%Y-%m-%d')
        streak = existing_user.get('login_streak', 0)
        if (current_login - last_login_date).days == 1:
            streak += 1  # Increment streak
        elif (current_login - last_login_date).days > 1:
            streak = 1  # Reset streak
    else:
        streak = 1  # First login

    # Update login info
    await user_collection.update_one({'id': user_id}, {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}})

    info_text = f"""
「 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 」
───────────────────
✨ {first_name}  [`{user_id}`]
🌐 𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀 : @{username}
───────────────────
📜 𝘾𝙃𝘼𝙍𝘼𝘾𝙏𝙀𝙍𝙎 𝗖𝗢𝗨𝗡𝗧 : `{total_count}` / `{global_count}`
🏆 𝙂𝙇𝙊𝘽𝘼𝙇 𝙍𝘼𝙉𝙆 : `{global_rank}`
───────────────────
💸 𝙒𝙀𝘼𝙇𝙏𝙃 : ₩`{balance_formatted}`
🔱 𝙂𝙇𝙊𝘽𝘼𝙇 𝙒𝙀𝘼𝙇𝙏𝙃 𝙍𝘼𝙉𝙆  : `{global_coin_rank}`
───────────────────
🎮 𝙇𝙀𝙑𝙀𝙇 : `{level}` | 𝙓𝙋 : `{xp}`
🔥 𝙇𝙊𝙂𝙄𝙉 𝙎𝙏𝙍𝙀𝘼𝙆 : {streak} days
───────────────────
🎖 𝘼𝘾𝙃𝙄𝙀𝙑𝙀𝙈𝙀𝙉𝙏𝙎 : {badges_message}
───────────────────
{rarity_message}
"""
    return info_text, photo_id

# Command to show user profile/status
@shivuu.on_message(filters.command("status"))
async def profile(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif not message.reply_to_message and len(message.command) == 1:
        user = message.from_user.id
    elif not message.reply_to_message and len(message.command) != 1:
        user = message.text.split(None, 1)[1]
    
    existing_user = await user_collection.find_one({'id': user})
    m = await message.reply_text("✨ Fetching Your Hunter License...")

    try:
        info_text, photo_id = await get_user_info(user)
    except Exception as e:
        print(f"Something went wrong: {e}")
        return await m.edit(f"❌ Sorry, something went wrong. Report at @{SUPPORT_CHAT}.")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")]
    ])
    
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Start Me in PM First", url=f"https://t.me/{shivuu.me.username}?start=True")]
        ]
    )
    
    if photo_id is None:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    elif not existing_user:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=reply_markup)
    
    photo = await shivuu.download_media(photo_id)
    await message.reply_photo(photo, caption=info_text, reply_markup=keyboard)
    await m.delete()
    os.remove(photo)

# Fetch the user from the database
existing_user = await user_collection.find_one({'id': user_id})

# Now you can safely use existing_user
custom_photo = existing_user.get('profile_pic') if existing_user else None

# Use custom profile picture if it exists, otherwise use the Telegram photo
if custom_photo:
    photo_id = custom_photo
else:
    photo_id = user.photo.big_file_id if user.photo else None

@shivuu.on_message(filters.command("setpfp") & filters.reply)
async def set_profile_pic(client, message):
    if message.reply_to_message.photo:
        photo_id = message.reply_to_message.photo.file_id
        user_id = message.from_user.id
        
        # Save the profile picture in the database
        await user_collection.update_one({'id': user_id}, {'$set': {'profile_pic': photo_id}}, upsert=True)
        
        await message.reply_text("✅ Custom profile picture set successfully!")
    else:
        await message.reply_text("❌ Please reply to a photo to set it as your profile picture.")
