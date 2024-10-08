import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection

# Constants
WIN_RATE_PERCENTAGE = 30  # Set the win rate percentage here
COOLDOWN_DURATION = 300  # Set the cooldown duration in seconds (5 minutes)
FIGHT_FEE = 30000  # Set the fee for the fight command

# Tracking cooldowns
user_cooldowns = {}  # Dictionary to track user cooldowns

# Banned user IDs (example)
BAN_USER_IDS = {1234567890}  # Replace with real banned user IDs

# Random dynamic fight videos
BATTLE_VIDEOS = [
    'https://files.catbox.moe/n5wgtw.mp4',
    'https://files.catbox.moe/o31n2n.mp4',
    'https://files.catbox.moe/qxfu13.gif'
]

# Random battle outcomes
BATTLE_MESSAGES = [
    "⚔️ The epic battle between Gojo and Sukuna begins 🏹",
    "💥 A fierce fight is about to unfold between Gojo and Sukuna 💥",
    "🔮 The domain expansion fight between Gojo and Sukuna is happening!"
]

# Fight preparation animations
FIGHT_PREPARATION = [
    "⚔️ Preparing your team... 🛡️",
    "💥 Powering up your domain expansion... 🌌",
    "🔥 Gathering your strongest warriors... 💪"
]

# Fight outcome animations
FIGHT_OUTCOME_ANIMATIONS = [
    "💥 The clash is intense! 💥",
    "🔥 Your warriors strike with precision! ⚔️",
    "🌀 Sukuna is unleashing a powerful move! 💀"
]

# Function to get random characters from the database
async def get_random_characters():
    target_rarities = ['🟡 Legendary']  # Example rarity list
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}  # Adjust the size as needed
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Fight command handler
@bot.on_message(filters.command(["fight"]))
async def sfight(_, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id
    current_time = time.time()

    # Check if the user is banned
    if user_id in BAN_USER_IDS:
        return await message.reply_text("Sorry, you are banned from this command. Contact @dynamic_gangs for help.")

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < COOLDOWN_DURATION:
        remaining_time = COOLDOWN_DURATION - int(current_time - user_cooldowns[user_id])
        minutes, seconds = divmod(remaining_time, 60)
        return await message.reply_text(f"⏳ Please wait! Your fighters are resting. Cooldown: {minutes} min {seconds} sec.")

    # Deduct the fight fee from the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)

    if user_balance < FIGHT_FEE:
        return await message.reply_text("🚫 You don't have enough tokens to initiate a battle. You need at least 30,000.")

    # Deduct fee
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -FIGHT_FEE}})

    # Fetch random characters for the user
    random_characters = await get_random_characters()

    try:
        # Set cooldown for the user
        user_cooldowns[user_id] = current_time

        # Send the starting message with a random video
        start_message = random.choice(BATTLE_MESSAGES)
        video_url = random.choice(BATTLE_VIDEOS)
        start_msg = await bot.send_video(chat_id, video=video_url, caption=start_message)

        # Add fight preparation animation
        for animation in FIGHT_PREPARATION:
            await message.reply_text(animation)
            await asyncio.sleep(1)

        # Determine if the user wins or loses the battle
        if random.random() < (WIN_RATE_PERCENTAGE / 100):
            # User wins the fight
            await asyncio.sleep(3)  # Add some delay for realism

            for character in random_characters:
                try:
                    # Add the character to the user's collection
                    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(f"Error adding character to user: {e}")

            img_urls = [character['img_url'] for character in random_characters]
            captions = [
                f"🔥 {mention}, you won the fight! 🔥\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                for character in random_characters
            ]

            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

            # Send outcome animation
            for animation in FIGHT_OUTCOME_ANIMATIONS:
                await message.reply_text(animation)
                await asyncio.sleep(1)

            # Add a retry button
            retry_button = InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚔️ Try Another Fight ⚔️", callback_data="retry_fight")]]
            )
            await message.reply_text("💪 Ready for another battle?", reply_markup=retry_button)

        else:
            # User loses the fight
            await asyncio.sleep(2)
            await message.reply_text(f"{mention}, you lost the fight. Sukuna has defeated Gojo! 💀")
            loss_video = random.choice(BATTLE_VIDEOS)
            await bot.send_video(chat_id, video=loss_video, caption="💀 Tough loss, better luck next time!")

    except Exception as e:
        print(f"Error during fight: {e}")
        await message.reply_text("⚠️ Something went wrong. Please try again later.")

# Retry fight callback handler
@bot.on_callback_query(filters.regex("retry_fight"))
async def retry_fight(_, callback_query: t.CallbackQuery):
    await sfight(_, callback_query.message)
