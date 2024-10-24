# Imports
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputTextMessageContent, InlineQueryResultArticle
)
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, InlineQueryHandler, 
    CallbackContext
)
from shivu import application, collection
from pymongo.errors import PyMongoError

# Character List Command
async def chlist(update: Update, context: CallbackContext):
    await display_character_list(update, context, 0)

# Function to display character list with pagination
async def display_character_list(update: Update, context: CallbackContext, page: int):
    try:
        # Fetch all characters from the database
        all_characters = await collection.find({}).to_list(length=None)
    except PyMongoError as e:
        await update.message.reply_text(f"Database Error: {e}")
        return
    
    grouped_characters = {}
    
    # Group characters by anime
    for character in all_characters:
        if character['anime'] not in grouped_characters:
            grouped_characters[character['anime']] = []
        grouped_characters[character['anime']].append(character)

    total_animes = len(grouped_characters)
    total_pages = (total_animes // 10) + (1 if total_animes % 10 != 0 else 0)

    # Ensure valid page range
    if page < 0 or page >= total_pages:
        page = 0

    # Create the keyboard with anime list and navigation buttons
    keyboard = [
        [InlineKeyboardButton(f"{anime} ({len(grouped_characters[anime])})", callback_data=f"chlist:{page}:{i}")]
        for i, anime in enumerate(list(grouped_characters.keys())[page * 10:(page + 1) * 10])
    ]

    keyboard.append([InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat="")])

    # Add navigation buttons
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"chlist:{page - 1}:0"))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"chlist:{page + 1}:0"))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle initial message or callback
    if update.message:
        await update.message.reply_text("Select an anime to view its characters:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Select an anime to view its characters:", reply_markup=reply_markup)

# Callback to handle character selection
async def character_list_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    page = int(data[1])
    index = int(data[2])

    # If index is 0, go back to anime list
    if index == 0:
        await display_character_list(update, context, page)
        return

    try:
        # Fetch all characters
        all_characters = await collection.find({}).to_list(length=None)
    except PyMongoError as e:
        await query.message.reply_text(f"Database Error: {e}")
        return

    # Group characters by anime
    grouped_characters = {}
    for character in all_characters:
        if character['anime'] not in grouped_characters:
            grouped_characters[character['anime']] = []
        grouped_characters[character['anime']].append(character)

    anime_list = list(grouped_characters.keys())

    if page * 10 + index >= len(anime_list):
        await query.answer("Invalid selection!")
        return

    anime = anime_list[page * 10 + index]
    characters = sorted(grouped_characters[anime], key=lambda x: x['rarity'], reverse=True)

    # Display character information
    message = f"<b>{anime}</b>\n\n"
    for character in characters:
        message += f"{character['id']} {character['name']} ({character['rarity']})\n"

    # Provide a back button to return to the anime list
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=f"chlist:{page}:0")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="HTML", reply_markup=reply_markup)

# Inline search function
async def inline_search(update: Update, context: CallbackContext):
    query = update.inline_query.query
    if not query:
        return

    try:
        # Fetch matching characters based on query
        all_characters = await collection.find({}).to_list(length=None)
    except PyMongoError as e:
        await update.inline_query.answer([])
        return

    matching_characters = [
        char for char in all_characters if query.lower() in char['name'].lower()
    ]
    matching_characters = sorted(matching_characters, key=lambda x: x['rarity'], reverse=True)

    # Create inline search results
    results = [
        InlineQueryResultArticle(
            id=str(char['_id']),
            title=f"{char['name']} ({char['rarity']})",
            input_message_content=InputTextMessageContent(
                f"{char['id']} {char['name']} ({char['rarity']})"
            )
        )
        for char in matching_characters[:50]
    ]

    await update.inline_query.answer(results)

# Handlers
application.add_handler(CommandHandler("chlist", chlist, block=False))
application.add_handler(CallbackQueryHandler(character_list_callback, pattern="^chlist", block=False))
application.add_handler(InlineQueryHandler(inline_search, block=False))

# End
# by https://github.com/lovetheticx
