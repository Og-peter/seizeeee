import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import time

# Cooldown Management
cooldowns = {}

# Leaderboard & Streak Tracking
leaderboard = {}
roll_streaks = {}

# Rarity Categories
target_rarities = ['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']

# Function to Fetch Unique Characters
async def get_unique_characters(receiver_id, target_rarities=target_rarities):
    try:
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters.id': 1})
        user_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        pipeline = [
            {
                '$match': {
                    'rarity': {'$in': target_rarities},
                    'id': {'$nin': user_character_ids}
                }
            },
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=1)  # Fetch a single character
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Generate Congratulatory Message
def get_congratulatory_message(mention, character):
    return f"🎉 {mention}, you just met **{character['name']}** from **{character['anime']}**! 💖 What will you do next?"

# Generate Failure Message
def get_rejection_message(mention):
    return f"💔 Sorry, {mention}. No character this time. Keep trying!"

# Cooldown Message with Timer
def get_cooldown_message(cooldown_time):
    return f"⏳ Please wait **{cooldown_time}** seconds before trying again."

# Handle Marry and Reject Button Press
@bot.on_callback_query(filters.regex(r"^(marry|reject)_"))
async def handle_marry_reject(client, callback_query: t.CallbackQuery):
    try:
        action, user_id, character_id = callback_query.data.split('_')
        user_id = int(user_id)
        character_id = int(character_id)

        # Check if the callback query is from the correct user
        if callback_query.from_user.id != user_id:
            await callback_query.answer("🚫 You can't interact with this!", show_alert=True)
            return

        # Fetch character and user data
        character = await collection.find_one({'id': character_id})
        user_data = await user_collection.find_one({'id': user_id})

        if not character or not user_data:
            await callback_query.answer("❌ Error: Data not found!", show_alert=True)
            return

        if action == "marry":
            # Check if character is already in the user's collection
            if any(c['id'] == character_id for c in user_data.get('characters', [])):
                await callback_query.answer("⚠️ Character is already in your collection!", show_alert=True)
                return

            # Add character to user's collection
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': {'id': character_id, 'name': character['name'], 'anime': character['anime']}}}
            )
            await callback_query.answer("💍 You successfully married this character!", show_alert=True)
            await callback_query.message.edit_caption(
                f"🎉 {callback_query.from_user.mention} married **{character['name']}** from **{character['anime']}**! 💖",
                reply_markup=None  # Remove buttons
            )
        elif action == "reject":
            await callback_query.answer("❌ You rejected the character!", show_alert=True)
            await callback_query.message.delete()  # Delete the message on rejection
    except Exception as e:
        print(f"Error handling callback query: {e}")

# Main Dice/Marry Command
@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_, message: t.Message):
    try:
        chat_id = message.chat.id
        mention = message.from_user.mention
        user_id = message.from_user.id

        # Cooldown Check
        if user_id in cooldowns:
            elapsed_time = time.time() - cooldowns[user_id]
            if elapsed_time < 60:
                cooldown_time = int(60 - elapsed_time)
                return await message.reply_text(get_cooldown_message(cooldown_time), quote=True)

        cooldowns[user_id] = time.time()  # Set new cooldown

        await message.reply_text("🎲 Rolling the dice... 🎲")
        dice_msg = await bot.send_dice(chat_id)
        value = dice_msg.dice.value

        # Define success range based on dice value
        success_range = [1, 3, 5]

        if value in success_range:
            unique_characters = await get_unique_characters(user_id)
            if unique_characters:
                character = unique_characters[0]
                img_url = character.get('img_url', 'https://via.placeholder.com/300')  # Fallback image
                caption = get_congratulatory_message(mention, character)
                buttons = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("💍 Marry", callback_data=f"marry_{user_id}_{character['id']}"),
                            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{character['id']}")
                        ]
                    ]
                )
                await message.reply_photo(img_url, caption=caption, reply_markup=buttons)
            else:
                await message.reply_text("💔 No unique characters found.")
        else:
            await message.reply_text(get_rejection_message(mention), quote=True)
            roll_streaks[mention] = 0  # Reset streak
    except Exception as e:
        print(f"Error in dice command: {e}")
