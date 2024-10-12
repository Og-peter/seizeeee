import re
import time
import logging
from html import escape
from cachetools import TTLCache
from pymongo import DESCENDING
from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode
from shivu import user_collection, collection, application, db
import asyncio

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Define a lock for concurrency control
lock = asyncio.Lock()

# Ensure the necessary indexes are created
db.characters.create_index([('id', DESCENDING)])
db.characters.create_index([('anime', DESCENDING)])
db.characters.create_index([('img_url', DESCENDING)])

db.user_collection.create_index([('characters.id', DESCENDING)])
db.user_collection.create_index([('characters.name', DESCENDING)])
db.user_collection.create_index([('characters.img_url', DESCENDING)])

# Initialize caches
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)
character_id_cache = TTLCache(maxsize=10000, ttl=600)

# Function to clear the caches
def clear_all_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()
    character_id_cache.clear()

# Call the function to clear the caches
clear_all_caches()

# Define the rarity emojis mapping
rarity_emojis = {
    '⚪️ Common': {'emoji': '⚪️', 'name': 'Common'},
    '🔮 Limited Edition': {'emoji': '🔮', 'name': 'Limited Edition'},
    '🫧 Premium': {'emoji': '🫧', 'name': 'Premium'},
    '🌸 Exotic': {'emoji': '🌸', 'name': 'Exotic'},
    '💮 Exclusive': {'emoji': '💮', 'name': 'Exclusive'},
    '👶 Chibi': {'emoji': '👶', 'name': 'Chibi'},
    '🟡 Legendary': {'emoji': '🟡', 'name': 'Legendary'},
    '🟠 Rare': {'emoji': '🟠', 'name': 'Rare'},
    '🔵 Medium': {'emoji': '🔵', 'name': 'Medium'},
    '🎐 Astral': {'emoji': '🎐', 'name': 'Astral'},
    '💞 Valentine': {'emoji': '💞', 'name': 'Valentine'}
}

def get_rarity_formatted(rarity):
    rarity_data = rarity_emojis.get(rarity, {'emoji': '', 'name': ''})
    return f"{rarity_data['emoji']} ʀᴀʀɪᴛʏ: <b>{rarity_data['name']}</b>"

async def inlinequery(update: Update, context: CallbackContext) -> None:
    async with lock:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        # Load 3 results per row
        results_per_row = 4
        results_per_page = 8
        start_index = offset
        end_index = offset + results_per_page

        if query.startswith('collection.'):
            user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
            if user_id.isdigit():
                if user_id in user_collection_cache:
                    user = user_collection_cache[user_id]
                else:
                    user = await user_collection.find_one({'id': int(user_id)})
                    user_collection_cache[user_id] = user

                if user:
                    all_characters = list({v.get('id'): v for v in user['characters']}.values())
                    if search_terms:
                        regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                        all_characters = [character for character in all_characters if regex.search(character.get('name', '')) or regex.search(character.get('anime', ''))]
                else:
                    all_characters = []
                    logging.warning(f"Invalid user_id format: {user_id}")
            else:
                all_characters = []
                logging.warning(f"Invalid user_id format: {user_id}")
        else:
            if query:
    if query in all_characters_cache:
        all_characters = all_characters_cache[query]
    else:
        regex = re.compile(query, re.IGNORECASE)
        all_characters = list(await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=None))
        all_characters_cache[query] = all_characters  # Cache the result for future use
            else:
                if 'all_characters' in all_characters_cache:
                    all_characters = all_characters_cache['all_characters']
                else:
                    all_characters = list(await collection.find({}).to_list(length=None))
                    all_characters_cache['all_characters'] = all_characters
        # Ensure no duplicate characters in the results
        unique_characters = {char['id']: char for char in all_characters if isinstance(char, dict) and 'id' in char}.values()
        # Slice the characters based on the current offset and results per page
        characters = list(unique_characters)[start_index:end_index]
        # Calculate the next offset
        next_offset = str(end_index) if len(characters) == results_per_page else ""
        results = []
        for character in characters:
            counts = await user_collection.aggregate([
    {'$match': {'characters.id': character['id']}},
    {'$group': {'_id': '$characters.anime', 'global_count': {'$sum': 1}}},
]).to_list(length=None)

global_count = counts[0]['global_count'] if counts else 0
anime_characters = counts[0]['_id'] if counts else 0  # Adjust this based on your data structure
            anime_characters = await collection.count_documents({'anime': character['anime']})

            rarity_formatted = get_rarity_formatted(character.get('rarity', ''))

            if query.startswith('collection.'):
                user_character_count = sum(c.get('id') == character.get('id') for c in user['characters'])
                user_anime_characters = sum(c.get('anime') == character.get('anime') for c in user['characters'])
                caption = (f"<b> OᴡO ! ᴄʜᴇᴄᴋ ᴏᴜᴛ <a href='tg://user?id={user['id']}'>{(escape(user.get('first_name', user['id'])))}</a> sᴀɴ ᴄʜᴀʀᴀᴄᴛᴇʀ 🏮!</b>\n\n"
                           f"⚜️ ɴᴀᴍᴇ: <b>{character['name']} (x{user_character_count})</b>\n"
                           f"⛩️ ᴀɴɪᴍᴇ: <b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n"
                           f"{rarity_formatted}\n\n"
                           f"<b>🍜 ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ:</b> {character['id']}")
                # Check for tags in character's name
                if '🐰' in character['name']:
                    caption += "\n\n🐰 𝑩𝒖𝒏𝒏𝒚 🐰"
                elif '👩‍🏫' in character['name']:
                    caption += "\n\n👩‍🏫 𝑻𝒆𝒂𝒄𝒉𝒆𝒓 👩‍🏫"
                elif '🎒' in character['name']:
                    caption += "\n\n🎒 𝑺𝒄𝒉𝒐𝒐𝒍 🎒"
                elif '👘' in character['name']:
                    caption += "\n\n👘 𝑲𝒊𝒎𝒐𝒏𝒐 👘"
                elif '🏖' in character['name']:
                    caption += "\n\n🏖 𝑺𝒖𝒎𝒎𝒆𝒓 🏖"
                elif '🎄' in character['name']:
                    caption += "\n\n🎄 𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔 🎄"
                elif '🧹' in character['name']:
                    caption += "\n\n🧹 𝑴𝒂𝒊𝒅 🧹"
                elif '🥻' in character['name']:
                    caption += "\n\n🥻 𝑺𝒂𝒓𝒆𝒆 🥻"
                elif '🩺' in character['name']:
                    caption += "\n\n🩺 𝑵𝒖𝒓𝒔𝒆 🩺"
                elif '☃️' in character['name']:
                    caption += "\n\n☃️ 𝑾𝒊𝒏𝒕𝒆𝒓 ☃️"
            else:
                caption = (f"<b> 🧃OᴡO ! ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ !</b>\n\n"
                           f"🫧 ɴᴀᴍᴇ: <b>{character['name']}</b>\n"
                           f"🦄 ᴀɴɪᴍᴇ: <b>{character['anime']}</b>\n"
                           f"{rarity_formatted}\n\n"
                           f"🌏This Character Seized Globally: <b>{global_count} Times</b>\n\n"
                           f"❄️ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ: <b>{character['id']}</b>")
                unique_id = str(time.time())  # Unique identifier for cache
                character_id_cache[unique_id] = character['id']  # Store the character ID in cache
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("★ ᴡʜᴏ ᴄᴏʟʟᴇᴄᴛᴇᴅ ★", callback_data=f"top_grabbers:{unique_id}")]]
                )
               # Check for tags in character's name
                if '🐰' in character['name']:
                    caption += "\n\n🐰 𝑩𝒖𝒏𝒏𝒚 🐰"
                elif '👩‍🏫' in character['name']:
                    caption += "\n\n👩‍🏫 𝑻𝒆𝒂𝒄𝒉𝒆𝒓 👩‍🏫"
                elif '🎒' in character['name']:
                    caption += "\n\n🎒 𝑺𝒄𝒉𝒐𝒐𝒍 🎒"
                elif '👘' in character['name']:
                    caption += "\n\n👘 𝑲𝒊𝒎𝒐𝒏𝒐 👘"
                elif '🏖' in character['name']:
                    caption += "\n\n🏖 𝑺𝒖𝒎𝒎𝒆𝒓 🏖"
                elif '🎄' in character['name']:
                    caption += "\n\n🎄 𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔 🎄"
                elif '🧹' in character['name']:
                    caption += "\n\n🧹 𝑴𝒂𝒊𝒅 🧹"
                elif '🥻' in character['name']:
                    caption += "\n\n🥻 𝑺𝒂𝒓𝒆𝒆 🥻"
                elif '🩺' in character['name']:
                    caption += "\n\n🩺 𝑵𝒖𝒓𝒔𝒆 🩺"
                elif '☃️' in character['name']:
                    caption += "\n\n☃️ 𝑾𝒊𝒏𝒕𝒆𝒓 ☃️"
        
            # Debugging print for character_id
           

            results.append(
                InlineQueryResultPhoto(
                    thumbnail_url=character['img_url'],
                    id=f"{character['id']}_{time.time()}",
                    photo_url=character['img_url'],
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=keyboard if not query.startswith('collection.') else None,
                    photo_width=300,  # Adjust the width as needed
                    photo_height=300  # Adjust the height as needed
                )
            )

        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Callback query handler for the "See Top Grabbers Of This Chat" button
async def show_top_grabbers(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        unique_id = query.data.split(":")[1]

        # Retrieve the character ID from the cache
        character_id = character_id_cache.get(unique_id)
        if not character_id:
            logging.error(f"Character ID not found in cache for unique_id: {unique_id}")
            await query.answer("Character ID not found.")
            return

        # Debugging print for character_id
        

        character = await collection.find_one({'id': character_id})

        if not character:
            await query.answer("Character not found.")
            return

        global_count = await user_collection.count_documents({'characters.id': character_id})

        # Find top 10 grabbers in the chat
        top_grabbers = await user_collection.aggregate([
            {'$match': {'characters.id': character_id}},
            {'$unwind': '$characters'},
            {'$match': {'characters.id': character_id}},
            {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]).to_list(length=None)

        grabbers_text = []
        for grabber in top_grabbers:
            user_data = await user_collection.find_one({'id': grabber['_id']})
            if user_data:
                full_name = user_data.get('first_name', '') + ' ' + user_data.get('last_name', '')
                # Construct HTML formatted name with blue link
                user_link = f"<a href='tg://user?id={grabber['_id']}'>{escape(full_name)}</a>"
                grabbers_text.append(f"➥ {user_link} x {grabber['count']}")

        grabbers_text = "\n".join(grabbers_text)

        rarity_formatted = get_rarity_formatted(character.get('rarity', ''))

        updated_caption = (
            f"<b> OwO! Check Out This Character!🏮!!</b>\n\n"
            f"🧩 ɴᴀᴍᴇ: <b>{character['name']}</b>\n"
            f"🏖️ ᴀɴɪᴍᴇ: <b>{character['anime']}</b>\n"
            f"{rarity_formatted}\n\n"
            f"🌏This Character Seized Globally: <b>{global_count} Times</b>\n\n"
            f"ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ: <b>{character['id']}</b>\n\n"
            f"<b>Top 10 Seizers Globally of This Character:</b>\n\n{grabbers_text}"
        )

        # Determine if the callback query is from an inline message or a chat message
        if query.message:
            # Chat message
            await query.message.edit_caption(updated_caption, parse_mode=ParseMode.HTML)
        else:
            # Inline message
            inline_message_id = query.inline_message_id
            await context.bot.edit_message_caption(
                inline_message_id=inline_message_id,
                caption=updated_caption,
                parse_mode=ParseMode.HTML
            )

        await query.answer()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        await query.answer("An error occurred while processing your request.")

# Handlers
inline_query_handler = InlineQueryHandler(inlinequery)
callback_query_handler = CallbackQueryHandler(show_top_grabbers, pattern=r'^top_grabbers:')

# Adding handlers to the dispatcher
application.add_handler(inline_query_handler)
application.add_handler(callback_query_handler)
