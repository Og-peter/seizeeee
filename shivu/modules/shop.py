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
        # Build the pipeline correctly to avoid an empty stage
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
async def generate_character_message(characters, page, action_type):
    if not characters or page >= len(characters):
        return "No characters available.", [], []

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
    if not waifus:
        return await message.reply_text("No characters available for purchase.")
    
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

# Callback query handler for pagination, refresh, buy, and sell actions
@app.on_callback_query()
async def callback_query_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if "next_" in data or "prev_" in data:
        # Handle pagination
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
        # Handle refresh
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
        action_type, character_id, price = data.split("_")
        price = int(price)
        user = await user_collection.find_one({'id': user_id})

        if action_type == "buy":
            # Check if user has enough tokens to buy
            if user['tokens'] < price:
                await query.answer("Insufficient tokens to buy this character.", show_alert=True)
                return

            # Deduct tokens and add character to user collection
            await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': -price}, '$push': {'characters': {'id': character_id}}})
            await query.answer("Character purchased successfully!")
            await query.message.delete()

            # Send DM with character details
            character = next((char for char in await get_random_characters(collection, {'id': character_id}) if char['id'] == character_id), None)
            if character:
                dm_text = (
                    f"You have successfully purchased:\n\n"
                    f"╭──\n"
                    f"| ➩ Name: {character['name']}\n"
                    f"| ➩ ID: {character['id']}\n"
                    f"| ➩ Anime: {character['anime']}\n"
                    f"▰▱▰▱▰▱▰▱▰▱\n"
                    f"| Price: {price} tokens\n"
                )
                await app.send_photo(user_id, photo=character['img_url'], caption=dm_text)

        elif action_type == "sell":
            # Check if character exists in user's collection
            if any(char['id'] == character_id for char in user['characters']):
                # Add tokens and remove character from user collection
                await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': price}, '$pull': {'characters': {'id': character_id}}})
                await query.answer("Character sold successfully!")
                await query.message.delete()

                # Send DM with character details
                character = next((char for char in user['characters'] if char['id'] == character_id), None)
                if character:
                    dm_text = (
                        f"You have successfully sold:\n\n"
                        f"╭──\n"
                        f"| ➩ Name: {character['name']}\n"
                        f"| ➩ ID: {character['id']}\n"
                        f"| ➩ Anime: {character['anime']}\n"
                        f"▰▱▰▱▰▱▰▱▰▱\n"
                        f"| Price: {price} tokens\n"
                    )
                    await app.send_photo(user_id, photo=character['img_url'], caption=dm_text)
            else:
                await query.answer("Character not found in your collection.", show_alert=True)

    elif "cancel" in data:
        await query.message.delete()
