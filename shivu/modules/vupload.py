import urllib.request
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from pymongo import ReturnDocument
from shivu import shivuu as app

# Constants
CHARA_CHANNEL_ID = -1001234567890  # Replace with your channel ID
SUPPORT_CHAT = -1009876543210  # Replace with your support group ID
sudo_users = ["6835013483", "987654321"]  # Replace with your sudo users
user_states = {}
collection = None  # Replace with your MongoDB character collection
rarity_emojis = {"⚜️ Animated": "animated", "⭐ Rare": "rare", "🌟 Ultra Rare": "ultra_rare"}
event_emojis = {"🎉 Event 1": "event1", "🎊 Event 2": "event2"}  # Replace with actual events

# Helper Functions
async def get_next_sequence_number(field: str) -> int:
    # Simulate MongoDB sequence handling
    return 1  # Replace with logic to get the next ID

# Admin Panel
@app.on_message(filters.command("admin_panel") & filters.private)
async def admin_panel(client, message):
    if str(message.from_user.id) in sudo_users:
        total_waifus = await collection.count_documents({})
        total_animes = await collection.distinct("anime")
        total_harems = 0  # Replace with user collection count logic if needed
        admin_message = (
            f"Admin Panel:\n\n"
            f"Total Characters: {total_waifus}\n"
            f"Total Animes: {len(total_animes)}\n"
            f"Total Harems: {total_harems}"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🆕 Add Character", callback_data="add_waifu"),
                 InlineKeyboardButton("Add Anime 🆕", callback_data="add_anime")],
                [InlineKeyboardButton("👾 Anime List", switch_inline_query_current_chat="choose_anime ")]
            ]
        )
        await message.reply_text(admin_message, reply_markup=keyboard)
    else:
        await message.reply_text("You are not authorized to use this command.")

# Add Character Workflow
@app.on_callback_query(filters.regex('^add_waifu$'))
async def add_waifu_callback(client, callback_query):
    await callback_query.message.edit_text(
        "Choose an anime to save the character in:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👾 Search Anime", switch_inline_query_current_chat="choose_anime ")],
             [InlineKeyboardButton("⚔️ Cancel", callback_data="cancel_add_waifu")]]
        )
    )
    user_states[callback_query.from_user.id] = {"state": "selecting_anime"}

@app.on_callback_query(filters.regex('^add_waifu_'))
async def choose_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "awaiting_character_name", "anime": selected_anime}
    await callback_query.message.edit_text(
        f"You've selected {selected_anime}. Now, please enter the new character's name:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_add_waifu")]])
    )

@app.on_message(filters.private & filters.text)
async def receive_text_message(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data and user_data["state"] == "awaiting_character_name":
        user_states[message.from_user.id]["name"] = message.text.strip()
        user_states[message.from_user.id]["state"] = "awaiting_character_rarity"
        await message.reply_text(
            "Now, choose the character's rarity:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(rarity, callback_data=f"select_rarity_{rarity}")]
                 for rarity in rarity_emojis.keys()]
            )
        )

@app.on_callback_query(filters.regex('^select_rarity_'))
async def select_rarity_callback(client, callback_query):
    selected_rarity = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id]["rarity"] = selected_rarity
    user_states[callback_query.from_user.id]["state"] = "awaiting_character_video"
    await callback_query.message.edit_text(
        "Send the character's video now:"
    )

@app.on_message(filters.private & filters.video)
async def receive_video(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data and user_data["state"] == "awaiting_character_video":
        video_file_id = message.video.file_id
        character_id = str(await get_next_sequence_number('character_id')).zfill(2)

        # Build character data
        character = {
            "img_url": video_file_id,
            "name": user_data["name"],
            "anime": user_data["anime"],
            "rarity": user_data["rarity"],
            "id": character_id,
            "event_emoji": user_data.get("event_emoji", ""),
        }

        caption = (
            f"🎌 <b>New Character Added!</b>\n\n"
            f"<b>{user_data['anime']}</b>\n"
            f"<b>ID:</b> {character_id}\n"
            f"<b>Name:</b> {user_data['name']} {character['event_emoji']}\n"
            f"<b>Rarity:</b> {user_data['rarity']}\n\n"
            f"Added by: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        )

        try:
            await app.send_video(
                chat_id=CHARA_CHANNEL_ID,
                video=video_file_id,
                caption=caption,
                parse_mode="html"
            )
            await collection.insert_one(character)
            await message.reply_text("✅ Character added successfully!")
            user_states.pop(message.from_user.id, None)
        except Exception as e:
            await message.reply_text(f"An error occurred while adding the character: {e}")

# Inline Anime Search
@app.on_inline_query()
async def search_anime(client, inline_query: InlineQuery):
    if str(inline_query.from_user.id) not in sudo_users:
        return
    query = inline_query.query.strip().lower()
    if query.startswith("choose_anime "):
        query = query[len("choose_anime "):]
        anime_results = await collection.aggregate([
            {"$match": {"anime": {"$regex": query, "$options": "i"}}},
            {"$group": {"_id": "$anime", "count": {"$sum": 1}}},
            {"$limit": 10}
        ]).to_list(length=None)

        results = [
            InlineQueryResultArticle(
                title=anime["_id"],
                description=f"{anime['count']} Characters",
                input_message_content=InputTextMessageContent(f"Anime: {anime['_id']}\nCharacters: {anime['count']}"),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Add Character", callback_data=f"add_waifu_{anime['_id']}")]]
                )
            ) for anime in anime_results
        ]
        await inline_query.answer(results, cache_time=1)
