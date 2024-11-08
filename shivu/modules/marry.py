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

# Function to Fetch Unique Characters from Target Rarities Only
async def get_unique_characters(receiver_id, target_rarities=target_rarities):
    try:
        pipeline = [
            {'$match': {
                'rarity': {'$in': target_rarities},
                'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}
            }},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in fetching characters: {e}")
        return []

# Function to handle button callback
@bot.on_callback_query(filters.regex(r"^marry:(yes|no):(\d+)$"))
async def marry_callback(_, callback_query: t.CallbackQuery):
    choice, user_id = callback_query.data.split(":")[1:]
    user_id = int(user_id)

    if callback_query.from_user.id != user_id:
        await callback_query.answer("This action is not for you!", show_alert=True)
        return

    if choice == "yes":
        # User chose "Yes" - chance-based reward
        if random.random() < 0.5:  # 50% chance to win
            receiver_id = callback_query.from_user.id
            unique_characters = await get_unique_characters(receiver_id)

            for character in unique_characters:
                try:
                    await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(e)
                await callback_query.message.reply_photo(
                    photo=character['img_url'],
                    caption=f"🎉 {callback_query.from_user.mention}, ʏᴏᴜ'ᴠᴇ sᴇᴄᴜʀᴇᴅ {character['name']} ғʀᴏᴍ {character['anime']} 💍!"
                )
            await callback_query.answer("Congratulations! You've won the waifu!", show_alert=True)
        else:
            await callback_query.message.reply_text(f"💔 {callback_query.from_user.mention}, sʜᴇ ʀᴇᴊᴇᴄᴛᴇᴅ ʏᴏᴜʀ ᴘʀᴏᴘᴏsᴀʟ... ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ.")
            await callback_query.answer("Better luck next time!", show_alert=True)
    else:
        # Improved message for "No" choice
        await callback_query.message.reply_text(f"😔 {callback_query.from_user.mention}, ʏᴏᴜ ᴅᴇᴄɪᴅᴇᴅ ᴛᴏ ʟᴇᴛ ɢᴏ. ᴍᴀʏʙᴇ sᴏᴍᴇᴏɴᴇ ᴇʟsᴇ ᴡɪʟʟ ғɪʟʟ ʏᴏᴜʀ ʜᴇᴀʀᴛ.")
        await callback_query.answer("You chose to decline.", show_alert=True)

# Marry Command with Button Options
@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Cooldown Check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(f"⏳ 𝑷𝒍𝒆𝒂𝒔𝒆 𝒘𝒂𝒊𝒕 {cooldown_time} 𝒔𝒆𝒄𝒐𝒏𝒅𝒔 𝒃𝒆𝒇𝒐𝒓𝒆 𝒂𝒏𝒐𝒕𝒉𝒆𝒓 𝒕𝒓𝒚!", quote=True)
        return

    # Update Cooldown
    cooldowns[user_id] = time.time()

    # Fetch a random waifu for proposal from target rarities
    receiver_id = user_id
    unique_characters = await get_unique_characters(receiver_id)

    if unique_characters:
        character = unique_characters[0]
        img_url = character['img_url']
        caption = (
            f"💖 {mention}, ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴘʀᴏᴘᴏsᴇ ᴛᴏ {character['name']} ғʀᴏᴍ {character['anime']}?\n\n"
            "ᴄʜᴏᴏsᴇ ᴏɴᴇ!"
        )
        
        # Send waifu image with "Yes" and "No" buttons
        buttons = [
            [
                t.InlineKeyboardButton("Yes 💍", callback_data=f"marry:yes:{user_id}"),
                t.InlineKeyboardButton("No 💔", callback_data=f"marry:no:{user_id}")
            ]
        ]
        reply_markup = t.InlineKeyboardMarkup(buttons)

        await message.reply_photo(photo=img_url, caption=caption, reply_markup=reply_markup)
    else:
        await message.reply_text(f"💔 Sorry {mention}, no unique waifus are available right now.")
