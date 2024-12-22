import urllib.request
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from pymongo import MongoClient
from shivu import shivuu as app

# Constants
CHARA_CHANNEL_ID = -1001234567890  # Replace with your channel ID
SUPPORT_CHAT = -1009876543210  # Replace with your support group ID
sudo_users = ["6835013483", "987654321"]  # Replace with your sudo users
user_states = {}
rarity_emojis = {"⚜️ Animated": "animated", "⭐ Rare": "rare", "🌟 Ultra Rare": "ultra_rare"}

# MongoDB Setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["anime_game"]  # Replace with your database name
collection = db["characters"]

# Helper Function to Get Next ID
async def get_next_sequence_number(field: str) -> int:
    sequence_doc = await db["sequences"].find_one_and_update(
        {"_id": field},
        {"$inc": {"value": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    return sequence_doc["value"]

# Admin Panel Command
@app.on_message(filters.command("admin_panel") & filters.private)
async def admin_panel(client, message):
    if str(message.from_user.id) in sudo_users:
        total_characters = await collection.count_documents({})
        total_animes = len(await collection.distinct("anime"))
        admin_message = (
            f"👑 <b>Admin Panel</b>\n\n"
            f"📊 Total Characters: <b>{total_characters}</b>\n"
            f"📚 Total Animes: <b>{total_animes}</b>\n"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ Add Character", callback_data="add_waifu")],
                [InlineKeyboardButton("📖 View Anime List", switch_inline_query_current_chat="search_anime ")],
                [InlineKeyboardButton("🔙 Exit", callback_data="admin_exit")]
            ]
        )
        await message.reply_text(admin_message, reply_markup=keyboard)
    else:
        await message.reply_text("❌ You are not authorized to use this command.")

# Add Character Workflow
@app.on_callback_query(filters.regex("^add_waifu$"))
async def start_add_waifu(client, callback_query):
    user_states[callback_query.from_user.id] = {"state": "selecting_anime"}
    await callback_query.message.edit_text(
        "📚 Please search for the anime to add the character to:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔍 Search Anime", switch_inline_query_current_chat="search_anime ")],
             [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_waifu")]]
        )
    )

@app.on_inline_query()
async def search_anime(client, inline_query: InlineQuery):
    if inline_query.query.lower().startswith("search_anime "):
        query = inline_query.query.replace("search_anime ", "").strip()
        anime_results = await collection.aggregate([
            {"$match": {"anime": {"$regex": query, "$options": "i"}}},
            {"$group": {"_id": "$anime", "count": {"$sum": 1}}},
            {"$limit": 10}
        ]).to_list(length=None)

        results = [
            InlineQueryResultArticle(
                title=anime["_id"],
                description=f"{anime['count']} Characters",
                input_message_content=InputTextMessageContent(f"Anime: {anime['_id']}"),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Select", callback_data=f"select_anime_{anime['_id']}")]]
                )
            ) for anime in anime_results
        ]
        await inline_query.answer(results, cache_time=1)

@app.on_callback_query(filters.regex("^select_anime_"))
async def select_anime(client, callback_query):
    anime_name = callback_query.data.split("_", 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "awaiting_character_name", "anime": anime_name}
    await callback_query.message.edit_text(
        f"✅ Anime selected: <b>{anime_name}</b>\n\nPlease enter the character's name:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_waifu")]])
    )

@app.on_message(filters.private & filters.text)
async def handle_character_name(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data and user_data["state"] == "awaiting_character_name":
        user_data["name"] = message.text.strip()
        user_data["state"] = "awaiting_character_rarity"
        await message.reply_text(
            "📌 Select the character's rarity:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(rarity, callback_data=f"select_rarity_{rarity}")]
                 for rarity in rarity_emojis.keys()]
            )
        )

@app.on_callback_query(filters.regex("^select_rarity_"))
async def select_rarity(client, callback_query):
    rarity = callback_query.data.split("_", 2)[-1]
    user_states[callback_query.from_user.id]["rarity"] = rarity
    user_states[callback_query.from_user.id]["state"] = "awaiting_character_video"
    await callback_query.message.edit_text("📽️ Send the character's video:")

@app.on_message(filters.private & filters.video)
async def handle_character_video(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data and user_data["state"] == "awaiting_character_video":
        character_id = str(await get_next_sequence_number("character_id")).zfill(4)
        character = {
            "id": character_id,
            "name": user_data["name"],
            "anime": user_data["anime"],
            "rarity": user_data["rarity"],
            "video_file_id": message.video.file_id
        }

        caption = (
            f"🎉 <b>New Character Added!</b>\n\n"
            f"🎬 <b>Anime:</b> {user_data['anime']}\n"
            f"🆔 <b>ID:</b> {character_id}\n"
            f"📛 <b>Name:</b> {user_data['name']}\n"
            f"✨ <b>Rarity:</b> {user_data['rarity']}"
        )

        try:
            await app.send_video(
                chat_id=CHARA_CHANNEL_ID,
                video=message.video.file_id,
                caption=caption,
                parse_mode="html"
            )
            await collection.insert_one(character)
            await message.reply_text("✅ Character added successfully!")
            user_states.pop(message.from_user.id, None)
        except Exception as e:
            await message.reply_text(f"❌ Failed to add character: {e}")
