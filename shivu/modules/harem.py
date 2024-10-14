from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application
import math
from html import escape
import random
from itertools import groupby

# Enhanced Harem function
async def harem(update: Update, context: CallbackContext, page=0, filter_anime=None, filter_rarity=None) -> None:
    user_id = update.effective_user.id

    # Fetch user data
    user = await user_collection.find_one({'id': user_id})

    if not user:
        message = 'You have not seized any characters yet..'
        await update.message.reply_text(message) if update.message else await update.callback_query.edit_message_text(message)
        return

    characters = user['characters']

    # Apply filters if provided
    if filter_anime:
        characters = [char for char in characters if char.get('anime') == filter_anime]
    if filter_rarity:
        characters = [char for char in characters if char.get('rarity') == filter_rarity]

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
    
    # Adding filter options
    filter_buttons = [
        [InlineKeyboardButton("Filter by Rarity", callback_data=f"filter_rarity:{user_id}")],
        [InlineKeyboardButton("Filter by Anime", callback_data=f"filter_anime:{user_id}")]
    ]
    
    keyboard = filter_buttons + [[InlineKeyboardButton(f"See Characters 🏮 ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀ Previous", callback_data=f"harem:{page-1}:{user_id}"))
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

# Register filter callback
async def filter_harem(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    user_id = query.from_user.id

    if data.startswith("filter_rarity"):
        # Present options for filtering by rarity (show inline buttons)
        pass  # Add logic to filter by rarity
    elif data.startswith("filter_anime"):
        # Present options for filtering by anime
        pass  # Add logic to filter by anime

application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(filter_harem, pattern='^filter_', block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
