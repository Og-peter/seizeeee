from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application
import math
from html import escape
import random
from itertools import groupby

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You have not looted any characters yet..')
        else:
            await update.callback_query.edit_message_text('You have not looted any characters yet..')
        return

    characters = sorted(user['characters'], key=lambda x: (x.get('anime', ''), x.get('id', '')))

    # Check if the user has chosen a rarity preference
    if 'rarity_preference' in user:
        rarity = user['rarity_preference']
        characters = [char for char in characters if char.get('rarity') == rarity]

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x.get('id'))}

    unique_characters = list({character.get('id'): character for character in characters}.values())

    total_pages = math.ceil(len(unique_characters) / 15)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    current_characters = unique_characters[page*15:(page+1)*15]

    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x.get('anime', ''))}

    rarity_emojis = {
        '⚪️ Common': '⚪️',
        '🔮 Limited Edition': '🔮',
        '🫧 Premium': '🫧',
        '🌸 Exotic': '🌸',
        '💮 Exclusive': '💮',
        '👶 Chibi': '👶',
        '🟡 Legendary': '🟡',
        '🟠 Rare': '🟠',
        '🔵 Medium': '🔵',
        '🎐 Astral': '🎐',
        '💞 Valentine': '💞'
    }

    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n<b>❖ {anime} ﹝{len(characters)}/{await collection.count_documents({"anime": anime})}〕</b>\n'
        
        for character in characters:
            count = character_counts.get(character.get('id'), 0)
            rarity = character.get('rarity', 'Unknown')
            rarity_emoji = rarity_emojis.get(rarity, rarity)
            character_id = character.get("id", "Unknown")
            harem_message += f'⌬  ⌠ {rarity_emoji} ⌡  𝐈𝐃 : {character_id}  {character.get("name", "Unknown")} ×{count}\n'
            
    total_count = len(user['characters'])

    keyboard = [[InlineKeyboardButton(f"sᴇᴇ ᴄʜᴀʀᴀᴄᴛᴇʀs 🪭 ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀ previous", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ▶", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c.get('id') == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.callback_query.message.photo:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])
            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    if update.callback_query.message.photo:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.message:
                    await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("⬤ ʏᴏᴜʀ ʟɪsᴛ ɪs sᴏ ᴇᴍᴘᴛʏ :)")
            else:
                await update.callback_query.edit_message_text("⬤ ʏᴏᴜʀ ʟɪsᴛ ɪs sᴏ ᴇᴍᴘᴛʏ :)")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    _, page_str, user_id = data.split(':')

    current_page = int(page_str)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("⬤ ᴅᴏɴ'ᴛ sᴛᴀʟᴋ ᴏᴛʜᴇʀ ᴜsᴇʀ's ʜᴀʀᴇᴍ", show_alert=True)
        return

    if "next" in data:
        page = current_page + 1
    elif "prev" in data:
        page = current_page - 1
    else:
        page = current_page

    await harem(update, context, page)

application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
        
