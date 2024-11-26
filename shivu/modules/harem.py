from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from html import escape 
import random
import math
from itertools import groupby
from shivu import collection, user_collection, application
async def harem(update: Update, context: CallbackContext, page=0, edit=False) -> None:
    user_id = update.effective_user.id
    
    # Mapping harem mode to rarity values
    harem_mode_mapping = {
        "common": "⚪️ Common",
        "limited_edition": "🔮 Limited Edition",
        "premium": "🫧 Premium",
        "exotic": "🌸 Exotic",
        "exclusive": "💮 Exclusive",
        "chibi": "👶 Chibi",
        "legendary": "🟡 Legendary",
        "rare": "🟠 Rare",
        "medium": "🔵 Medium",
        "astral": "🎐 Astral",
        "valentine": "💞 Valentine",
        "default": None
    }
    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text("🚨 ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʀᴇɢɪsᴛᴇʀ ғɪʀsᴛ! sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ɪɴ ᴅᴍ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.")
        return
    
    characters = user.get('characters', [])
    fav_character_id = user.get('favorites', [])[0] if 'favorites' in user else None
    fav_character = None
    if fav_character_id:
        for c in characters:
            if isinstance(c, dict) and c.get('id') == fav_character_id:
                fav_character = c
                break
    
    hmode = user.get('smode')
    if hmode == "default" or hmode is None:
        characters = [char for char in characters if isinstance(char, dict)]
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))
        rarity_value = "all"
    else:
        rarity_value = harem_mode_mapping.get(hmode, "Unknown Rarity")
        characters = [char for char in characters if isinstance(char, dict) and char.get('rarity') == rarity_value]
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))
    
    if not characters:
        await update.message.reply_text(f"❌ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ({rarity_value}) ʜᴀʀᴇᴍ. ᴄʜᴀɴɢᴇ ɪᴛ ᴜsɪɴɢ /hmode.")
        return
    
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    total_pages = math.ceil(len(characters) / 10)
    if page < 0 or page >= total_pages:
        page = 0
    
    harem_message = (
        f"<b>💌 {escape(update.effective_user.first_name)}'s sᴀɴ ʜᴀʀᴇᴍ - Page {page + 1}/{total_pages}</b>\n\n"
        f"✨ ᴅɪsᴘʟᴀʏɪɴɢ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ. ғɪʟᴛᴇʀᴇᴅ ʙʏ ʀᴀʀɪᴛʏ: <b>{rarity_value.capitalize()}</b>."
    )
    
    current_characters = characters[page * 10:(page + 1) * 10]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    included_characters = set()
    
    for anime, characters in current_grouped_characters.items():
        user_anime_count = len([char for char in user['characters'] if isinstance(char, dict) and char.get('anime') == anime])
        total_anime_count = await collection.count_documents({"anime": anime})
        
        harem_message += f'\n⌬ <b>{anime} 〔{user_anime_count}/{total_anime_count}〕</b>\n'
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'
        
        for character in characters:
            if character['id'] not in included_characters:
                count = character_counts[character['id']]
                formatted_id = f"{int(character['id']):04d}"
                harem_message += f'➥ {formatted_id} | {character["rarity"][0]} | {character["name"]} ×{count}\n'
                included_characters.add(character['id'])
        harem_message += f'⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'
    
    keyboard = [
        [InlineKeyboardButton(f"🥂 sᴇᴇ ғᴜʟʟ ʜᴀʀᴇᴍ", switch_inline_query_current_chat=f"collection.{user_id}")],
        [InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore")]
    ]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ ᴘʀᴇᴠ", callback_data=f"harem:{page - 1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ ɴᴇxᴛ", callback_data=f"harem:{page + 1}:{user_id}"))
        keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = update.message or update.callback_query.message

    if fav_character and 'img_url' in fav_character:
        if fav_character['img_url'].endswith(('.mp4', '.gif')):
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_video(video=fav_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_photo(photo=fav_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])
            if 'img_url' in random_character:
                if random_character['img_url'].endswith(('.mp4', '.gif')):
                    if edit:
                        await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await message.reply_video(video=random_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if edit:
                        await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await message.reply_photo(photo=random_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if edit:
                    await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if edit:
                await message.edit_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)
    if query.from_user.id != user_id:
        await query.answer("⛔ This isn't your harem!", show_alert=True)
        return
    await query.answer()
    await harem(update, context, page, edit=True)


async def set_hmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("💠 Default", callback_data="default"),
            InlineKeyboardButton("✨ Rarity", callback_data="rarity"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo="https://files.catbox.moe/imfe7m.jpg",
        caption="🌟 **Select your preferred Harem Mode** 🌟\n\n"
                "Please choose from the options below to set your desired Harem Mode:",
        reply_markup=reply_markup,
    )


async def hmode_rarity(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("⚪ Common", callback_data="common"),
            InlineKeyboardButton("🔮 Limited Edition", callback_data="limited_edition"),
            InlineKeyboardButton("🫧 Premium", callback_data="premium"),
        ],
        [
            InlineKeyboardButton("🌸 Exotic", callback_data="exotic"),
            InlineKeyboardButton("💮 Exclusive", callback_data="exclusive"),
            InlineKeyboardButton("👶 Chibi", callback_data="chibi"),
        ],
        [
            InlineKeyboardButton("🟡 Legendary", callback_data="legendary"),
            InlineKeyboardButton("🟠 Rare", callback_data="rare"),
            InlineKeyboardButton("🔵 Medium", callback_data="medium"),
        ],
        [
            InlineKeyboardButton("🎐 Astral", callback_data="astral"),
            InlineKeyboardButton("💞 Valentine", callback_data="valentine"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.edit_message_caption(
        caption="✨ **Choose a Rarity** ✨\n\n"
                "Select the rarity you want to set as your Harem Mode:",
        reply_markup=reply_markup,
    )
    await query.answer()


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if data == "default":
        await user_collection.update_one({'id': user_id}, {'$set': {'smode': data}})
        await query.answer()
        await query.edit_message_caption(
            caption="✅ **Harem Mode Updated!**\n\n"
                    "Your harem mode has been successfully set to **Default**."
        )
    elif data == "rarity":
        await hmode_rarity(update, context)
    else:
        await user_collection.update_one({'id': user_id}, {'$set': {'smode': data}})
        await query.answer()
        await query.edit_message_caption(
            caption=f"✅ **Rarity Set Successfully!**\n\n"
                    f"You have set your Harem Mode to: **{data.capitalize()}**."
        )


# New Feature: Harem Stats
async def harem_stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        caption = "❌ **No Harem Data Found!**\n\n" \
                  "It seems like you haven't configured your Harem Mode yet. Use `/hmode` to get started!"
    else:
        mode = user_data.get('smode', 'Default').capitalize()
        rarity_count = user_data.get('rarities', {})  # Example data structure for rarity
        total_waifus = sum(rarity_count.values())
        caption = f"🎉 **Your Harem Stats** 🎉\n\n" \
                  f"🔹 **Current Mode:** {mode}\n" \
                  f"💠 **Total Waifus:** {total_waifus}\n\n" \
                  "🌟 **Rarity Breakdown:**\n" \
                  + "\n".join([f" - {key.capitalize()}: {value}" for key, value in rarity_count.items()]) \
                  + "\n\nUse `/hmode` to modify your preferences!"

    await update.message.reply_photo(
        photo="https://files.catbox.moe/imfe7m.jpg",
        caption=caption,
    )


# Handlers
application.add_handler(CommandHandler(["harem"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
application.add_handler(CommandHandler("hmode", set_hmode))
application.add_handler(
    CallbackQueryHandler(
        button,
        pattern='^default$|^common$|^limited_edition$|^premium$|^exotic$|^exclusive$|^chibi$|^legendary$|^rare$|^medium$|^astral$|^valentine$',
        block=False,
    )
)
application.add_handler(CommandHandler("haremstats", harem_stats))
