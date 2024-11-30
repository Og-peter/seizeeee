import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
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
        pipeline = [
            {
                '$match': {
                    'rarity': {'$in': target_rarities},
                    'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}
                }
            },
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
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

# Streak Bonus Message
def get_streak_bonus_message(mention, streak):
    return f"🔥 Impressive, {mention}! You're on a streak of **{streak}** successful rolls!"

# Handle Marry and Reject Button Press
@bot.on_callback_query(filters.regex(r"^(marry|reject)_"))
async def handle_marry_reject(client, callback_query: t.CallbackQuery):
    action, user_id, character_id = callback_query.data.split('_')
    user_id = int(user_id)

    # Check if the callback query is from the correct user
    if callback_query.from_user.id != user_id:
        await callback_query.answer("🚫 You can't interact with this!", show_alert=True)
        return

    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await callback_query.answer("❌ User data not found!", show_alert=True)
        return

    if action == "marry":
        # Fetch the character details
        character = await collection.find_one({'id': int(character_id)})
        if character:
            # Check if the character is already in the user's collection
            if any(c['id'] == character['id'] for c in user_data.get('characters', [])):
                await callback_query.answer("⚠️ Character is already in your collection!", show_alert=True)
                return
            
            # Add the character to the user's collection
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': character}}
            )
            await callback_query.answer("💍 Congratulations on your new partner!", show_alert=True)
            await callback_query.message.edit_caption(
                f"🎉 {callback_query.from_user.mention}, you married **{character['name']}** from **{character['anime']}**! 💖"
            )
        else:
            await callback_query.answer("❌ Character not found!", show_alert=True)

    elif action == "reject":
        await callback_query.answer("❌ Character rejected!", show_alert=True)
        await callback_query.message.delete()

# Main Dice/Marry Command
@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Cooldown Check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(get_cooldown_message(cooldown_time), quote=True)

    cooldowns[user_id] = time.time()  # Reset Cooldown

    await message.reply_text("🎲 Rolling the dice... 🎲")
    dice_msg = await bot.send_dice(chat_id)
    value = dice_msg.dice.value

    # Define success range based on dice value
    success_range = [1, 3, 5]  # Adjusted success range

    if value in success_range:
        unique_characters = await get_unique_characters(user_id)
        if unique_characters:
            character = unique_characters[0]
            img_url = character['img_url']
            caption = get_congratulatory_message(mention, character)
            buttons = t.InlineKeyboardMarkup(
                [
                    [
                        t.InlineKeyboardButton("💍 Marry", callback_data=f"marry_{user_id}_{character['id']}"),
                        t.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{character['id']}")
                    ]
                ]
            )
            await message.reply_photo(img_url, caption=caption, reply_markup=buttons)
        else:
            await message.reply_text("💔 No unique characters found.")
    else:
        await message.reply_text(get_rejection_message(mention), quote=True)
        roll_streaks[mention] = 0  # Reset streak
