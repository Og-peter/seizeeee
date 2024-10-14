from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivu import collection, user_collection, shivuu as app
import math
import random

# Global dictionary to store user data
user_data = {}

# Start the harem mode and show sorting options
async def hmode(client, message):
    user_id = message.from_user.id
    user_data[user_id] = user_id  # Store the user ID in global user_data

    keyboard = [
        [InlineKeyboardButton("🍜 Sort By Rarity", callback_data="sort_rarity")],
        [InlineKeyboardButton("🔠 Sort By Name", callback_data="sort_name")],
        [InlineKeyboardButton("📺 Sort By Anime", callback_data="sort_anime")],
        [InlineKeyboardButton("🎲 Random Character", callback_data="random_character")],
        [InlineKeyboardButton("🌐 Reset Preferences", callback_data="reset_preferences")],
        [InlineKeyboardButton("🚮 Close", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_photo(
        photo="https://telegra.ph/file/1fc98964f8a467b947853.jpg",
        caption="Set Your Harem Mode:",
        reply_markup=reply_markup,
    )

@app.on_callback_query(filters.regex(r'^sort_'))
async def hmode_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    if user_id != hmode_user_id:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await callback_query.answer("You have not seized any characters yet.", show_alert=True)
        return

    if data == "close":
        await callback_query.message.delete()
    elif data == "sort_rarity":
        await send_rarity_preferences(callback_query)
    elif data in ["sort_name", "sort_anime"]:
        sort_by = data.split("_")[1]
        await send_sorted_characters(callback_query, sort_by=sort_by)
    elif data == "random_character":
        await send_random_character(callback_query)

async def send_rarity_preferences(callback_query: CallbackQuery):
    rarity_order = [
        "⚪️ Common", "🔮 Limited Edition", "🫧 Premium", "🌸 Exotic", "💮 Exclusive",
        "👶 Chibi", "🟡 Legendary", "🟠 Rare", "🔵 Medium", "🎐 Astral", "💞 Valentine"
    ]
    keyboard = [[InlineKeyboardButton(rarity, callback_data=f"rarity_{rarity}")] for rarity in rarity_order]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.edit_text("🎴 Choose Your Preferred Rarity.", reply_markup=reply_markup)

async def send_sorted_characters(callback_query: CallbackQuery, sort_by, page=1):
    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    characters = user.get('characters', [])

    if sort_by == "name":
        characters.sort(key=lambda c: c.get("name", "Unknown Name"))
    elif sort_by == "anime":
        characters.sort(key=lambda c: c.get("anime", "Unknown Anime"))
    elif sort_by == "rarity":
        characters.sort(key=lambda c: c.get("rarity", "Unknown Rarity"))

    characters_per_page = 10
    total_pages = math.ceil(len(characters) / characters_per_page)
    start = (page - 1) * characters_per_page
    end = start + characters_per_page

    sorted_list = "\n".join([f"{c['name']} from {c['anime']}" for c in characters[start:end]])
    navigation_buttons = [
        InlineKeyboardButton("⬅️ Prev", callback_data=f"sort_{sort_by}_prev_{page-1}") if page > 1 else None,
        InlineKeyboardButton("➡️ Next", callback_data=f"sort_{sort_by}_next_{page+1}") if page < total_pages else None
    ]
    
    reply_markup = InlineKeyboardMarkup([list(filter(None, navigation_buttons))])
    await callback_query.message.edit_text(f"Sorted by {sort_by.capitalize()}:\n\n{sorted_list[:2000]}", reply_markup=reply_markup)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r'sort_(name|anime|rarity)_(prev|next)_(\d+)'))
async def paginate_sorted_characters(client, callback_query: CallbackQuery):
    data = callback_query.data.split('_')
    sort_by = data[1]
    direction = data[2]
    page = int(data[3])

    new_page = page - 1 if direction == "prev" else page + 1
    await send_sorted_characters(callback_query, sort_by=sort_by, page=new_page)

async def send_random_character(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    characters = user.get('characters', [])
    
    if not characters:
        await callback_query.answer("You have no characters in your collection.", show_alert=True)
        return

    random_character = random.choice(characters)
    caption = (f"🎲 Randomly Selected:\n\n🧃 Name: {random_character['name']}\n"
               f"⚜️ Anime: {random_character['anime']}\n"
               f"🥂 Rarity: {random_character['rarity']}")

    await callback_query.message.reply_photo(photo=random_character.get("img_url"), caption=caption)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r'^favorite_character$'))
async def favorite_character(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    characters = user.get('characters', [])

    if not characters:
        await callback_query.answer("You have no characters to favorite.", show_alert=True)
        return

    random_character = random.choice(characters)
    await user_collection.update_one({'id': user_id}, {'$set': {'favorite_character': random_character}})
    await callback_query.message.edit_text(f"🌟 {random_character['name']} from {random_character['anime']} is now your favorite character!")
    await callback_query.answer()

@app.on_callback_query(filters.regex(r'^rarity_'))
async def rarity_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    rarity = callback_query.data.split("_")[1]

    if user_id != user_data.get(user_id):
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'rarity_preference': rarity}})
    await callback_query.message.edit_text("Harem Interface Changed Successfully")
    await send_sorted_characters(callback_query, sort_by="rarity")

@app.on_callback_query(filters.regex(r'reset_preferences'))
async def reset_preferences(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id != user_data.get(user_id):
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'rarity_preference': ''}})
    await callback_query.message.edit_text("🌋 Your Rarity Preferences Have Been Reset Successfully!")
    await hmode(client, callback_query.message)

@app.on_message(filters.command("hmode"))
async def hmode_command(client, message):
    await hmode(client, message)

@app.on_message(filters.command("reset_preferences"))
async def reset_preferences_command(client, message):
    await reset_preferences(client, message)
