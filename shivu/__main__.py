import importlib
import time
import random
import re
import asyncio
import math
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, OWNER_ID, sudo_users, db, LOGGER
from shivu import set_on_data, set_off_data
from shivu.modules import ALL_MODULES

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
character_message_links = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

archived_characters = {}

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    # Lock setup for the chat
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        # Fetch or set default message frequency
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_frequency.get('message_frequency', 100) if chat_frequency else 100

        # Track the user's message count
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                # Warn user if within cooldown time
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    # Stylized warning message
                    warning_message = stylize_text(
                        f"🚫 Excessive Messages Detected!\n⛔️ {update.effective_user.first_name}, please take a break! You are being ignored for 10 minutes."
                    )
                    await update.message.reply_text(warning_message)
                    warned_users[user_id] = time.time()
                    return
        else:
            # Reset message count if the user has changed
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        # Increment message count for the chat
        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

        # Send an image at the specified frequency
        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0
    
rarity_active = {
    "⚪️ 𝘾𝙊𝙈𝙈𝙊𝙉": True,
    "🔵 𝙈𝙀𝘿𝙄𝙐𝙈": True,
    "👶 𝘾𝙃𝙄𝘽𝙄": True,
    "🟠 𝙍𝘼𝙍𝙀": True,
    "🟡 𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔": True,
    "💮 𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀": True,
    "🫧 𝙋𝙍𝙀𝙈𝙄𝙐𝙈": True,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉": True,
    "🌸 𝙀𝙓𝙊𝙏𝙄𝘾": True,
    "🎐 𝘼𝙎𝙏𝙍𝘼𝙇": True,
    "💞 𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀": True
}

# Map numbers to rarity strings
rarity_map = {
   1: "⚪️ 𝘾𝙊𝙈𝙈𝙊𝙉",
   2: "🔵 𝙈𝙀𝘿𝙄𝙐𝙈",
   3: "👶 𝘾𝙃𝙄𝘽𝙄",
   4: "🟠 𝙍𝘼𝙍𝙀",
   5: "🟡 𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔",
   6: "💮 𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀",
   7: "🫧 𝙋𝙍𝙀𝙈𝙄𝙐𝙈",
   8: "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉",
   9: "🌸 𝙀𝙓𝙊𝙏𝙄𝘾",
   10: "🎐 𝘼𝙎𝙏𝙍𝘼𝙇",
   11: "💞 𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀"
 }

RARITY_WEIGHTS = {
    "⚪️ 𝘾𝙊𝙈𝙈𝙊𝙉": 13,
    "🔵 𝙈𝙀𝘿𝙄𝙐𝙈": 10,
    "👶 𝘾𝙃𝙄𝘽𝙄": 7,
    "🟠 𝙍𝘼𝙍𝙀": 2.5,
    "🟡 𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔": 4,
    "💮 𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀": 0.5,
    "🫧 𝙋𝙍𝙀𝙈𝙄𝙐𝙈": 0.5,
    "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉": 0.1,
    "🌸 𝙀𝙓𝙊𝙏𝙄𝘾": 0.5,
    "🎐 𝘼𝙎𝙏𝙍𝘼𝙇": 0.1,
    "💞 𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀": 0.1,
}
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    all_characters = list(await collection.find({}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    if 'available_characters' not in context.user_data:
        context.user_data['available_characters'] = [
            c for c in all_characters 
            if 'id' in c 
            and c['id'] not in sent_characters.get(chat_id, [])
            and c.get('rarity') is not None 
            and c.get('rarity') != '💞 Valentine Special'
        ]

    available_characters = context.user_data['available_characters']

    cumulative_weights = []
    cumulative_weight = 0
    for character in available_characters:
        cumulative_weight += RARITY_WEIGHTS.get(character.get('rarity'), 1)
        cumulative_weights.append(cumulative_weight)

    rand = random.uniform(0, cumulative_weight)
    selected_character = None
    for i, character in enumerate(available_characters):
        if rand <= cumulative_weights[i]:
            selected_character = character
            break

    if not selected_character:
        # If no character is selected, choose randomly from all characters
        selected_character = random.choice(all_characters)

    sent_characters[chat_id].append(selected_character['id'])
    last_characters[chat_id] = selected_character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    rarity_to_emoji = {
        "⚪️ 𝘾𝙊𝙈𝙈𝙊𝙉": ("⚪️", "𝘾𝙊𝙈𝙈𝙊𝙉"),
        "🔵 𝙈𝙀𝘿𝙄𝙐𝙈": ("🔵", "𝙈𝙀𝘿𝙄𝙐𝙈"),
        "👶 𝘾𝙃𝙄𝘽𝙄": ("👶", "𝘾𝙃𝙄𝘽𝙄"),
        "🟠 𝙍𝘼𝙍𝙀": ("🟠", "𝙍𝘼𝙍𝙀"),
        "🟡 𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔": ("🟡", "𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔"),
        "💮 𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀": ("💮", "𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀"),
        "🫧 𝙋𝙍𝙀𝙈𝙄𝙐𝙈": ("🫧", "𝙋𝙍𝙀𝙈𝙄𝙐𝙈"),
        "🔮 𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉": ("🔮", "𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉"),
        "🌸 𝙀𝙓𝙊𝙏𝙄𝘾": ("🌸", "𝙀𝙓𝙊𝙏𝙄𝘾"),
        "🎐 𝘼𝙎𝙏𝙍𝘼𝙇": ("🎐", "𝘼𝙎𝙏𝙍𝘼𝙇"),
        "💞 𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀": ("💞", "𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀"),
    }

    rarity_emoji, rarity_name = rarity_to_emoji.get(selected_character.get('rarity'), ("❓", "Unknown"))
   
    message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=selected_character['img_url'],
        caption=f"""<b>{character['rarity'][0]} ᴋᴀᴡᴀɪ ❄️! ᴀ {character['rarity'][2:]} ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀs ᴀᴘᴘᴇᴀʀᴇᴅ!</b>\n<b>ᴀᴅᴅ ʜᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʙʏ sᴇɴᴅɪɴɢ</b>\n<b>/seize ɴᴀᴍᴇ</b>""",
        parse_mode='HTML')

    if update.effective_chat.type == "private":
        message_link = f"https://t.me/c/{chat_id}/{message.message_id}"
    else:
        message_link = f"https://t.me/{update.effective_chat.username}/{message.message_id}"

    character_message_links[chat_id] = message_link
    
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in last_characters:
        return

    # Check if someone has already guessed correctly
    if chat_id in first_correct_guesses:
        correct_guess_user = first_correct_guesses[chat_id]  
        user_link = f'<a href="tg://user?id={correct_guess_user.id}">{correct_guess_user.first_name}</a>'  
        await update.message.reply_text(
            f'🌟 ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀs ʙᴇᴇɴ sᴇɪᴢᴇᴅ ʙʏ {user_link}!\n'
            f'🍵 ᴡᴀɪᴛ ғᴏʀ ᴛʜᴇ ɴᴇxᴛ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ sᴘᴀᴡɴ... 🌌', 
            parse_mode='HTML'
        )
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text(
            "🔒 𝖲𝗈𝗋𝗋𝗒, 𝗯𝗲𝗻𝖺𝖺! 𝖡𝗎𝗍 𝗽𝗹𝗲𝗮𝖼𝗲 𝗮𝖽𝖽 𝗮 𝗻𝖺𝗆𝖾 𝗐𝗂𝗍𝗁𝗈𝗎𝗍 '&' 𝖳𝗈 𝖼𝗈𝗅𝗅𝖾𝖼𝗍...🍂", 
            parse_mode='Markdown'
        )
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    # Check if the guess is correct
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):

        first_correct_guesses[chat_id] = update.effective_user
        
        # Update user information in the database
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })
            
        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })
            
        keyboard = [[InlineKeyboardButton(f"🏮 ʜᴀʀᴇᴍ 🏮", switch_inline_query_current_chat=f"collection.{user_id}")]]
        
        await update.message.reply_text(
            f'💥 𝙲ᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs, <b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b>! 🎊\n'
            f'❄️ ʏᴏᴜ ʜᴀᴠᴇ ᴀᴅᴅᴇᴅ ᴀ ɴᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ! \n\n'
            f'⚜️ Character: <b>{last_characters[chat_id]["name"]}</b>\n'
            f'⛩️ Anime: <b>{last_characters[chat_id]["anime"]}</b>\n'
            f'🏖️ Rarity: <b>{last_characters[chat_id]["rarity"]}</b>\n\n'
            f'🫧 ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʙʏ /harem', 
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        message_link = character_message_links.get(chat_id, "#")
        keyboard = [[InlineKeyboardButton("★ sᴇᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ★", url=message_link)]]
        await update.message.reply_text(
            '❌ ᴄʜᴀʀᴀᴄᴛᴇʀ ɴᴀᴍᴇ ɪs ɴᴏᴛ ᴄᴏʀʀᴇᴄᴛ. 🔍 ᴘʟᴇᴀsᴇ ᴛʏ ᴀɢᴀɪɴ!',
            reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Command to turn a rarity on
async def set_on(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != 6402009857:
        await update.message.reply_text("only `my sensei @The_clan_killer_12` can use this command.")
        return
    try:
        rarity_number = int(context.args[0])
        rarity = rarity_map.get(rarity_number)
        if rarity and rarity in rarity_active:
            if not rarity_active[rarity]:
                rarity_active[rarity] = True
                await update.message.reply_text(f'Rarity {rarity} is now ON and will spawn from now on.')
            else:
                await update.message.reply_text(f'Rarity {rarity} is already ON.')
        else:
            await update.message.reply_text('Invalid rarity number.')
    except (IndexError, ValueError):
        await update.message.reply_text('Please provide a valid rarity number.')
# Command to turn a rarity off
async def set_off(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != 6402009857:
        await update.message.reply_text("Only `my Sensei @The_clan_killer_12` Can use this command.")
        return
    try:
        rarity_number = int(context.args[0])
        rarity = rarity_map.get(rarity_number)
        if rarity and rarity in rarity_active:
            if rarity_active[rarity]:
                rarity_active[rarity] = False
                await update.message.reply_text(f'Rarity {rarity} is now OFF and will not spawn from now on.')
            else:
                await update.message.reply_text(f'Rarity {rarity} is already OFF.')
        else:
            await update.message.reply_text('Invalid rarity number.')
    except (IndexError, ValueError):
        await update.message.reply_text('Please provide a valid rarity number.')
        
application.add_handler(CommandHandler('set_on', set_on, block=False))
application.add_handler(CommandHandler('set_off', set_off, block=False))

def main() -> None:
    """Run bot."""
    
    application.add_handler(CommandHandler(["seize"], guess, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
