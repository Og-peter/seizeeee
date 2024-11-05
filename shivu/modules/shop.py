from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pymongo import MongoClient
from datetime import datetime
import random
from shivu import user_collection
from shivu import shivuu as app

# Constants
CHARACTERS_PER_PAGE = 3
RARITIES = ['🔮 Limited Edition', '🟡 Legendary', '🫧 Premium']
REFRESH_COST = 100

# Helper function for calculating prices based on rarity
def calculate_price(rarity, sell=False):
    base_price = {
        '🔮 Limited Edition': 50000,
        '🟡 Legendary': 30000,
        '🫧 Premium': 70000
    }.get(rarity, 5000)
    return int(base_price * 0.5) if sell else base_price

# Generate Random Characters for Shop
async def get_random_characters():
    characters = []
    for rarity in RARITIES:
        character = {
            'id': random.randint(1000, 9999),
            'name': f"Random Character {random.randint(1, 100)}",
            'rarity': rarity,
            'img_url': f"https://dummyimage.com/300x300/000/fff&text={rarity.replace(' ', '+')}"
        }
        characters.append(character)
    return characters

# Sell Function: Get User's Characters
async def get_user_characters(user_id, page):
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user or not user['characters']:
        return "No characters to sell.", [], []

    start = page * CHARACTERS_PER_PAGE
    characters = user['characters'][start:start + CHARACTERS_PER_PAGE]

    message_text = "Your characters available for sale:\n\n"
    button_layout = []
    media_content = []

    for char in characters:
        price = calculate_price(char['rarity'], sell=True)
        message_text += f"• {char['name']} (ID: {char['id']})\n  Rarity: {char['rarity']}\n  Sell Price: {price} tokens\n\n"
        button_layout.append([
            InlineKeyboardButton(f"Sell {char['name']} 💸", callback_data=f"sell_{char['id']}_{price}")
        ])
        media_content.append(InputMediaPhoto(media=char['img_url'], caption="Character for Sale"))

    if len(user['characters']) > CHARACTERS_PER_PAGE:
        if start + CHARACTERS_PER_PAGE < len(user['characters']):
            button_layout.append([InlineKeyboardButton("Next ➡️", callback_data=f"sell_next_{page}")])
        if page > 0:
            button_layout[-1].insert(0, InlineKeyboardButton("⬅️ Back", callback_data=f"sell_prev_{page}"))

    button_layout.append([InlineKeyboardButton("Refresh 🔄 (100 tokens)", callback_data="sell_refresh")])

    return message_text, media_content, button_layout

# Command to Display Shop Items
@app.on_message(filters.command("shop"))
async def display_shop(_, message: Message):
    waifus = await get_random_characters()
    page = 0

    if not waifus:
        await message.reply_text("No characters available in the shop.")
        return

    character = waifus[page]
    text = f"{character['name']} (ID: {character['id']})\n{character['rarity']}\nPrice: {calculate_price(character['rarity'])} tokens"
    media = InputMediaPhoto(media=character['img_url'], caption=text)
    
    buttons = [
        [InlineKeyboardButton("Buy 🛒", callback_data=f"buy_{character['id']}_{calculate_price(character['rarity'])}")],
        [InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")],
        [InlineKeyboardButton("Refresh 🔄 (100 tokens)", callback_data="refresh")]
    ]
    
    await message.reply_photo(photo=character['img_url'], caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Command to Display Sell Options
@app.on_message(filters.command("sell"))
async def display_sell(_, message: Message):
    user_id = message.from_user.id
    page = 0

    text, media, buttons = await get_user_characters(user_id, page)
    if text == "No characters to sell.":
        await message.reply_text(text)
    else:
        await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback Handler for Shop and Sell
@app.on_callback_query()
async def callback_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data.startswith("next_") or data.startswith("prev_"):
        page = int(data.split("_")[1])
        waifus = await get_random_characters()
        text, media, buttons = await generate_message(waifus, page, "buy")
        await query.message.edit_media(media=media)
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("buy_"):
        char_id, price = data.split("_")[1], int(data.split("_")[2])
        # Your buying logic goes here...

    elif data == "refresh":
        user = await user_collection.find_one({'id': user_id})
        if user['tokens'] >= REFRESH_COST:
            await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -REFRESH_COST}})
            waifus = await get_random_characters()
            page = 0
            text, media, buttons = await generate_message(waifus, page, "buy")
            await query.message.edit_media(media=media)
            await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
            await query.answer("Characters refreshed!")
        else:
            await query.answer("Insufficient tokens for refresh.", show_alert=True)

    elif data.startswith("sell_next_") or data.startswith("sell_prev_"):
        page = int(data.split("_")[2])
        text, media, buttons = await get_user_characters(user_id, page)
        await query.message.edit_media(media=media[0])
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("sell_"):
        char_id, price = data.split("_")[1], int(data.split("_")[2])
        # Handle selling character

    elif data == "sell_refresh":
        user = await user_collection.find_one({'id': user_id})
        if user['tokens'] >= REFRESH_COST:
            await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -REFRESH_COST}})
            page = 0
            text, media, buttons = await get_user_characters(user_id, page)
            await query.message.edit_media(media=media[0])
            await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
            await query.answer("Characters refreshed!")
        else:
            await query.answer("Insufficient tokens for refresh.", show_alert=True)

async def generate_message(characters, page, action_type):
    if not characters or page >= len(characters):
        return "No characters available.", None, []

    current_char = characters[page]
    price = calculate_price(current_char['rarity'])

    text = f"{current_char['name']} (ID: {current_char['id']})\n{current_char['rarity']}\nPrice: {price} tokens"
    media = InputMediaPhoto(media=current_char['img_url'], caption=text)

    buttons = [
        [InlineKeyboardButton("Buy 🛒", callback_data=f"buy_{current_char['id']}_{price}")],
        [InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")],
        [InlineKeyboardButton("Refresh 🔄 (100 tokens)", callback_data="refresh" if action_type == "buy" else "sell_refresh")]
    ]

    return text, media, buttons
