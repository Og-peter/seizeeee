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
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check character_id')
            return
        character_id = args[0]
        
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
        
        # Fetch top 10 users with this character
        cursor = user_collection.find(
            {'characters.id': character_id},
            {'_id': 1, 'id': 1, 'first_name': 1, 'last_name': 1, 'username': 1, 'profile_name': 1, 'characters.$': 1}
        ).sort([('characters.count', -1)]).limit(10)

        users = await cursor.to_list(length=10)

        # Debug: Print each user's full data to understand the structure
        for user in users:
            print("User Data:", user)  # Print the full user data to the console

        if users:
            response_message += "\n\n🌐 <b>Top 10 Grabbers of This Waifu:</b>\n\n"
            for i, user in enumerate(users, start=1):
                # Build the user's name (try multiple fields)
                full_name = user.get('profile_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown User')
                seized_count = user['characters'][0].get('count', 1)
                
                # Create mention link for the user
                mention = f"<a href='tg://user?id={user['id']}'>{escape(full_name)}</a>"
                response_message += f"├ {i:02d}. ➔ {mention} ✨ ➔ {seized_count}x\n"
        else:
            response_message += "\n\nNo users found with this character."
        
        # Create buttons for enhanced user interaction
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌐 View Global Seize Count", callback_data=f"slaves_{character['id']}_{global_count}"),
                InlineKeyboardButton("💎 Character Details", callback_data=f"details_{character['id']}")
            ]
        ])

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
        if data.startswith("slaves_"):
            parts = data.split('_')
            if len(parts) == 3:
                _, char_id, global_count = parts
                await query.answer(f"🌐 This character has been globally seized {global_count} times!", show_alert=True)
            else:
                await query.answer("Invalid data format.", show_alert=True)
        elif data.startswith("details_"):
            char_id = data.split('_')[1]
            # Fetch and display additional character details if needed
            character = await collection.find_one({'id': char_id})
            if character:
                detail_message = (
                    f"💎 <b>Character Details:</b>\n\n"
                    f"<b>Name:</b> {character['name']}\n"
                    f"<b>Anime:</b> {character['anime']}\n"
                    f"<b>Rarity:</b> {character['rarity']} 🌟\n"
                    f"<b>Description:</b> {character.get('description', 'No description available.')}\n"
                )
                await query.message.reply_text(detail_message, parse_mode='HTML')
            else:
                await query.answer("Character details not found.", show_alert=True)
        else:
            await query.answer("Unknown action.", show_alert=True)

    except Exception as e:
        print(f"Error in handle_callback_query: {e}")
        await query.answer(f"Error: {str(e)}", show_alert=True)

# Command handler for /check command
CHECK_HANDLER = CommandHandler('check', check_character, block=False)
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern='^(slaves_|details_)', block=False))
application.add_handler(CHECK_HANDLER)
