import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import random
import time

# Cooldown Dictionary
cooldowns = {}

# Leaderboard & Streak Tracking
leaderboard = {}
roll_streaks = {}

# Target Rarities
target_rarities = ['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']

# Log Channel ID (Replace with your own)
LOGS_CHANNEL_ID = -1002446048543  # Your Logs Channel ID

# Function to Fetch Unique Characters
async def get_unique_characters(receiver_id, target_rarities=target_rarities):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in fetching characters: {e}")
        return []

# Fun Congratulatory Message with Styled Fonts
def get_congratulatory_message(mention, character):
    messages = [
        f"🎉 ✨『Congratulations』✨ {mention}! You've just 『𝒎𝒂𝒓𝒓𝒊𝒆𝒅』 {character['name']} from {character['anime']} 💍!",
        f"💞 𝑯𝒂𝒊 {mention}! {character['name']} from {character['anime']} 🌸 𝑖𝑠 𝑤𝑎𝑖𝑡𝑖𝑛𝑔 𝑖𝑛 𝑦𝑜𝑢𝑟 𝒉𝒂𝒓𝒆𝒎!"
    ]
    return random.choice(messages)

# Failure Message with Styled Fonts
def get_rejection_message(mention):
    messages = [
        f"💔 𝑯𝒂𝒓𝒅 𝒍𝒖𝒄𝒌, {mention}! She slipped away and left you 『💀』",
        f"💀 Better luck next time, {mention}. She 『𝑟𝑒𝑓𝑢𝑠𝑒𝑑』 and vanished! 👻",
    ]
    return random.choice(messages)

# Cooldown Message with Emoji Countdown
def get_cooldown_message(cooldown_time):
    countdown_emojis = ['⏳', '⌛', '🕒']
    return f"{random.choice(countdown_emojis)} 𝑷𝒍𝒆𝒂𝒔𝒆 𝒘𝒂𝒊𝒕 {cooldown_time} 𝒔𝒆𝒄𝒐𝒏𝒅𝒔 𝒃𝒆𝒇𝒐𝒓𝒆 𝒂𝒏𝒐𝒕𝒉𝒆𝒓 𝒕𝒓𝒚!"

# Streak Bonus Message
def get_streak_bonus_message(mention, streak):
    return f"🔥 𝑾𝒐𝒘 {mention}, you've reached a 𝒔𝒕𝒓𝒆𝒂𝒌 of {streak}! 🔥"

# Marry Command with Advanced Features
@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Logging Command Usage
    log_message = f"🎲 <b>Marry Command Activated</b>\n\n👤 User: {mention} (ID: <code>{user_id}</code>)\n💬 Chat ID: <code>{chat_id}</code>"
    await bot.send_message(chat_id=LOGS_CHANNEL_ID, text=log_message)

    # Cooldown Check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(get_cooldown_message(cooldown_time), quote=True)

    # Updating Last Roll Time
    cooldowns[user_id] = time.time()

    # Rolling Dice with Styled Message
    await message.reply_text("🎲 『Rolling』 🎲")
    dice_msg = await bot.send_dice(chat_id=chat_id)
    value = int(dice_msg.dice.value)

    # Success Values (1, 6)
    if value in [1, 6]:
        receiver_id = user_id
        unique_characters = await get_unique_characters(receiver_id)

        for character in unique_characters:
            try:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                leaderboard[mention] = leaderboard.get(mention, 0) + 1
                roll_streaks[mention] = roll_streaks.get(mention, 0) + 1
            except Exception as e:
                print(e)

        for character in unique_characters:
            img_url = character['img_url']
            caption = get_congratulatory_message(mention, character)
            await message.reply_photo(photo=img_url, caption=caption)

        # Success Message with Emojis
        success_emojis = ['🎉', '💍', '💖', '🥳']
        await message.reply_text(f"{random.choice(success_emojis)} 『𝑳𝒖𝒄𝒌𝒚 𝑹𝒐𝒍𝒍』! 💍 Your proposal was accepted!")

        # Bonus for Streaks
        if roll_streaks[mention] > 1:
            await message.reply_text(get_streak_bonus_message(mention, roll_streaks[mention]))

    else:
        # Failure Message
        await message.reply_text(get_rejection_message(mention), quote=True)
        roll_streaks[mention] = 0  # Reset Streak
