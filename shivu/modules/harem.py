from telegram import Update
from itertools import groupby
import urllib.request
import re
import math
import html
import random
from collections import Counter
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters
from shivu import collection, user_collection, application
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InputTextMessageContent, InputMediaPhoto
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters
from telegram.ext import InlineQueryHandler, CallbackQueryHandler, ChosenInlineResultHandler

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id  
    user = await user_collection.find_one({'id': user_id})
    if not user:
        print(user)
        if update.message:
            await update.message.reply_text('ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ɢᴜᴇssᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀs ʏᴇᴛ.')
        else:
            await update.callback_query.edit_message_text('ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ɢᴜᴇssᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀs ʏᴇᴛ.')
        return
    # Retrieve selected rarity from the user's document
    selected_rarity = user.get('selected_rarity')

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
    
    # Filter characters based on the selected rarity
    if selected_rarity:
        characters = [character for character in characters if character['rarity'][0] == selected_rarity[0]]

    if selected_rarity == 'Default':
        characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
        

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    unique_characters = list({character['id']: character for character in characters}.values())
    total_pages = math.ceil(len(unique_characters) / 15)

    if page < 0 or page >= total_pages:
        page = 0
    harem_message = f"{update.effective_user.first_name}'s ʜᴀʀᴇᴍ - ᴘᴀɢᴇ {page+1}/{total_pages}\n"   
    current_characters = unique_characters[page*15:(page+1)*15]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n⌬ {anime} 〔{len(characters)}/{await collection.count_documents({"anime": anime})}〕\n'
        for character in characters:
            count = character_counts[character['id']]  
            if character["rarity"] == "🎐 Celestial":
                rarity_symbol = "🎐"
            else:
                rarity_symbol = character["rarity"][0]  
            
            harem_message += f'◈⌠{rarity_symbol}⌡ {character["id"]} {character["name"]} ×{count}\n'

    total_count = len(user['characters'])
    keyboard = [
        [InlineKeyboardButton(f"sᴇᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")],
        [InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore")]
    ]
    if total_pages > 1:
        nav_buttons = [
            InlineKeyboardButton("⬅️1x", callback_data=f"harem:{page-1}:{user_id}") if page > 0 else None,
            InlineKeyboardButton("1x➡️", callback_data=f"harem:{page+1}:{user_id}") if page < total_pages - 1 else None
        ]
        # Add buttons for page-6 and page+6
        if page >= 6:
            nav_buttons.insert(0, InlineKeyboardButton("⏪x6", callback_data=f"harem:{page-6}:{user_id}"))
        if page + 6 < total_pages:
            nav_buttons.append(InlineKeyboardButton("6x⏩", callback_data=f"harem:{page+6}:{user_id}"))
        keyboard.append(list(filter(None, nav_buttons)))
    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)
        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], caption=harem_message, reply_markup=reply_markup)
            else:
                if update.callback_query.message.caption != harem_message:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, reply_markup=reply_markup)
            else:
                if update.callback_query.message.text != harem_message:
                    await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])
            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], caption=harem_message, reply_markup=reply_markup)
                else:
                    if update.callback_query.message.caption != harem_message:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
            else:
                if update.message:
                    await update.message.reply_text(harem_message, reply_markup=reply_markup)
                else:
                    if update.callback_query.message.text != harem_message:
                        await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("ʏᴏᴜʀ ʟɪsᴛ ɪs ᴇᴍᴘᴛʏ :)")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("ᴅᴏɴ'ᴛ sᴛᴀʟᴋ ᴏᴛʜᴇʀ ᴜsᴇʀ's ʜᴀʀᴇᴍ..  OK", show_alert=True)
        return

    await harem(update, context, page)

async def add_rarity(update: Update, context: CallbackContext) -> None:
    global user_idh
    user_idh = update.effective_user.id
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    user_name = update.effective_user.first_name
    
    
    if not user:
        await update.message.reply_text("You haven't caught any characters yet.")
        return
    
    rarities = ["⚪️ Common", "🟣 Rare" , "🟡 Legendary", "🟢 Medium", "💮 Exclusive", "🔮 Mythical" , "🫧 Special", "🌤 Summer", "🎐 Celestial", "⚡ Galactic"]
    
    # Get the user's current rarity, if available
    current_rarity = user.get('selected_rarity')
    
    # Arrange rarities in rows of two
    keyboard = []
    for i in range(0, len(rarities), 2):
        row = [InlineKeyboardButton(f"{rarities[i].title()} {'✅️' if rarities[i] == current_rarity else ''}", 
                                     callback_data=f"add_rarity:{rarities[i]}")]
        if i + 1 < len(rarities):
            row.append(InlineKeyboardButton(f"{rarities[i + 1].title()} {'✅️' if rarities[i + 1] == current_rarity else ''}", 
                                             callback_data=f"add_rarity:{rarities[i + 1]}"))
        keyboard.append(row)
    
    # Add Default button with ✅️ if current_rarity is "Default"
    keyboard.append([InlineKeyboardButton(f"ᴅᴇꜰᴀᴜʟᴛ {'✅️' if current_rarity == 'Default' else ''}", callback_data="add_rarity:Default")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    image_url = "https://telegra.ph/file/202774af0d3e0544029ba.png"
    caption = f"{user_name} ᴘʟᴇᴀꜱᴇ ᴄʜᴏᴏꜱᴇ ʀᴀʀɪᴛʏ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇᴛ ᴀꜱ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ"
    
    # Send image with caption and markup keyboard
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=caption, reply_markup=reply_markup)



async def add_rarity_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if query.from_user.id != user_idh:
        await query.answer("its Not Your Harem", show_alert=True)
        return
        
    if data == "add_rarity:Default":
        # Set default rarity in the user's collection
        await user_collection.update_one({'id': user_id}, {'$set': {'selected_rarity': 'Default'}})
        
        # Edit caption to show selected rarity
        await query.message.edit_caption(caption="ʏᴏᴜ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ ᴀꜱ ᴅᴇꜰᴀᴜʟᴛ")
        
        rarities = ["1⚪️ Common", "🟣 Rare" , " 🟡 Legendary", "🟢 Medium", "💮 Exclusive", "🔮 Mythical" , "🫧 Special", "🌤 Summer", "🎐 Celestial", "⚡ Galactic"]
        # Arrange rarities in rows of two
        keyboard = []
        for i in range(0, len(rarities), 2):
            row = [InlineKeyboardButton(f"{rarities[i].title()} {'✅️' if rarities[i] == 'Default' else ''}", 
                                         callback_data=f"add_rarity:{rarities[i]}")]
            if i + 1 < len(rarities):
                row.append(InlineKeyboardButton(f"{rarities[i + 1].title()} {'✅️' if rarities[i + 1] == 'Default' else ''}", 
                                                 callback_data=f"add_rarity:{rarities[i + 1]}"))
            keyboard.append(row)
        
        # Add Default button with ✅️
        keyboard.append([InlineKeyboardButton("ᴅᴇꜰᴀᴜʟᴛ ✅️", callback_data="add_rarity:Default")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit message reply markup
        await query.message.edit_reply_markup(reply_markup=reply_markup)
    else:
        # If a rarity button other than Default is clicked
        rarity = data.split(":")[1]
        
        # Update the user's collection with the selected rarity
        await user_collection.update_one({'id': user_id}, {'$set': {'selected_rarity': rarity}})
    
        # Edit caption to show selected rarity
        await query.message.edit_caption(caption=f"ʏᴏᴜ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ ʀᴀʀɪᴛʏ ᴀꜱ {rarity}")

application.add_handler(CommandHandler("whmode", add_rarity, block=False))
add_rarity_handler = CallbackQueryHandler(add_rarity_callback, pattern='^add_rarity', block=False)
application.add_handler(add_rarity_handler)

application.add_handler(CommandHandler("harem", harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
