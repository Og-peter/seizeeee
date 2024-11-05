from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pymongo import MongoClient
import random
from shivu import user_collection, collection
from shivu import shivuu as app

CHARACTERS_PER_PAGE = 3
REFRESH_COST = 100

# Helper function to fetch random characters from the collection
async def get_random_characters(source_collection, filter_query=None):
    try:
        pipeline = []
        if filter_query:
            pipeline.append({'$match': filter_query})
        pipeline.append({'$sample': {'size': CHARACTERS_PER_PAGE}})
        cursor = source_collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters if characters else []
    except Exception as e:
        print(e)
        return []

# Helper function to generate message content for characters
async def generate_character_message(characters, page, action_type, user_mention):
    if not characters or page >= len(characters):
        return f"{user_mention}, no characters available.", [], []

    current_character = characters[page]
    price = generate_character_price(action_type)
    text = (
        f"╭──\n"
        f"| ➩ 🥂 ɴᴀᴍᴇ: {current_character['name']}\n"
        f"| ➩ ✨ ɪᴅ: {current_character['id']}\n"
        f"| ➩ ⛩️ ᴀɴɪᴍᴇ: {current_character['anime']}\n"
        f"▰▱▱▱▱▱▱▱▱▱▰\n"
        f"| 🍃 ᴘʀɪᴄᴇ: {price} ᴛᴏᴋᴇɴs\n"
        f"Requested by: {user_mention}"
    )
    img_url = current_character['img_url']
    media = [InputMediaPhoto(media=img_url, caption="Loading...")]

    action_button = InlineKeyboardButton("sᴇʟʟ 🛒" if action_type == "sell" else "Buy 🛒", callback_data=f"{action_type}_char_{current_character['id']}_{price}")
    buttons = [[action_button]]

    if page == 0:
        buttons.append([InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"{action_type}_next_{page}")])
    elif page == len(characters) - 1:
        buttons.append([InlineKeyboardButton("⬅️ ᴘʀᴇᴠ", callback_data=f"{action_type}_prev_{page}")])
    else:
        buttons.append([
            InlineKeyboardButton("⬅️ ᴘʀᴇᴠ", callback_data=f"{action_type}_prev_{page}"),
            InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"{action_type}_next_{page}")
        ])

    buttons.append([InlineKeyboardButton("ʀᴇғʀᴇsʜ 🔄 (100 ᴛᴏᴋᴇɴs)", callback_data=f"{action_type}_refresh")])

    return text, media, buttons

# Generate price based on action type
def generate_character_price(action_type):
    return 5000 if action_type == "sell" else 30000

# Command for shop (buying characters)
@app.on_message(filters.command(["cshop"]))
async def shop(_, message: Message):
    user_id = message.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    waifus = await get_random_characters(collection)
    if not waifus:
        return await message.reply_text(f"{user_mention}, no characters available for purchase.")
    
    text, media, buttons = await generate_character_message(waifus, 0, "buy", user_mention)
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Command for selling characters
@app.on_message(filters.command(["sell"]))
async def sell(_, message: Message):
    user_id = message.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    user = await user_collection.find_one({'id': user_id})

    if not user or 'characters' not in user or not user['characters']:
        return await message.reply_text(f"{user_mention}, you don't have any characters available for sale.")
    
    characters = random.sample(user['characters'], min(CHARACTERS_PER_PAGE, len(user['characters'])))
    text, media, buttons = await generate_character_message(characters, 0, "sell", user_mention)
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback query handler for pagination, refresh, buy, and sell actions
@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{query.from_user.first_name}</a>"
    data = query.data.split("_")
    action_type, action = data[0], data[1]

    if action == "next" or action == "prev":
        page = int(data[2]) + (1 if action == "next" else -1)
        characters = await get_random_characters(collection) if action_type == "buy" else await user_collection.find_one({'id': user_id}).get('characters', [])
        
        text, media, buttons = await generate_character_message(characters, page, action_type, user_mention)
        await query.message.edit_media(media=media[0])
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif action == "refresh":
        # Refresh logic here, similar to above
        pass

    elif action == "char":
        # Handle buy/sell character actions here
        pass
