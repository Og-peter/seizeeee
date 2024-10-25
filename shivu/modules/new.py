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

# Anime List Command
async def animelist(update: Update, context: CallbackContext):
    await display_anime_list(update, context, 0)

# Function to display anime list with pagination based on the first letter
async def display_anime_list(update: Update, context: CallbackContext, page: int):
    try:
        # Fetch all anime from the database
        all_anime = await collection.find({}).distinct('anime')
    except PyMongoError as e:
        await update.message.reply_text(f"Database Error: {e}")
        return
    
    all_anime = sorted(all_anime)
    if not all_anime:
        await update.message.reply_text("No anime found.")
        return

    # Group anime by the first letter
    grouped_anime = {}
    for anime in all_anime:
        first_letter = anime[0].upper()
        if first_letter not in grouped_anime:
            grouped_anime[first_letter] = []
        grouped_anime[first_letter].append(anime)

    alphabet_list = list(grouped_anime.keys())
    total_pages = len(alphabet_list) // 10 + (len(alphabet_list) % 10 > 0)
    page = max(0, min(page, total_pages - 1))  # Ensure valid page range

    # Keyboard for letters with pagination
    keyboard = [
        [InlineKeyboardButton(f"{letter}", callback_data=f"animelist:{page}:{i+1}")]
        for i, letter in enumerate(alphabet_list[page * 10:(page + 1) * 10])
    ]
    keyboard.append([InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat="")])
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"animelist:{page - 1}:0"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"animelist:{page + 1}:0"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Select a letter to view anime starting with that letter:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Select a letter to view anime starting with that letter:", reply_markup=reply_markup)

# Callback for alphabet selection
async def anime_list_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    page = int(data[1])
    index = int(data[2])

    if index == 0:
        await display_anime_list(update, context, page)
        return

    try:
        all_anime = await collection.find({}).distinct('anime')
    except PyMongoError as e:
        await query.message.reply_text(f"Database Error: {e}")
        return

    grouped_anime = {}
    all_anime = sorted(all_anime)
    for anime in all_anime:
        first_letter = anime[0].upper()
        if first_letter not in grouped_anime:
            grouped_anime[first_letter] = []
        grouped_anime[first_letter].append(anime)

    alphabet_list = list(grouped_anime.keys())
    if page * 10 + index - 1 >= len(alphabet_list):
        await query.answer("Invalid selection!")
        return

    selected_letter = alphabet_list[page * 10 + index - 1]
    anime_in_letter = sorted(grouped_anime[selected_letter])

    message = f"<b>Anime starting with '{selected_letter}':</b>\n\n"
    for i, anime in enumerate(anime_in_letter):
        message += f"{i + 1}. {anime}\n"
        
    message += "\nSelect an anime to view its characters."

    # Create buttons to select an anime
    keyboard = [
        [InlineKeyboardButton(f"{anime}", callback_data=f"anime_characters:{anime}")]
        for anime in anime_in_letter
    ]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"animelist:{page}:0")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="HTML", reply_markup=reply_markup)

# Callback to display characters
async def anime_characters_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    anime = query.data.split(":")[1]

    try:
        # Fetch characters for the selected anime
        anime_data = await collection.find_one({'anime': anime}, {'characters': 1})
        characters_list = anime_data.get('characters', []) if anime_data else []

        if not characters_list:
            await query.answer(f"No characters found for the anime '{anime}'!")
            return
        characters_list = sorted(characters_list)
    except PyMongoError as e:
        await query.message.reply_text(f"Database Error: {e}")
        return

    message = f"<b>Characters in '{anime}':</b>\n\n" + "\n".join(characters_list)
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"animelist:0:0")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="HTML", reply_markup=reply_markup)

# Inline search function for anime characters
async def inline_search(update: Update, context: CallbackContext):
    query = update.inline_query.query
    if not query:
        return

    try:
        all_characters = await collection.find({'characters': {'$regex': query, '$options': 'i'}}).distinct('characters')
        matching_characters = sorted(all_characters)
    except PyMongoError as e:
        await update.inline_query.answer([])
        return

    if not matching_characters:
        await update.inline_query.answer([])
        return

    results = [
        InlineQueryResultArticle(
            id=str(i),
            title=character,
            input_message_content=InputTextMessageContent(character)
        )
        for i, character in enumerate(matching_characters[:50])
    ]

    await update.inline_query.answer(results)

# Handlers
application.add_handler(CommandHandler("animelist", animelist, block=False))
application.add_handler(CallbackQueryHandler(anime_list_callback, pattern="^animelist", block=False))
application.add_handler(CallbackQueryHandler(anime_characters_callback, pattern="^anime_characters", block=False))
application.add_handler(InlineQueryHandler(inline_search, block=False))
