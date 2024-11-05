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
        pipeline = [{'$match': filter_query} if filter_query else {}, {'$sample': {'size': CHARACTERS_PER_PAGE}}]
        cursor = source_collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters if characters else []
    except Exception as e:
        print(e)
        return []

# Helper function to generate message content for characters
async def generate_character_message(characters, page, action_type):
    if not characters or page >= len(characters):
        if action_type == "sell":
            return "You don't have any characters available for sale.", [], []
        else:
            return "No characters currently available in the shop.", [], []

    current_character = characters[page]
    price = generate_character_price(action_type)
    text = (
        f"╭──\n"
        f"| ➩ Name: {current_character['name']}\n"
        f"| ➩ ID: {current_character['id']}\n"
        f"| ➩ Anime: {current_character['anime']}\n"
        f"▰▱▰▱▰▱▰▱▰▱\n"
        f"| Price: {price}\n"
    )
    img_url = current_character['img_url']
    media = [InputMediaPhoto(media=img_url, caption="Loading...")]

    action_button = InlineKeyboardButton("Sell 🛒" if action_type == "sell" else "Buy 🛒", callback_data=f"{action_type}_{current_character['id']}_{price}")
    buttons = [[action_button]]

    if page == 0:
        buttons.append([InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}_{action_type}")])
    elif page == len(characters) - 1:
        buttons.append([InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}_{action_type}")])
    else:
        buttons.append([
            InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}_{action_type}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}_{action_type}")
        ])

    buttons.append([InlineKeyboardButton("Refresh 🔄 (100 tokens)", callback_data=f"refresh_{action_type}")])

    return text, media, buttons

# Generate price based on action type
def generate_character_price(action_type):
    return 5000 if action_type == "sell" else 30000  # Default price structure for demo purposes

# Command for shop (buying characters)
@app.on_message(filters.command(["cshop"]))
async def shop(_, message: Message):
    waifus = await get_random_characters(collection)
    text, media, buttons = await generate_character_message(waifus, 0, "buy")
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Command for selling characters
@app.on_message(filters.command(["sell"]))
async def sell(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or 'characters' not in user or not user['characters']:
        return await message.reply_text("You don't have any characters available for sale.")
    
    characters = random.sample(user['characters'], min(CHARACTERS_PER_PAGE, len(user['characters'])))
    text, media, buttons = await generate_character_message(characters, 0, "sell")
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback query handler for pagination and refresh
@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if "next_" in data or "prev_" in data:
        action_type = "buy" if "buy" in data else "sell"
        page = int(data.split("_")[1]) + (1 if "next_" in data else -1)
        
        if action_type == "buy":
            characters = await get_random_characters(collection)
        else:
            user = await user_collection.find_one({'id': user_id})
            characters = user['characters'] if user and 'characters' in user else []
            characters = random.sample(characters, min(CHARACTERS_PER_PAGE, len(characters)))

        text, media, buttons = await generate_character_message(characters, page, action_type)
        await query.message.edit_media(media=media[0])
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif "refresh" in data:
        action_type = "buy" if "buy" in data else "sell"
        user = await user_collection.find_one({'id': user_id})
        
        if user['tokens'] < REFRESH_COST:
            await query.answer("Insufficient tokens for refresh.", show_alert=True)
            return

        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -REFRESH_COST}})
        
        if action_type == "buy":
            characters = await get_random_characters(collection)
        else:
            characters = random.sample(user['characters'], min(CHARACTERS_PER_PAGE, len(user['characters'])))
        
        text, media, buttons = await generate_character_message(characters, 0, action_type)
        await query.message.edit_media(media=media[0])
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer("Characters refreshed!")

    elif "buy_" in data or "sell_" in data:
        # Handle buy/sell transaction logic here
        pass
    elif "cancel" in data:
        await query.message.delete()
