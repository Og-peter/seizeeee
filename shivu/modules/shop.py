from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, InputMediaPhoto
from pymongo import MongoClient
from datetime import datetime
import random
from shivu import user_collection, collection
from shivu import shivuu as app

WAIFU_PER_PAGE = 3
RARITIES = ['🔮 Limited Edition', '🟡 Legendary']
ALLOWED_GROUP_ID = -1002104939708

sessions = {}

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
    if rarity == '🔮 Limited Edition':
        return 50000
    elif rarity == '🟡 Legendary':
        return 30000
    else:
        return 5000

async def generate_waifu_message(waifus, page):
    text = ""
    buttons = []
    media = []

    if not waifus or page >= len(waifus):
        return "No characters available.", [], []

    current_waifu = waifus[page]
    price = generate_waifu_price(current_waifu['rarity'])

    text += f"╭──\n| ➩ {current_waifu['name']}\n| ➩ ID -  {current_waifu['id']}\n| ➩ {current_waifu['anime']}\n| ➩ {current_waifu['rarity']}\n ▰▱▰▱▰▱▰▱▰▱\n| Price - {price}\n"
    buttons.append([InlineKeyboardButton("Buy 🛒", callback_data=f"buy_{current_waifu['id']}_{price}")])

    img_url = current_waifu['img_url']
    media.append(InputMediaPhoto(media=img_url, caption="Loading..."))

    if page == 0:
        buttons.append([
            InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")
        ])
    elif page == len(waifus) - 1:
        buttons.append([
            InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{page}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"next_{page}")
        ])

    return text, media, buttons

@app.on_message(filters.command(["cshop"]))
async def shop(_, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_id != ALLOWED_GROUP_ID:
        return await message.reply_text("This command is exclusive to the @dynamic_gangs group.")

    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'characters': [],
            'tokens': 0,
            'last_shop_access': None
        }
        await user_collection.insert_one(user)
    else:
        if 'tokens' not in user:
            await user_collection.update_one({'id': user_id}, {'$set': {'tokens': 0}})
            user['tokens'] = 0

    now = datetime.now()
    last_shop_access = user.get('last_shop_access')

    if not last_shop_access or (now - last_shop_access).total_seconds() >= 86400:
        waifus = await get_waifus_with_different_rarities()
        sessions[user_id] = {"waifus": waifus, "page": 0}
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'last_shop_access': now}}
        )
    else:
        waifus = sessions.get(user_id, {}).get("waifus", [])

    if not waifus:
        waifus = await get_waifus_with_different_rarities()
        sessions[user_id] = {"waifus": waifus, "page": 0}

    text, media, buttons = await generate_waifu_message(waifus, 0)
    await message.reply_photo(photo=media[0].media, caption=text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if user_id not in sessions:
        await query.answer("Please use the /cshop command first.")
        return

    session = sessions.get(user_id, {})
    waifus = session.get("waifus", [])
    page = session.get("page", 0)

    if query.message.reply_to_message and user_id != query.message.reply_to_message.from_user.id:
        await query.answer("This session is not yours.", show_alert=True)
        return

    if data.startswith("next_"):
        page += 1
        if page >= len(waifus):
            page = len(waifus) - 1
        sessions[user_id]["page"] = page
    elif data.startswith("prev_"):
        page -= 1
        if page < 0:
            page = 0
        sessions[user_id]["page"] = page
    elif data.startswith("buy_"):
        _, waifu_id, price = data.split("_")
        buttons = [
            [InlineKeyboardButton("Confirm ✅", callback_data=f"confirm_{waifu_id}_{price}")],
            [InlineKeyboardButton("Back", callback_data=f"cancel")]
        ]
        await query.message.edit_caption(caption="Click below to confirm your purchase", reply_markup=InlineKeyboardMarkup(buttons))
        return
    elif data.startswith("confirm_"):
        _, waifu_id, price = data.split("_")
        price = int(price)

        user = await user_collection.find_one({'id': user_id})
        if not user:
            await query.message.edit_caption(caption="User not found.")
            return

        if 'tokens' not in user:
            await user_collection.update_one({'id': user_id}, {'$set': {'tokens': 0}})
            user['tokens'] = 0

        if any(character['id'] == waifu_id for character in user['characters']):
            await query.message.edit_caption(caption="You already own this character.")
            return

        if user['tokens'] < price:
            await query.message.edit_caption(caption="Insufficient tokens. You need more tokens to purchase this character.")
            return

        waifu = next((w for w in waifus if w['id'] == waifu_id), None)
        if not waifu:
            await query.message.edit_caption(caption="Character not found.")
            return

        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': waifu}, '$inc': {'tokens': -price}}
        )
        await query.message.edit_caption(caption="Purchase confirmed ✅")
        return
    elif data.startswith("cancel"):
        page = session.get("page", 0)

    text, media, buttons = await generate_waifu_message(waifus, page)
    await query.message.edit_media(media=media[0])
    await query.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(buttons))
