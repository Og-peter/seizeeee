import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import random
import time

# Dictionary to store last roll time for each user (for cooldowns)
cooldowns = {}
# Leaderboard and Streak Tracking
leaderboard = {}
roll_streaks = {}

# Rarities that can be targeted
target_rarities = ['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']

# Logs Channel ID (replace with actual channel ID)
LOGS_CHANNEL_ID = -1002446048543  # Replace with your logs channel's chat ID

# Function to fetch unique characters
async def get_unique_characters(receiver_id, target_rarities=target_rarities):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}  # Adjust number of characters
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in fetching characters: {e}")
        return []

# Helper function to get a fun congratulatory message
def get_congratulatory_message(mention, character):
    messages = [
        f"🎉 Congratulations {mention}! You've just married {character['name']} from {character['anime']} 💍!",
        f"💞 {mention}, your new girl {character['name']} from {character['anime']} is waiting in the harem! 🌸",
        f"💖 Lucky you {mention}, {character['name']} from {character['anime']} said yes! 💍 Welcome her to your harem!"
    ]
    return random.choice(messages)

# Helper function to get failure message when the proposal is rejected
def get_rejection_message(mention):
    messages = [
        f"💔 Sorry {mention}, she ran away and left you heartbroken! 💀",
        f"🤡 {mention}, she rejected your marriage proposal and escaped! Try harder next time! 🤣",
        f"😢 {mention}, no luck today! She left you with nothing but tears! 💔"
    ]
    return random.choice(messages)

# Helper function for cooldown message with countdown
def get_cooldown_message(cooldown_time):
    countdown_emojis = ['⏳', '⌛', '⏰', '🕒', '🕔']
    return f"{random.choice(countdown_emojis)} Please wait {cooldown_time} seconds before trying again!"

# Helper function for streak bonus
def get_streak_bonus_message(mention, streak):
    return f"🔥 {mention}, you're on fire! You have a streak of {streak} successful rolls in a row! 🔥"

# Dice command with cooldowns, streaks, leaderboard, and improved messaging
@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Log the usage of the command
    log_message = f"🎲 <b>Marry Command Used</b>\n\n👤 User: {mention} (ID: <code>{user_id}</code>)\n💬 Chat ID: <code>{chat_id}</code>"
    await bot.send_message(chat_id=LOGS_CHANNEL_ID, text=log_message)

    # Check if the user is in cooldown
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:  # Adjust cooldown time
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(get_cooldown_message(cooldown_time), quote=True)

    # Update the last roll time for the user
    cooldowns[user_id] = time.time()

    # Roll the dice with a fun emoji animation
    await message.reply_text("🎲 Rolling the dice... Let's see your luck!")
    dice_msg = await bot.send_dice(chat_id=chat_id)
    value = int(dice_msg.dice.value)

    # Process based on dice value
    if value in [1, 6]:  # Special success values (1 or 6)
        receiver_id = user_id
        unique_characters = await get_unique_characters(receiver_id)

        for character in unique_characters:
            try:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                leaderboard[mention] = leaderboard.get(mention, 0) + 1
                roll_streaks[mention] = roll_streaks.get(mention, 0) + 1
            except Exception as e:
                print(e)  # Handle the exception appropriately

        for character in unique_characters:
            img_url = character['img_url']
            caption = get_congratulatory_message(mention, character)
            await message.reply_photo(photo=img_url, caption=caption)

        success_emojis = ['🎉', '💍', '💖', '🥳', '👰']
        await message.reply_text(f"{random.choice(success_emojis)} You rolled a lucky number! 💍 Your proposal was accepted!")

        # Bonus for roll streaks
        if roll_streaks[mention] > 1:
            await message.reply_text(get_streak_bonus_message(mention, roll_streaks[mention]))

    else:
        # In case of failure (any other value)
        await message.reply_text(get_rejection_message(mention), quote=True)
        roll_streaks[mention] = 0  # Reset streak
