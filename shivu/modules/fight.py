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

# Logs Channel ID (replace with actual channel ID)
LOGS_CHANNEL_ID = -1002446048543  # Replace with your logs channel's chat ID

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
    "⚔️ **ᴛʜᴇ ᴇᴘɪᴄ ʙᴀᴛᴛʟᴇ ʙᴇᴛᴡᴇᴇɴ ɢᴏᴊᴏ ᴀɴᴅ sᴜᴋᴜɴᴀ ʙᴇɢɪɴs!** 🏹",
    "💥 **ᴀ ғɪᴇʀᴄᴇ ғɪɢʜᴛ ɪs ᴀʙᴏᴜᴛ ᴛᴏ ᴜɴғᴏʟᴅ ʙᴇᴛᴡᴇᴇɴ ɢᴏᴊᴏ ᴀɴᴅ sᴜᴋᴜɴᴀ!** 💥",
    "🔮 **ᴛʜᴇ ᴅᴏᴍᴀɪɴ ᴇxᴘᴀɴsɪᴏɴ ғɪɢʜᴛ ʙᴇᴛᴡᴇᴇɴ ɢᴏᴊᴏ ᴀɴᴅ sᴜᴋᴜɴᴀ ɪs ʜᴀᴘᴘᴇɴɪɴɢ!**"
]

# Sukuna and Gojo's Moves
SUKUNA_MOVES = [
    "🌀 **sᴜᴋᴜɴᴀ ᴜsᴇs ʜɪs Dɪsᴍᴀɴᴛʟᴇ ᴛᴏ ᴛᴇᴀʀ ᴛʜʀᴏᴜɢʜ ᴛʜᴇ ʙᴀᴛᴛʟᴇғɪᴇʟᴅ!**",
    "💀 **sᴜᴋᴜɴᴀ ᴜɴʟᴇᴀsʜᴇs ᴍᴀʟᴇᴠᴏʟᴇɴᴛ sʜʀɪɴᴇ, ᴇɴɢᴜʟғɪɴɢ ɢᴏᴊᴏ ɪɴ ᴀ ᴅᴇsᴛʀᴜᴄᴛɪᴠᴇ ᴅᴏᴍᴀɪɴ!**",
    "🔥 **sᴜᴋᴜɴᴀ sᴜᴍᴍᴏɴs Cʟᴇᴀᴠᴇ ᴛᴏ sʟɪᴄᴇ ᴛʜʀᴏᴜɢʜ ɢᴏᴊᴏ's ᴅᴇғᴇɴsᴇs!**"
]

GOJO_MOVES = [
    "🔵 **ɢᴏᴊᴏ ᴀᴄᴛɪᴠᴀᴛᴇs Iɴғɪɴɪᴛʏ, ʙʟᴏᴄᴋɪɴɢ sᴜᴋᴜɴᴀ's ᴀᴛᴛᴀᴄᴋ ᴡɪᴛʜ ᴀɴ ɪᴍᴘᴇɴᴇᴛʀᴀʙʟᴇ ʙᴀʀʀɪᴇʀ!**",
    "🌌 **ɢᴏᴊᴏ ᴜsᴇs ʜᴏʟʟᴏᴡ ᴘᴜʀᴘʟᴇ, ᴇʀᴀsɪɴɢ ᴇᴠᴇʀʏᴛʜɪɴɢ ɪɴ ɪᴛs ᴘᴀᴛʜ!**",
    "⚡ **ɢᴏᴊᴏ ᴘᴇʀғᴏʀᴍs Rᴇᴅ Rᴇᴠᴇʀsᴀʟ, sᴇɴᴅɪɴɢ sᴜᴋᴜɴᴀ ғʟʏɪɴɢ!**"
]

# Fight preparation animations
FIGHT_PREPARATION = [
    "⚔️ **ᴘʀᴇᴘᴀʀɪɴɢ ʏᴏᴜʀ ᴛᴇᴀᴍ...** 🛡️",
    "💥 **ᴘᴏᴡᴇʀɪɴɢ ᴜᴘ ʏᴏᴜʀ ᴅᴏᴍᴀɪɴ ᴇxᴘᴀɴsɪᴏɴ...** 🌌",
    "🔥 **ɢᴀᴛʜᴇʀɪɴɢ ʏᴏᴜʀ sᴛʀᴏɴɢᴇsᴛ ᴡᴀʀʀɪᴏʀs...** 💪"
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

    # Log the usage of the command
    log_message = (
        f"⚔️ **<b>ғɪɢʜᴛ ᴄᴏᴍᴍᴀɴᴅ ᴜsᴇᴅ</b>**\n\n"
        f"👤 **ᴜsᴇʀ:** {mention} (ID: <code>{user_id}</code>)\n"
        f"💬 **ᴄʜᴀᴛ ɪᴅ:** <code>{chat_id}</code>"
    )
    await bot.send_message(chat_id=LOGS_CHANNEL_ID, text=log_message)

    # Check if the user is banned
    if user_id in BAN_USER_IDS:
        return await message.reply_text("❌ **sᴏʀʀʏ, ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ. ᴄᴏɴᴛᴀᴄᴛ @dynamic_gangs ғᴏʀ ʜᴇʟᴘ.**")

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < COOLDOWN_DURATION:
        remaining_time = COOLDOWN_DURATION - int(current_time - user_cooldowns[user_id])
        minutes, seconds = divmod(remaining_time, 60)
        return await message.reply_text(f"⏳ **ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ! ʏᴏᴜʀ ғɪɢʜᴛᴇʀs ᴀʀᴇ ʀᴇsᴛɪɴɢ.** **ᴄᴏᴏʟᴅᴏᴡɴ:** {minutes} ᴍɪɴ {seconds} sᴇᴄ.")

    # Deduct the fight fee from the user's balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)

    if user_balance < FIGHT_FEE:
        return await message.reply_text("🚫 **ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ᴛᴏᴋᴇɴs ᴛᴏ ɪɴɪᴛɪᴀᴛᴇ ᴀ ʙᴀᴛᴛʟᴇ. ʏᴏᴜ ɴᴇᴇᴅ ᴀᴛ ʟᴇᴀsᴛ 30,000.**")

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
        await bot.send_video(chat_id, video=video_url, caption=start_message)

        # Add fight preparation animation
        for animation in FIGHT_PREPARATION:
            await message.reply_text(animation)
            await asyncio.sleep(1)

        # Battle simulation with moves
        for i in range(3):  # 3 rounds of moves
            sukuna_move = random.choice(SUKUNA_MOVES)
            gojo_move = random.choice(GOJO_MOVES)

            await message.reply_text(sukuna_move)
            await asyncio.sleep(1)
            await message.reply_text(gojo_move)
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
                f"🔥 **{mention}, ʏᴏᴜ ᴡᴏɴ ᴛʜᴇ ғɪɢʜᴛ!** 🔥\n"
                f"🥂 **ɴᴀᴍᴇ:** {character['name']}\n"
                f"❄️ **ʀᴀʀɪᴛʏ:** {character['rarity']}\n"
                f"⛩️ **ᴀɴɪᴍᴇ:** {character['anime']}\n"
                for character in random_characters
            ]

            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

            # Add a retry button
            retry_button = InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚔️ ᴛʀʏ ᴀɴᴏᴛʜᴇʀ ғɪɢʜᴛ ⚔️", callback_data="retry_fight")]]
            )
            await message.reply_text("💪 ʀᴇᴀᴅʏ ғᴏʀ ᴀɴᴏᴛʜᴇʀ ʙᴀᴛᴛʟᴇ?", reply_markup=retry_button)

        else:
            # User loses the fight
            await asyncio.sleep(2)
    
            # Add character-specific dialogues based on the loser
            if random.random() < 0.5:  # Randomly decide if Sukuna or Gojo loses
                await message.reply_text(f"💀 **{mention}, ʏᴏᴜ ʟᴏsᴛ ᴛʜᴇ ғɪɢʜᴛ. sᴜᴋᴜɴᴀ ʜᴀs ᴅᴇғᴇᴀᴛᴇᴅ ɢᴏᴊᴏ!** 💀")
                await message.reply_text("😈 **sᴜᴋᴜɴᴀ:** ʏᴏᴜ ʜᴀᴅ ɴᴏ ᴄʜᴀɴᴄᴇs, ɢᴏᴊᴏ! ᴏʀ ɴᴏᴡ, ᴛʜʀᴏᴡ ʏᴏᴜʀsᴇʟғ ᴀᴡᴀʏ.")
            else:
                await message.reply_text(f"💀 **{mention}, ʏᴏᴜ ʟᴏsᴛ ᴛʜᴇ ғɪɢʜᴛ. ɢᴏᴊᴏ ʜᴀs ᴅᴇғᴇᴀᴛᴇᴅ sᴜᴋᴜɴᴀ!** 💀")
                await message.reply_text("😤 **ɢᴏᴊᴏ:** sᴜᴋᴜɴᴀ, ʏᴏᴜ ᴀʀᴇ ɴᴏᴛʜɪɴɢ ʙᴜᴛ ᴀ ʙʟᴏᴏᴅʏ ᴡʜɪsᴘᴇʀ. ɴᴏᴡ ʟᴇᴀᴠᴇ ᴏʀ ɪ'ʟʟ ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ᴅᴇsᴛʀᴏʏ ʏᴏᴜ!")

            loss_video = random.choice(BATTLE_VIDEOS)
            await bot.send_video(chat_id, video=loss_video, caption="💀 **ᴛᴏᴜɢʜ ʟᴏss, ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ!**")

# Retry fight callback handler
@bot.on_callback_query(filters.regex("retry_fight"))
async def retry_fight(_, callback_query: t.CallbackQuery):
    await sfight(_, callback_query.message)
