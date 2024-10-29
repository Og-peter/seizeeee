import asyncio
import traceback
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta

DEVS = [6402009857]

GROUP_ID = -1002104939708
LOG_CHANNEL_ID = -1002446048543  # Replace with your actual log channel ID

async def send_error_to_devs(error_message):
    for dev_id in DEVS:
        try:
            await bot.send_message(dev_id, error_message)
        except Exception as e:
            print(f"Error sending message to dev {dev_id}: {e}")

async def send_log_message(log_message):
    try:
        await bot.send_message(LOG_CHANNEL_ID, log_message)
    except Exception as e:
        print(f"Error sending log message: {e}")

async def get_unique_characters(receiver_id, target_rarities=None):
    if target_rarities is None:
        target_rarities = ['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']

    try:
        user = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_character_ids = [char.get('id') for char in user.get('characters', [])]

        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_character_ids}}},
            {'$sample': {'size': 1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        await send_error_to_devs(f"Error in get_unique_characters: {traceback.format_exc()}")
        return []

last_claim_time = {}

async def process_claim(user_id, chat_id, user_first_name, message_id):
    unique_characters = await get_unique_characters(user_id)
    try:
        # Update user's character list in the database
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': unique_characters}}})
        
        # Prepare image URLs and captions with additional text and user mention
        img_urls = [character['img_url'] for character in unique_characters]
        captions = [
            f"❄️ **ᴏᴡᴏ, {user_first_name} (@{user_id})! ʜᴇʀᴇ ɪs ᴀ sᴘᴇᴄɪᴀʟ ᴄʟᴀɪᴍ ғᴏʀ ʏᴏᴜ!** 🏮\n\n"
            f"🥂 **ɴᴀᴍᴇ:** {character['name']}\n"
            f"☃️ **ʀᴀʀɪᴛʏ:** {character['rarity']}\n"
            f"⛩️ **ᴀɴɪᴍᴇ:** {character['anime']}\n\n"
            f"🍃 **ᴅᴏɴ'ᴛ ғᴏʀɢᴇᴛ ᴛᴏ ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ғᴏʀ ᴍᴏʀᴇ ᴄʟᴀɪᴍs!**"
            for character in unique_characters
        ]
        
        # Send each image with caption, replying to the specified message
        for img_url, caption in zip(img_urls, captions):
            await bot.send_photo(
                chat_id=chat_id,
                photo=img_url,
                caption=caption,
                reply_to_message_id=message_id  # Replying to a specific message
            )
    except Exception as e:
        await send_error_to_devs(f"Error in process_claim: {traceback.format_exc()}")
        
@bot.on_message(filters.command(["wclaim"]))
async def claim_waifu(_, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_first_name = message.from_user.first_name

    if chat_id != GROUP_ID:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴊᴏɪɴ ɢʀᴏᴜᴘ ᴛᴏ ᴄʟᴀɪᴍ", url="https://t.me/dynamic_gangs")]
        ])
        return await message.reply_text(
            "🚫 **ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ.**\n\n"
            "ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ!",
            reply_markup=keyboard,
            quote=True
        )

    if user_id == 7162166061:
        return await message.reply_text("⚠️ **Sorry, you are banned from using this command.**")

    now = datetime.now()
    if user_id in last_claim_time:
        last_claim_date = last_claim_time[user_id]
        if last_claim_date.date() == now.date():
            next_claim_time = (last_claim_date + timedelta(days=1)).strftime("%H:%M:%S")
            return await message.reply_text(
                             f"⏰ **ɢᴏᴍᴇɴ'ɴᴀsᴀɪ, @{update.effective_user.username}!**\n"
                             f"**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟ {next_claim_time} ᴛᴏ ᴄʟᴀɪᴍ ʏᴏᴜʀ ɴᴇxᴛ ᴄʜᴀʀᴀᴄᴛᴇʀ.**",
                             quote=True
                        )

    last_claim_time[user_id] = now

    animation_messages = [
        "🔥 **ɢᴇᴛᴛɪɴɢ ʏᴏᴜʀ ᴄʟᴀɪᴍ ʀᴇᴀᴅʏ...**",
        "⚡ **ᴘʀᴇᴘᴀʀɪɴɢ ᴛʜᴇ ʀᴇᴡᴀʀᴅs...**",
        "❄️ **ᴡᴀɪᴛᴏ ʙᴀᴋᴀ...**",
        "🎉 **ʜᴇʀᴇ ᴄᴏᴍᴇs ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ ʙᴀʙʏ!**"
    ]

    animation_message = await message.reply_text(animation_messages[0])
    for msg in animation_messages[1:]:
        await asyncio.sleep(1)
        await animation_message.edit_text(msg)

    await process_claim(user_id, chat_id, user_first_name)

    # Send a log message about the claim
    log_message = (
        f"📢 <b>Waifu Claimed!</b>\n\n"
        f"🧑‍🚀 <b>User:</b> {user_first_name} (ID: <code>{user_id}</code>)\n"
        f"🗣 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"📅 <b>Date & Time:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🌸 <i>Another waifu has been claimed! Happy hunting!</i>"
    )

    # Send the log message
    await send_log_message(log_message)
