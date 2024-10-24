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

# Anime List by Alphabet Command
async def animelist(update: Update, context: CallbackContext):
    await display_anime_list(update, context, 0)

# Function to display anime list with pagination based on the first letter
async def display_anime_list(update: Update, context: CallbackContext, page: int):
    try:
        # Fetch all anime from the database
        all_anime = await collection.find({}).distinct('anime')  # Fetch unique anime names
    except PyMongoError as e:
        await update.message.reply_text(f"Database Error: {e}")
        return
    
    # Sort anime alphabetically
    all_anime = sorted(all_anime)

    # Group by the first letter of the anime
    grouped_anime = {}
    for anime in all_anime:
        first_letter = anime[0].upper()
        if first_letter not in grouped_anime:
            grouped_anime[first_letter] = []
        grouped_anime[first_letter].append(anime)

    alphabet_list = list(grouped_anime.keys())
    total_pages = len(alphabet_list) // 10 + (len(alphabet_list) % 10 > 0)

    # Ensure valid page range
    if page < 0 or page >= total_pages:
        page = 0

    # Create the keyboard with anime list by alphabet and navigation buttons
    keyboard = [
        [InlineKeyboardButton(f"{letter}", callback_data=f"animelist:{page}:{i}")]
        for i, letter in enumerate(alphabet_list[page * 10:(page + 1) * 10])
    ]

    keyboard.append([InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat="")])

    # Add navigation buttons
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"animelist:{page - 1}:0"))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"animelist:{page + 1}:0"))

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle initial message or callback
    if update.message:
        await update.message.reply_text("Select a letter to view anime starting with that letter:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Select a letter to view anime starting with that letter:", reply_markup=reply_markup)

# Callback to handle anime selection by alphabet
async def anime_list_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    page = int(data[1])
    index = int(data[2])

    # If index is 0, go back to anime list
    if index == 0:
        await display_anime_list(update, context, page)
        return

    try:
        # Fetch all anime
        all_anime = await collection.find({}).distinct('anime')
    except PyMongoError as e:
        await query.message.reply_text(f"Database Error: {e}")
        return

    # Group by the first letter
    grouped_anime = {}
    all_anime = sorted(all_anime)
    for anime in all_anime:
        first_letter = anime[0].upper()
        if first_letter not in grouped_anime:
            grouped_anime[first_letter] = []
        grouped_anime[first_letter].append(anime)

    alphabet_list = list(grouped_anime.keys())

    if page * 10 + index >= len(alphabet_list):
        await query.answer("Invalid selection!")
        return

    selected_letter = alphabet_list[page * 10 + index]
    anime_in_letter = sorted(grouped_anime[selected_letter])

    # Display anime starting with the selected letter
    message = f"<b>Anime starting with '{selected_letter}':</b>\n\n"
    for anime in anime_in_letter:
        message += f"{anime}\n"

    # Provide a back button to return to the alphabet list
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=f"animelist:{page}:0")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="HTML", reply_markup=reply_markup)

# Inline search function
async def inline_search(update: Update, context: CallbackContext):
    query = update.inline_query.query
    if not query:
        return

    try:
        # Fetch matching anime based on query
        all_anime = await collection.find({}).distinct('anime')
    except PyMongoError as e:
        await update.inline_query.answer([])
        return

    matching_anime = [
        anime for anime in all_anime if anime.lower().startswith(query.lower())
    ]
    matching_anime = sorted(matching_anime)

    # Create inline search results
    results = [
        InlineQueryResultArticle(
            id=str(i),
            title=f"{anime}",
            input_message_content=InputTextMessageContent(
                f"{anime}"
            )
        )
        for i, anime in enumerate(matching_anime[:50])
    ]

    await update.inline_query.answer(results)

# Handlers
application.add_handler(CommandHandler("animelist", animelist, block=False))
application.add_handler(CallbackQueryHandler(anime_list_callback, pattern="^animelist", block=False))
application.add_handler(InlineQueryHandler(inline_search, block=False))

# End
# by https://github.com/lovetheticx
