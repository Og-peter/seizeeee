from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application, shivuu
import logging

app = shivuu

from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden

MUST_JOIN = "dosti_ki_baate"

async def shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    rarity_3_characters = await collection.find({'rarity': "💸 Premium Edition"}).to_list(length=7)

    try:
        if MUST_JOIN:
            await app.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        # User has not joined, return without sending the start message
        await update.message.reply_text('Please unlock me to use this command.')
        return

    if not rarity_3_characters:
        await update.message.reply_text("No legendary characters available in the shop.")
        return
        
    first_character = rarity_3_characters[0]
    reply_markup = get_inline_keyboard(first_character)
    message = await context.bot.send_photo(
        update.message.chat_id,
        photo=first_character['img_url'],
        caption=f"🪙Welcome to the Shop! Choose a character to buy:\n\n"
                f"🏮Anime Name: {first_character['anime']}\n"
                f"🎴Character Name: {first_character['name']}\n"
                f"🌀Rarity: {first_character['rarity']}\n"
                f"🎗️Character ID: {first_character['id']}\n"
                f"💸Coin Price: {first_character['coin_price']}",
        reply_markup=reply_markup
    )
    
    context.user_data['shop_message'] = {'message_id': message.message_id, 'current_index': 0, 'user_id': update.effective_user.id}

async def next_character(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data.get('shop_message')
    if user_data is None or user_data['user_id'] != update.effective_user.id:
        return  # Do nothing if user_data is not found or the user is different

    current_index = user_data.get('current_index', 0)
    rarity_3_characters = await collection.find({'rarity': "💸 Premium Edition"}).to_list(length=700)

    if current_index + 1 < len(rarity_3_characters):
        # Increment the current_index to get the next character
        current_index += 1
        next_character = rarity_3_characters[current_index]
        reply_markup = get_inline_keyboard(next_character, current_index)

        # Create the caption with details of the next character
        caption = f"🪙Welcome to the Shop! Choose a character to buy:\n\n" \
                  f"🏮Anime Name: {next_character['anime']}\n" \
                  f"🎴Character Name: {next_character['name']}\n" \
                  f"🌀Rarity: {next_character['rarity']}\n" \
                  f"🎗️Character ID: {next_character['id']}\n" \
                  f"💸Coin Price: {next_character['coin_price']}"

        # Update the existing message with details of the next character
        await context.bot.edit_message_media(
            chat_id=update.callback_query.message.chat_id,
            message_id=user_data['message_id'],
            media=InputMediaPhoto(media=next_character['img_url'], caption=caption),
            reply_markup=reply_markup
        )

        # Update the current_index in user_data
        context.user_data['shop_message']['current_index'] = current_index

async def close_shop(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data.get('shop_message')
    if user_data is None:
        return  # Do nothing if user_data is not found

    message_id = user_data.get('message_id')
    if message_id:
        try:
            await context.bot.delete_message(chat_id=update.callback_query.message.chat_id, message_id=message_id)
        except Exception as e:
            logging.error(f"Error deleting message: {e}")

    del context.user_data['shop_message']

def get_inline_keyboard(character, current_index=0, total_count=7):
    keyboard = []

    if current_index == 0:
        # For the first character, display "CLOSED" and "NEXT" buttons
        keyboard.append([
            InlineKeyboardButton("❎𝘾𝙇𝙊𝙎𝙀𝘿❎", callback_data="shop:closed"),
            InlineKeyboardButton("➡️𝙉𝙀𝙓𝙏➡️", callback_data=f"shop_next_{current_index + 1}")
        ])
    else:
        # For all other characters, display both "BACK" and "NEXT" buttons
        keyboard.append([
            InlineKeyboardButton(" ⬅️𝘽𝘼𝘾𝙆⬅️", callback_data="shop:back"),
            InlineKeyboardButton("➡️𝙉𝙀𝙓𝙏➡️", callback_data=f"shop_next_{current_index + 1}")
        ])

    # Add "Buy" button for all characters
    keyboard.append([InlineKeyboardButton("✅𝘽𝙐𝙔✅", callback_data=f"buy:{character['id']}")])

    return InlineKeyboardMarkup(keyboard)

async def set_price(update: Update, context: CallbackContext) -> None:
    # Get the user ID of the person invoking the command
    user_id = update.effective_user.id

    # Check if the user is the owner (replace '6069337486' with the actual owner ID)
    if user_id != 6655070772:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Invalid command format. Use /set (character ID) (coin price)")
        return

    character_id, coin_price = args
    result = await collection.update_one({'id': character_id}, {'$set': {'coin_price': coin_price}})

    if result.modified_count == 1:
        await update.message.reply_text(f"Coin price for Character ID {character_id} set to {coin_price}")
    else:
        await update.message.reply_text(f"Failed to set coin price. Character ID {character_id} not found.")

async def buy_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    character_id_str = query.data.split(":")[1]  # Extract character ID as a string
    character_id = int(character_id_str)

    character = await collection.find_one({'id': character_id_str})  # Use the string ID in the query

    if not character:
        await query.answer("Character not found.")
        return

    user_id = update.effective_user.id

    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'characters': 1})

    if not user_data:
        await query.answer("Failed to retrieve user data.")
        return

    coin_price = int(character.get('coin_price', 0))  # Convert coin_price to integer

    if user_data.get('balance', 0) < coin_price:
        await query.answer("Insufficient balance to buy this character.")
        return

    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -coin_price}})
    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})

    await query.answer(f"You have successfully bought {character['name']} for {coin_price} coins!")

def get_inline_keyboard(character, current_index=0, total_count=7):
    keyboard = []

    if current_index == 0:
        # For the first character, display "CLOSED" and "NEXT" buttons
        keyboard.append([
            InlineKeyboardButton("❎𝘾𝙇𝙊𝙎𝙀𝘿❎", callback_data="shop:closed"),
            InlineKeyboardButton("➡️𝙉𝙀𝙓𝙏➡️", callback_data=f"shop_next_{current_index + 1}")
        ])
    else:
        # For all other characters, display both "BACK" and "NEXT" buttons
        keyboard.append([
            InlineKeyboardButton(" ⬅️𝘽𝘼𝘾𝙆⬅️", callback_data="shop:back"),
            InlineKeyboardButton("➡️𝙉𝙀𝙓𝙏➡️", callback_data=f"shop_next_{current_index + 1}")
        ])

    # Add "Buy" button for all characters
    keyboard.append([InlineKeyboardButton("✅𝘽𝙐𝙔✅", callback_data=f"buy:{character['id']}")])

    return InlineKeyboardMarkup(keyboard)

async def previous_character(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data.get('shop_message')
    if user_data is None:
        return  # Do nothing if user_data is not found

    current_index = user_data.get('current_index', 0)
    rarity_3_characters = await collection.find({'rarity': "💸 Premium Edition"}).to_list(length=7)

    if current_index - 1 >= 0:
        # Decrement the current_index to get the previous character
        current_index -= 1
        previous_character = rarity_3_characters[current_index]
        reply_markup = get_inline_keyboard(previous_character, current_index)

        # Create the caption with details of the previous character
        caption = f"🪙Welcome back to the Shop! Choose a character to buy:\n\n" \
                  f"🏮Anime Name: {previous_character['anime']}\n" \
                  f"🎴Character Name: {previous_character['name']}\n" \
                  f"🌀Rarity: {previous_character['rarity']}\n" \
                  f"🎗️Character ID: {previous_character['id']}\n" \
                  f"💸Coin Price: {previous_character['coin_price']}"

        # Update the existing message with details of the previous character
        await context.bot.edit_message_media(
            chat_id=update.callback_query.message.chat_id,
            message_id=user_data['message_id'],
            media=InputMediaPhoto(media=previous_character['img_url'], caption=caption),
            reply_markup=reply_markup
        )

        # Update the current_index in user_data
        context.user_data['shop_message']['current_index'] = current_index


# Add a handler for the 'closed' button
application.add_handler(CallbackQueryHandler(close_shop, pattern=r'^shop:closed$'))
application.add_handler(CallbackQueryHandler(previous_character, pattern=r'^shop:back$'))
application.add_handler(CallbackQueryHandler(next_character, pattern=r'^shop_next_\d+$'))
application.add_handler(CommandHandler("shop", shop, block=False))
application.add_handler(CommandHandler("set", set_price, block=False))
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy:\d+$'))
