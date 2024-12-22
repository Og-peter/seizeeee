import urllib.request
from pymongo import ReturnDocument
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaVideo
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

# Step 1: Start the process to upload a character
async def start_upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text("Ask My Owner...")
        return
    
    keyboard = [
        [InlineKeyboardButton("Add New Character", callback_data="add_character")],
        [InlineKeyboardButton("Search by Anime", callback_data="search_anime")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

# Step 2: Add a new character
async def add_character_step(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Select Anime", callback_data="select_anime")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("First, select the anime for this character:", reply_markup=reply_markup)

# Step 3: Select an anime
async def select_anime(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    # Example: Anime options can be populated dynamically from the database
    anime_list = ["Naruto", "One Piece", "Bleach", "Attack on Titan"]
    keyboard = [[InlineKeyboardButton(anime, callback_data=f"anime_{anime}")] for anime in anime_list]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose the anime:", reply_markup=reply_markup)

# Step 4: Set character details
async def anime_selected(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    anime = query.data.split("_", 1)[1]
    context.user_data["anime"] = anime
    
    keyboard = [
        [InlineKeyboardButton("Set Character Name", callback_data="set_character_name")],
        [InlineKeyboardButton("Set Rarity", callback_data="set_rarity")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Anime selected: {anime}\nNow, set character details:", reply_markup=reply_markup)

# Step 5: Upload video and send to the channel
async def set_character_name(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("Send me the character's name:")
    return  # Handle the next message to capture the name

# Handle rarity selection
async def set_rarity(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚜️ Animated", callback_data="rarity_1")],
        [InlineKeyboardButton("⭐ Rare", callback_data="rarity_2")],
        [InlineKeyboardButton("🌟 Ultra Rare", callback_data="rarity_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select character rarity:", reply_markup=reply_markup)

# Handle rarity selection result
async def rarity_selected(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    rarity = query.data.split("_", 1)[1]
    context.user_data["rarity"] = rarity
    
    await query.edit_message_text(f"Rarity selected: {rarity}\nNow send the video URL:")

# Final step: Save the character and upload
async def finalize_upload(update: Update, context: CallbackContext) -> None:
    if "anime" not in context.user_data or "rarity" not in context.user_data:
        await update.message.reply_text("Please complete all steps first.")
        return
    
    anime = context.user_data["anime"]
    rarity = context.user_data["rarity"]
    video_url = update.message.text  # Assuming the URL is sent as a message
    
    try:
        urllib.request.urlopen(video_url)
    except:
        await update.message.reply_text("Invalid URL.")
        return
    
    character_name = context.user_data.get("character_name", "Unknown Character")
    id = str(await get_next_sequence_number("character_id")).zfill(2)
    category = get_category(character_name)
    
    character = {
        "img_url": video_url,
        "name": character_name,
        "anime": anime,
        "rarity": rarity,
        "id": id,
        "category": category
    }
    
    caption = f"Oni chan New Character Added!\n\n{anime}\n{id}: {character_name}\n(𝙍𝘼𝙍𝙄𝙏𝙔: {rarity})\n"
    if category:
        caption += f"\n{category}\n"
    caption += f"\n➼ ᴀᴅᴅᴇᴅ ʙʏ: <a href=\"tg://user?id={update.effective_user.id}\">{update.effective_user.first_name}</a>"
    
    try:
        message = await context.bot.send_video(
            chat_id=CHARA_CHANNEL_ID,
            video=video_url,
            caption=caption,
            parse_mode="HTML"
        )
        character["message_id"] = message.message_id
        await collection.insert_one(character)
        await update.message.reply_text("Character successfully added!")
    except Exception as e:
        await update.message.reply_text(f"Error adding character: {e}")

# Add handlers
application.add_handler(CommandHandler("hvupload", start_upload))
application.add_handler(CallbackQueryHandler(add_character_step, pattern="^add_character$"))
application.add_handler(CallbackQueryHandler(select_anime, pattern="^select_anime$"))
application.add_handler(CallbackQueryHandler(anime_selected, pattern="^anime_"))
application.add_handler(CallbackQueryHandler(set_character_name, pattern="^set_character_name$"))
application.add_handler(CallbackQueryHandler(set_rarity, pattern="^set_rarity$"))
application.add_handler(CallbackQueryHandler(rarity_selected, pattern="^rarity_"))
