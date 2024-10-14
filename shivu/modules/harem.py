from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application
import math
from html import escape
import random
from itertools import groupby

# Enhanced Harem function without filters
async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    # Fetch user data
    user = await user_collection.find_one({'id': user_id})

    if not user:
        message = 'You have not seized any characters yet..'
        await update.message.reply_text(message) if update.message else await update.callback_query.edit_message_text(message)
        return

    characters = user['characters']

    characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))

    # Group characters by ID for counting
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x.get('id'))}

    # Unique characters
    unique_characters = list({char['id']: char for char in characters}.values())

    total_pages = math.ceil(len(unique_characters) / 15)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page [{page+1}/{total_pages}]</b>\n"

    # Paginate and group by anime
    current_characters = unique_characters[page*15:(page+1)*15]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x.get('anime', ''))}

    rarity_emojis = {
        '⚪️ Common': '⚪️',
        '🔮 Limited Edition': '🔮',
        '🫧 Premium': '🫧',
        '🌸 Exotic': '🌸',
        '💮 Exclusive': '💮',
        '🟡 Legendary': '🟡',
        '🟠 Rare': '🟠',
        '🔵 Medium': '🔵',
        '🎐 Astral': '🎐',
        '💞 Valentine': '💞'
    }

    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n<b> ᯽{anime} ﹝{len(characters)}/{await collection.count_documents({"anime": anime})}〕</b>\n'
        harem_message += '╭── ⋅ ⋅ ──── ✩ ──── ⋅ ⋅ ──╮\n'
        for character in characters:
            count = character_counts.get(character.get('id'), 0)
            rarity = character.get('rarity', 'Unknown')
            rarity_emoji = rarity_emojis.get(rarity, rarity)
            character_id = character.get("id", "Unknown")
            harem_message += f'❖  ⌠ {rarity_emoji} ⌡ : {character_id}  {character.get("name", "Unknown")} ×{count}\n'
            harem_message += f'╰── ⋅ ⋅ ──── ✩ ──── ⋅ ⋅ ──╯\n'

    total_count = len(user['characters'])

    # Button logic (pagination, fast forward, etc.)
    keyboard = []

    # Pagination Buttons
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("1x ⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("1x ➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)
    
    # Current Page Indicator
    keyboard.append([InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop")])

    # Fast Forward Button
    if page < total_pages - 2:
        keyboard.append([InlineKeyboardButton("FAST ⏩", callback_data=f"harem:{page+2}:{user_id}")])

    # Globe Button (Placeholder: Modify this as per your need)
    keyboard.append([InlineKeyboardButton("🌐", callback_data="global_view")])

    # Trash/Delete Button (Placeholder: Implement your own logic for deleting)
    keyboard.append([InlineKeyboardButton("🗑️", callback_data=f"delete_harem:{user_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handling favorite character image display
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
        random_character = random.choice(user['characters']) if user['characters'] else None
        if random_character and 'img_url' in random_character:
            if update.message:
                await update.message.reply_photo(photo=random_character['img_url'], caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.callback_query.message.photo:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text("⬤ Your list is so empty :)") if update.message else await update.callback_query.edit_message_text("⬤ Your list is so empty :)")

# Callback function for handling harem pagination
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    # Extract page and user ID from the callback data
    _, page_str, user_id = data.split(':')

    current_page = int(page_str)
    user_id = int(user_id)

    # Ensure users cannot interact with other users' harems
    if query.from_user.id != user_id:
        await query.answer("⬤ Don't stalk other user's harem", show_alert=True)
        return

    # Display the harem with the selected page
    await harem(update, context, current_page)

# Register handlers after defining all functions
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
