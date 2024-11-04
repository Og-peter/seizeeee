from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from shivu import user_collection, collection
from shivu import shivuu as app

WAIFU_PER_PAGE = 3
RARITIES = ['🔮 Limited Edition', '🟡 Legendary']
ALLOWED_GROUP_ID = -1002104939708
DAILY_TOKEN_BONUS = 1000

async def get_waifus_with_different_rarities():
    try:
        waifus = []
        for rarity in RARITIES:
            pipeline = [
                {'$match': {'rarity': rarity}},
                {'$sample': {'size': 1}}
            ]
            cursor = collection.aggregate(pipeline)
            characters = await cursor.to_list(length=None)
            if characters:
                waifus.append(characters[0])
        return waifus
    except Exception as e:
        print(e)
        return []

def generate_waifu_price(rarity):
    return 50000 if rarity == '🔮 Limited Edition' else 30000 if rarity == '🟡 Legendary' else 5000

async def generate_waifu_message(waifus, page):
    if not waifus or page >= len(waifus):
        return "No characters available.", [], []

    current_waifu = waifus[page]
    price = generate_waifu_price(current_waifu['rarity'])
    
    text = f"╭──\n| ➩ {current_waifu['name']}\n| ➩ ID -  {current_waifu['id']}\n| ➩ {current_waifu['anime']}\n| ➩ {current_waifu['rarity']}\n"
    text += f"| Price - {price}\n▰▱▰▱▰▱▰▱▰▱\n"
    
    buttons = [[InlineKeyboardButton("Buy 🛒", callback_data=f"buy_{current_waifu['id']}_{price}")]]
    if page == 0:
        buttons.append([InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")])
    elif page == len(waifus) - 1:
        buttons.append([InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}")])
    else:
        buttons.append([
            InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")
        ])

    media = [InputMediaPhoto(media=current_waifu['img_url'], caption="Loading...")]
    return text, media, buttons

@app.on_message(filters.command(["cshop"]))
async def shop(_, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_id != ALLOWED_GROUP_ID:
        return await message.reply_text("This command is exclusive to the @dynamic_gangs group.")
    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {'id': user_id, 'characters': [], 'tokens': DAILY_TOKEN_BONUS, 'last_shop_access': None}
        await user_collection.insert_one(user)
        first_access = True
    else:
        first_access = False
        if 'tokens' not in user:
            await user_collection.update_one({'id': user_id}, {'$set': {'tokens': 0}})
            user['tokens'] = 0

    now = datetime.now()
    last_access = user.get('last_shop_access')
    if not last_access or now - last_access >= timedelta(days=1):
        waifus = await get_waifus_with_different_rarities()
        user['tokens'] += DAILY_TOKEN_BONUS if not first_access else 0
        await user_collection.update_one({'id': user_id}, {'$set': {'last_shop_access': now, 'tokens': user['tokens']}})
    else:
        waifus = user.get("daily_waifus", [])

    text, media, buttons = await generate_waifu_message(waifus, 0)
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    user = await user_collection.find_one({'id': user_id})
    waifus = user.get("daily_waifus", [])
    page = user.get("page", 0)

    if data.startswith("next_"):
        page += 1
        page = min(page, len(waifus) - 1)
    elif data.startswith("prev_"):
        page -= 1
        page = max(page, 0)
    elif data.startswith("buy_"):
        _, waifu_id, price = data.split("_")
        price = int(price)
        
        # Show confirm and cancel options
        confirm_buttons = [
            [InlineKeyboardButton("Confirm ✅", callback_data=f"confirm_{waifu_id}_{price}")],
            [InlineKeyboardButton("Cancel ❌", callback_data="cancel")]
        ]
        await query.message.edit_caption(
            caption=f"Are you sure you want to buy this character for {price} tokens?",
            reply_markup=InlineKeyboardMarkup(confirm_buttons)
        )
        return
    elif data.startswith("confirm_"):
        _, waifu_id, price = data.split("_")
        price = int(price)

        if user['tokens'] < price:
            await query.message.edit_caption("Insufficient tokens.")
            return
        if any(char['id'] == waifu_id for char in user['characters']):
            await query.message.edit_caption("Character already owned.")
            return
        
        waifu = next((w for w in waifus if w['id'] == waifu_id), None)
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': waifu}, '$inc': {'tokens': -price}}
        )
        await query.message.edit_caption("Purchase confirmed ✅")
        return
    elif data == "cancel":
        # Return to waifu list if the purchase is canceled
        text, media, buttons = await generate_waifu_message(waifus, page)
        await query.message.edit_media(media=media[0])
        await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
    
    text, media, buttons = await generate_waifu_message(waifus, page)
    await query.message.edit_media(media=media[0])
    await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
