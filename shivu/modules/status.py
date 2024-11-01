from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu
from shivu import SUPPORT_CHAT, user_collection, collection
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Ensure to add PIL to your environment: pip install pillow

# Global rank based on user balance
async def get_global_rank(user_id):
    user_balance = await get_user_balance(user_id)
    higher_balance_count = await user_collection.count_documents({'balance': {'$gt': user_balance}})
    return higher_balance_count + 1

# Fetch user balance from database
async def get_user_balance(user_id):
    user = await user_collection.find_one({"id": user_id})
    return user.get("balance", 0) if user else 0

# Calculate user level based on XP
def calculate_user_level(xp):
    return xp // 100

async def get_user_info(user, already=False):
    try:
        if not already:
            user = await shivuu.get_users(user)
        if not user.first_name:
            return ["⚠️ Deleted account", None]

        user_id = user.id
        existing_user = await user_collection.find_one({'id': user_id})
        if not existing_user:
            return ["⚠️ User not found in the database.", None]

        first_name = user.first_name
        global_rank = await get_global_rank(user_id)
        total_waifus = len(existing_user.get('characters', []))
        total_characters = await collection.count_documents({})
        photo_id = user.photo.big_file_id if user.photo else None
        balance = await get_user_balance(user_id)
        global_coin_rank = await user_collection.count_documents({'balance': {'$gt': balance}}) + 1
        xp = existing_user.get('xp', 0)
        level = calculate_user_level(xp)
        tokens = existing_user.get('tokens', 0)
        current_login = datetime.now()
        last_login_date = existing_user.get('last_login')
        streak = existing_user.get('login_streak', 0) + 1 if last_login_date else 1

        # Update last login and streak in the database
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'last_login': current_login.strftime('%Y-%m-%d'), 'login_streak': streak}}
        )

        # Formatting for tokens and balance
        tokens_formatted = f"{tokens:,}"
        balance_formatted = f"{balance:,}"

        # Profile Information Message Formatting
        info_text = f"""
Name: {first_name}
User ID: {user_id}
Total Waifus: {total_waifus}/{total_characters}
Waifu Percentage: {round((total_waifus / total_characters) * 100, 2)}%
Level: {level}
XP: {xp}
Tokens: {tokens_formatted}
Global Position: {global_rank}
Token Position: {global_coin_rank}
Login Streak: {streak} days
"""

        return info_text.strip(), photo_id
    except Exception as e:
        print(f"⚠️ Error in get_user_info: {e}")
        return ["⚠️ Error fetching user information.", None]

async def create_profile_image(info_text, profile_photo_path):
    try:
        # Load background image
        background = Image.open("/path/to/background-image.jpg").convert("RGBA")
        
        # Check if profile photo path exists
        if not profile_photo_path or not os.path.exists(profile_photo_path):
            print("⚠️ Profile photo path does not exist.")
            return None
        
        # Load and process profile photo
        profile_photo = Image.open(profile_photo_path).convert("RGBA").resize((100, 100))
        
        # Create circular mask
        mask = Image.new("L", profile_photo.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, profile_photo.size[0], profile_photo.size[1]), fill=255)
        profile_photo.putalpha(mask)

        # Paste profile photo onto background
        background.paste(profile_photo, (50, 50), profile_photo)

        # Draw info text on the image
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype("/path/to/arial.ttf", 20)  # Ensure path to font file is correct
        text_position = (200, 50)
        draw.multiline_text(text_position, info_text, font=font, fill="white")  # Use multiline text

        # Save and return the path to the image
        output_path = "/tmp/profile_image.png"
        background.save(output_path)
        return output_path
    except Exception as e:
        print(f"⚠️ Error in create_profile_image: {e}")
        return None
