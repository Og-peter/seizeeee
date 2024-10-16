from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
import os
from datetime import datetime

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
    return 0

# Function to calculate user level based on experience points (XP)
def calculate_user_level(xp: int) -> int:
    return int(xp ** 0.5)  # Level calculation based on square root of XP

# Function to get detailed user information
async def get_user_info(user_id: int):
    user = await shivuu.get_users(user_id)
    if not user.first_name:
        return "Deleted account", None

    existing_user = await user_collection.find_one({'id': user_id})
    first_name = user.first_name
    username = user.username
    mention = user.mention("Link")
    global_rank = await get_global_rank(user_id)
    global_count = await collection.count_documents({})
    total_count = len(existing_user.get('characters', []))
    photo_id = existing_user.get('profile_pic', user.photo.big_file_id if user.photo else None)
    balance = await get_user_balance(user_id)
    global_coin_rank = await user_collection.count_documents({'balance': {'$gt': balance}}) + 1
    xp = existing_user.get('xp', 0)
    level = calculate_user_level(xp)
    
    # Calculate login streak
    last_login = existing_user.get('last_login', 'Unknown')
    current_login = datetime.now()
    last_login_date = existing_user.get('last_login')
    streak = existing_user.get('login_streak', 1)
    
    if last_login_date:
        last_login_date = datetime.strptime(last_login_date, '%Y-%m-%d')
        if (current_login - last_login_date).days == 1:
            streak += 1
        elif (current_login - last_login_date).days > 1:
            streak = 1
    await user_collection.update_one({'id': user_id}, {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}})
    
    # Rarity counts and other info
    rarity_counts = {
        "🫧 Premium": 0, "💮 Exclusive": 0, "🔮 Limited Edition": 0,
        "🌸 Exotic": 0, "👶 Chibi": 0, "🟡 Legendary": 0,
        "🟠 Rare": 0, "🔵 Medium": 0, "⚪️ Common": 0,
        "🎐 Astral": 0, "💞 Valentine": 0
    }
    for char in existing_user.get('characters', []):
        rarity = char.get('rarity', '⚪️ Common')
        if rarity in rarity_counts:
            rarity_counts[rarity] += 1

    rarity_message = "\n".join([
        f"⌠{rarity.split()[0]}⌡ Rarity: {' '.join(rarity.split()[1:])}: {count}"
        for rarity, count in rarity_counts.items()
    ])

    # Prepare the user information message
    info_text = f"""
「 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 」
───────────────────
✨ {first_name}  [`{user_id}`]
🌐 𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀 : @{username}
───────────────────
📜 𝘾𝙃𝘼𝙍𝘼𝘾𝙏𝙀𝙍𝙎 𝗖𝗢𝗨𝗡𝗧 : `{total_count}` / `{global_count}`
🏆 𝙂𝙇𝙊𝘽𝘼𝙇 𝙍𝘼𝙉𝙆 : `{global_rank}`
───────────────────
💸 𝙒𝙀𝘼𝙇𝙏𝙃 : ₩`{balance:,}`
🔱 𝙂𝙇𝙊𝘽𝘼𝙇 𝙒𝙀𝘼𝙇𝙏𝙃 𝙍𝘼𝙉𝙆  : `{global_coin_rank}`
───────────────────
🎮 𝙇𝙀𝙑𝙀𝙇 : `{level}` | 𝙓𝙋 : `{xp}`
🔥 𝙇𝙊𝙂𝙄𝙉 𝙎𝙏𝙍𝙀𝘼𝙆 : {streak} days
───────────────────
{rarity_message}
"""
    return info_text, photo_id

# Command to show user profile/status
@shivuu.on_message(filters.command("status"))
async def profile(client, message):
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else message.from_user.id
    
    m = await message.reply_text("✨ Fetching Your Hunter License...")

    try:
        info_text, photo_id = await get_user_info(user_id)
    except Exception as e:
        return await m.edit(f"❌ Something went wrong: {e}. Report at @{SUPPORT_CHAT}.")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")]
    ])
    
    if photo_id is None:
        return await m.edit(info_text, disable_web_page_preview=True, reply_markup=keyboard)
    
    photo = await shivuu.download_media(photo_id)
    await message.reply_photo(photo, caption=info_text, reply_markup=keyboard)
    await m.delete()
    os.remove(photo)

# Command to set a custom profile picture
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
