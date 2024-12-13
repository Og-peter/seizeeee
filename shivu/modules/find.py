import re
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import user_collection, collection, event_collection, application, db
from shivu import shivuu as bot
from cachetools import TTLCache

# TTL cache with a time-to-live of 10 minutes and a maximum size of 100
cache = TTLCache(maxsize=100, ttl=600)

current_page = 0
users_with_character = []
processing_message = None
character_id = None

# bongo dindex
user_collection.create_index('characters.id')

async def find_users_with_character(character_name):
    if character_name in cache:
        return cache[character_name]
    
    query = {'characters.id': character_name}
    projection = {'id': 1, 'first_name': 1, 'username': 1, 'characters': 1}
    users_with_character = []

    async for user in user_collection.find(query, projection):
        users_with_character.append({'id': user['id'], 'first_name': user['first_name'], 'username': user.get('username')})
    
    cache[character_name] = users_with_character
    return users_with_character


async def find_trade(update: Update, context: CallbackContext) -> None:
    global current_page, users_with_character, processing_message, character_id
    try:
        user_id = update.effective_user.id 
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /find <id>')
            return

        character_id = args[0]
        users_with_character = await find_users_with_character(character_id)
        
        if not users_with_character:
            await update.message.reply_text('No users found with that character in this chat.')
            return
        
        current_page = 0
        processing_message = await update.message.reply_text("Processing...")
        
        await send_pagination(update, user_id)

    except Exception as e:
        print(e)
        await update.message.reply_text('An error occurred while processing your request.')

async def send_pagination(update, user_id):
    global current_page, processing_message, users_with_character, character_id
    items_per_page = 10
    total_pages = (len(users_with_character) + items_per_page - 1) // items_per_page

    current_users = users_with_character[current_page * items_per_page: (current_page + 1) * items_per_page]
    message = f"Tʜɪs Is Lɪsᴛ Wʜᴏ Oᴡɴ Tʜɪs Cʜᴀʀᴀᴄᴛᴇʀ Iɴ Eɴᴛɪʀᴇ Bᴏᴛ Cᴏʟʟᴇᴄᴛɪᴏɴ:- {character_id}\n\n"
    
    for i, user in enumerate(current_users, start=current_page * items_per_page + 1):
        mention = f'<a href="https://t.me/{user["username"]}">{user["first_name"][:15]}</a>' if user.get('username') else user["first_name"]
        message += f"{i}. {mention}\n"
    
    message += f"\nPage {current_page + 1}/{total_pages}"

    reply_markup = None
    if total_pages > 1:
        buttons = []
        if current_page > 0:
            buttons.append(InlineKeyboardButton("《 ᴘʀᴇᴠɪᴏᴜꜱ", callback_data=f"findTprevv_{user_id}"))
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton("ɴᴇxᴛ 》", callback_data=f"findTnextt_{user_id}"))
        reply_markup = InlineKeyboardMarkup([buttons])

    await processing_message.edit_text(message, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)

async def character_callback(update: Update, context: CallbackContext) -> None:
    global current_page
    query = update.callback_query
    data = query.data
    user_id = int(data.split("_")[1])
    
    if "findTprevv_" in data and current_page > 0:
        if query.from_user.id != user_id:
            await query.answer("Please Don't Stalk", show_alert=True)
            return    
        current_page -= 1
        await send_pagination(query, user_id)
    elif "findTnextt_" in data and (current_page + 1) * 10 < len(users_with_character):
        if query.from_user.id != user_id:
            await query.answer("Please Don't Stalk", show_alert=True)
            return    
        current_page += 1
        await send_pagination(query, user_id)

add_rarity_handler = CallbackQueryHandler(character_callback, pattern=r'^findTprevv_\d+$|^findTnextt_\d+$', block=False)
application.add_handler(add_rarity_handler)
start_handler = CommandHandler('find', find_trade, block=False)
application.add_handler(start_handler)
