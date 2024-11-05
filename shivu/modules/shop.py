from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pymongo import MongoClient
from datetime import datetime
import random
from shivu import user_collection, collection
from shivu import shivuu as app

CHARACTERS_PER_PAGE = 3
REFRESH_COST = 100

async def get_random_characters(source_collection, filter_query=None):
    try:
        pipeline = [{'$match': filter_query} if filter_query else {}, {'$sample': {'size': CHARACTERS_PER_PAGE}}]
        cursor = source_collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters if characters else []
    except Exception as e:
        print(e)
        return []

async def generate_character_message(characters, page, action_type):
    text = ""
    buttons = []
    media = []

    if not characters or page >= len(characters):
        return "No characters available.", [], []

    current_character = characters[page]
    price = generate_character_price(action_type)

    text += f"╭──\n| ➩ {current_character['name']}\n| ➩ ID - {current_character['id']}\n| ➩ {current_character['anime']}\n ▰▱▰▱▰▱▰▱▰▱\n| Price - {price}\n"
    img_url = current_character['img_url']
    media.append(InputMediaPhoto(media=img_url, caption="Loading..."))

    action_button = InlineKeyboardButton("Sell 🛒" if action_type == "sell" else "Buy 🛒", callback_data=f"{action_type}_{current_character['id']}_{price}")
    buttons.append([action_button])

    if page == 0:
        buttons.append([InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}_{action_type}")])
    elif page == len(characters) - 1:
        buttons.append([InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}_{action_type}")])
    else:
        buttons.append([InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}_{action_type}"), InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}_{action_type}")])

    buttons.append([InlineKeyboardButton("Refresh 🔄 (100 tokens)", callback_data=f"refresh_{action_type}")])

    return text, media, buttons

def generate_character_price(action_type):
    return 5000 if action_type == "sell" else 30000  # Default price structure for demo purposes

@app.on_message(filters.command(["cshop"]))
async def shop(_, message: Message):
    user_id = message.from_user.id
    waifus = await get_random_characters(collection)
    text, media, buttons = await generate_character_message(waifus, 0, "buy")
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.command(["sell"]))
async def sell(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or 'characters' not in user or not user['characters']:
        return await message.reply_text("You don't have any characters available for sale.")
    
    characters = random.sample(user['characters'], min(CHARACTERS_PER_PAGE, len(user['characters'])))
    text, media, buttons = await generate_character_message(characters, 0, "sell")
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    action_type = "buy" if "buy" in data else "sell"
    characters = await get_random_characters(collection if action_type == "buy" else user_collection, {'id': user_id})

    if data.startswith("next_") or data.startswith("prev_"):
        page = int(data.split("_")[1]) + (1 if data.startswith("next_") else -1)
    elif data.startswith("refresh"):
        user = await user_collection.find_one({'id': user_id})
        if user['tokens'] < REFRESH_COST:
            await query.answer("Insufficient tokens for refresh.", show_alert=True)
            return
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -REFRESH_COST}})
        characters = await get_random_characters(collection if action_type == "buy" else user_collection, {'id': user_id})
        page = 0
        await query.answer("Characters refreshed!")
    elif data.startswith("buy_") or data.startswith("sell_"):
        # Handle buy/sell transaction logic here
        return
    elif data.startswith("cancel"):
        page = 0

    text, media, buttons = await generate_character_message(characters, page, action_type)
    await query.message.edit_media(media=media[0])
    await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
