import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection, user_totals_collection, shivuu, application
import time

DEVS = (6402009857)

async def get_unique_characters(receiver_id, target_rarities=['🟡 Legendary', '💮 Exclusive']):
    try:
        pipeline = [
            {'$match': {
                'rarity': {'$in': target_rarities}, 
                'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}
            }},
            {'$sample': {'size': 1}}  # Adjust the number of characters sampled
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

async def get_bonus_character(receiver_id):
    try:
        pipeline = [
            {'$match': {
                'rarity': '🔮 Limited Edition',
                'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}
            }},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        bonus_character = await cursor.to_list(length=None)
        return bonus_character
    except Exception as e:
        print(f"Error in get_bonus_character: {e}")
        return []

# Dictionary to store last roll time for each user
cooldowns = {}

@bot.on_message(filters.command(["dice", "roll"]))
async def dice(_, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if the user is in cooldown
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:  # Adjust the cooldown time (in seconds)
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(
            f"⏳ Hold on {mention}, you can roll again in *{cooldown_time}* seconds.", 
            quote=True
        )
        return

    # Update the last roll time for the user
    cooldowns[user_id] = time.time()

    # Keyboard with 1x and 2x roll options
    roll_options = t.InlineKeyboardMarkup([
        [t.InlineKeyboardButton("🎲 1x Roll", callback_data="roll_1x"), 
         t.InlineKeyboardButton("🎲 2x Roll", callback_data="roll_2x")]
    ])
    await message.reply_text(f"Choose your roll option, {mention}:", reply_markup=roll_options)

@bot.on_callback_query(filters.regex("roll_"))
async def roll_callback(_, query: t.CallbackQuery):
    user_id = query.from_user.id
    mention = query.from_user.mention
    receiver_id = user_id
    roll_type = query.data.split("_")[1]
    
    if roll_type == "1x":
        roll_chance = 5  # Lower chance for jackpot
    else:  # 2x roll
        roll_chance = 6  # Higher chance for jackpot
    
    await query.message.delete()  # Remove the roll selection message

    # Roll dice animation with different jackpot chances
    dice_msg = await bot.send_dice(chat_id=query.message.chat.id, emoji="🎲")
    value = int(dice_msg.dice.value)

    unique_characters = await get_unique_characters(receiver_id)
    bonus_character = await get_bonus_character(receiver_id) if value >= roll_chance else []

    if value >= roll_chance:
        # Jackpot win
        for character in unique_characters + bonus_character:
            try:
                await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
            except Exception as e:
                print(f"Error updating character: {e}")

        img_urls = [character['img_url'] for character in unique_characters + bonus_character]
        captions = [
            f"🩵 ᴊᴀᴄᴋᴘᴏᴛ! ❄️\n"
            f"🏮 ʏᴏᴜ ʀᴏʟʟᴇᴅ ᴀ {value}, {mention}!\n\n"
            f"🥂 **ᴜɴɪǫᴜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴜɴʟᴏᴄᴋᴇᴅ!** 🥂\n"
            f"🍃 **ɴᴀᴍᴇ:** {character['name']}\n"
            f"⚜️ **ʀᴀʀɪᴛʏ:** {character['rarity']}\n"
            f"⛩️ **ᴀɴɪᴍᴇ:** {character['anime']}\n\n"
            f"🫧 **ɢᴏᴏᴅ ʟᴜᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴇxᴛ ʀᴏʟʟ!** 🫧\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for character in unique_characters + bonus_character
        ]
        for img_url, caption in zip(img_urls, captions):
            await query.message.reply_photo(photo=img_url, caption=caption)

    elif value in [3, 4]:
        # Medium roll
        await query.message.reply_animation(
            animation="https://files.catbox.moe/p62bql.mp4",
            caption=(
                f"❄️ **ɴɪᴄᴇ ʀᴏʟʟ, {mention}!** ❄️\n\n"
                f"ʏᴏᴜ ʀᴏʟʟᴇᴅ ᴀ {value}, ɴᴏᴛ ʙᴀᴅ ᴀᴛ ᴀʟʟ ɴᴏᴛ ʙᴀᴅ ᴀᴛ ᴀʟʟ! 🩷 ᴋᴇᴇᴘ ᴛʀʏɪɴɢ ғᴏʀ ᴛʜᴇ ᴊᴀᴄᴋᴘᴏᴛ!\n\n"
                f"🥂 **ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ!** 🥂"
            ),
            quote=True
        )

    else:
        # Low roll
        await query.message.reply_animation(
            animation="https://files.catbox.moe/hn08wr.mp4",
            caption=(
                f"💔 **Oᴏᴘs, {mention}.**\n\n"
                f"ʏᴏᴜ ʀᴏʟʟᴇᴅ ᴀ {value}... 🪭\n\n"
                f"ᴅᴏɴ'ᴛ ɢɪᴠᴇ ᴜᴘ! ᴛʀʏ ᴀɪᴍ ғᴏʀ sᴛᴀʀs! 💫"
            ),
            quote=True
        )
