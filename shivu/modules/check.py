import urllib.request
import os
from pymongo import ReturnDocument
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, collection, db, user_collection
from html import escape

async def check_character(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) < 1 or not args[0].isdigit():
            await update.message.reply_text('Incorrect format. Please use: /check character_id [page_number]')
            return

        character_id = args[0]
        page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

        # Fetch character details
        character = await collection.find_one({'id': character_id})
        if not character:
            await update.message.reply_text('Wrong id.')
            return
        
        # Count globally seized times for the character
        global_count = await user_collection.count_documents({'characters.id': character['id']})

        # Original response message retained
        response_message = (
            f"<b>🧋 ᴏᴡᴏ! ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ !!</b>\n\n"
            f"{character['id']}: <b>{character['name']}</b>\n"
            f"<b>{character['anime']}</b>\n"
            f"(𝙍𝘼𝙍𝙄𝙏𝙔: {character['rarity']})\n\n"
            f"🌐 <b>Globally Seized:</b> {global_count}x"
        )

        # Fetch top 20 users with this character
        cursor = user_collection.find(
            {'characters.id': character_id},
            {'_id': 1, 'id': 1, 'first_name': 1, 'last_name': 1, 'username': 1, 'profile_name': 1, 'characters.$': 1}
        ).sort([('characters.count', -1)]).limit(20)

        users = await cursor.to_list(length=20)

        # Prepare page content (10 users per page)
        per_page = 10
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        users_page = users[start_index:end_index]

        if users_page:
            response_message += f"\n\n🌐 <b>Top Grabbers (Page {page}):</b>\n\n"
            for i, user in enumerate(users_page, start=start_index + 1):
                full_name = user.get('profile_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown User')
                seized_count = user['characters'][0].get('count', 1)

                # Create mention link for the user
                mention = f"<a href='tg://user?id={user['id']}'>{escape(full_name)}</a>"
                response_message += f"├ {i:02d}. ➔ {mention} ✨ ➔ {seized_count}x\n"
        else:
            response_message += "\n\nNo users found with this character."
        
        # Create pagination buttons
        keyboard_buttons = []
        if start_index > 0:
            keyboard_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{character_id}_{page - 1}"))
        if end_index < len(users):
            keyboard_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"page_{character_id}_{page + 1}"))

        keyboard = InlineKeyboardMarkup([keyboard_buttons] if keyboard_buttons else [])

        # Send the message with the image and buttons
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=character['img_url'],
            caption=response_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    except Exception as e:
        # Log error for debugging
        print(f"Error in check_character: {e}")
        await update.message.reply_text(f'Error: {str(e)}')

async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    try:
        if data.startswith("page_"):
            _, char_id, page = data.split('_')
            page = int(page)  # Ensure page is an integer
            context.args = [char_id, str(page)]  # Pass page number as argument as a string
            await check_character(update, context)
            await query.answer()  # Acknowledge the callback query without alert
        elif data.startswith("slaves_"):
            parts = data.split('_')
            if len(parts) == 3:
                _, char_id, global_count = parts
                await query.answer(f"🌐 This character has been globally seized {global_count} times!", show_alert=True)
            else:
                await query.answer("Invalid data format.", show_alert=True)
        else:
            await query.answer("Unknown action.", show_alert=True)

    except Exception as e:
        print(f"Error in handle_callback_query: {e}")
        await query.answer(f"Error: {str(e)}", show_alert=True)

# Command handler for /check command
CHECK_HANDLER = CommandHandler('check', check_character, block=False)
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern='^(page_|slaves_)', block=False))
application.add_handler(CHECK_HANDLER)
