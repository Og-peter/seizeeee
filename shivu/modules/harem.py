from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application
import math
from html import escape
import random
from itertools import groupby
from telegram.error import BadRequest

SUPPORT_CHANNEL = "@Seizer_updates"

async def is_user_in_channel(user_id: int) -> bool:
    try:
        member = await application.bot.get_chat_member(chat_id=SUPPORT_CHANNEL, user_id=user_id)
        return member.status not in ['left', 'kicked']
    except BadRequest:
        return False
        
async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    # Check if user is in the support channel
    if not await is_user_in_channel(user_id):
        join_message = f"⬤ ᴊᴏɪɴ [ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ]({SUPPORT_CHANNEL}) ᴛᴏ ᴀᴄᴄᴇss ᴛʜɪs ғᴇᴀᴛᴜʀᴇ."
        if update.message:
            await update.message.reply_text(join_message, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await update.callback_query.edit_message_text(join_message, parse_mode='Markdown', disable_web_page_preview=True)
        return

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

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem</b>\n\n"

    current_characters = unique_characters[page*15:(page+1)*15]

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

    # Group by anime and display characters under each anime
    anime_groups = groupby(current_characters, key=lambda x: x.get('anime', 'Unknown'))

    for anime, characters_in_anime in anime_groups:
        characters_in_anime = list(characters_in_anime)
        harem_message += f"❖ <b>{anime}</b> ⌠{len(characters_in_anime)}/{len([c for c in characters if c.get('anime', '') == anime])}⌡\n"
        harem_message += "── ⋅ ⋅ ⋅ ⋅ ─── ⋅  ⋅ ─── ⋅ ⋅ ⋅ ⋅ ──\n"
        
        for character in characters_in_anime:
            count = character_counts.get(character.get('id'), 0)
            rarity = character.get('rarity', 'Unknown')
            rarity_emoji = rarity_emojis.get(rarity, rarity)
            character_id = character.get("id", "Unknown")
            harem_message += f"➸ {character_id} 〔 {rarity_emoji} 〕 {character.get('name', 'Unknown')} x{count}\n"

        harem_message += "── ⋅ ⋅ ⋅ ⋅ ─── ⋅  ⋅ ─── ⋅ ⋅ ⋅ ⋅ ──\n\n"

    total_count = len(user['characters'])

    # New keyboard
    keyboard = [
        [
            InlineKeyboardButton("◀", callback_data=f"harem:{page-1}:{user_id}"),
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"),
            InlineKeyboardButton("▶", callback_data=f"harem:{page+1}:{user_id}"),
        ],
        [
            InlineKeyboardButton("🌐", switch_inline_query_current_chat=f"collection.{user_id}"),
            InlineKeyboardButton("FAST ▶", callback_data=f"harem:{total_pages-1}:{user_id}"),
            InlineKeyboardButton("🗑", callback_data="delete"),
        ],
        ]
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

    if page < 0 or page >= total_pages:
        await query.answer("⬤ ɪɴᴠᴀʟɪᴅ ᴘᴀɢᴇ!", show_alert=True)
        return
    if "next" in data:
        page = current_page + 1
    elif "prev" in data:
        page = current_page - 1
    else:
        page = current_page

    await harem(update, context, page)

harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem:', block=False)
application.add_handler(harem_handler)
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
