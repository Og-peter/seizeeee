import urllib.request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext
from shivu import application, sudo_users, collection, SUPPORT_CHAT

# A global cache for anime data
anime_cache = []

WRONG_FORMAT_TEXT = """Incorrect Usage ❌️.
Correct Usage: /addanime anime_name post_url img_url

Ensure:
- anime_name: Name of the anime.
- post_url: A valid URL (e.g., Wikipedia or MyAnimeList page).
- img_url: Direct URL to an image of the anime.

Please try again."""

async def add_anime(update: Update, context: CallbackContext) -> None:
    """Handler for the /addanime command."""
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text("You do not have permission to use this command. Please contact the bot owner.")
        return

    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text(WRONG_FORMAT_TEXT)
            return

        # Extract and format arguments
        anime_name = args[0].replace('-', ' ').title()
        post_url = args[1]
        img_url = args[2]

        # Validate URLs
        try:
            urllib.request.urlopen(post_url)
            urllib.request.urlopen(img_url)
        except Exception:
            await update.message.reply_text("One or more provided URLs are invalid. Please check and try again.")
            return

        # Generate unique anime ID
        anime_id = str(await get_next_sequence_number("anime_id")).zfill(2)

        # Anime data
        anime_data = {
            "id": anime_id,
            "name": anime_name,
            "post_url": post_url,
            "img_url": img_url
        }

        try:
            # Send post to the chat where the command is used
            message = await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_url,
                caption=(
                    f"<b>Anime Name:</b> {anime_name}\n"
                    f"<b>More Info:</b> <a href='{post_url}'>Click Here</a>\n"
                    f"<b>ID:</b> {anime_id}\n"
                    f"Added by <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>"
                ),
                parse_mode="HTML"
            )
            anime_data["message_id"] = message.message_id

            # Save to database
            await collection.insert_one(anime_data)
            await update.message.reply_text("Anime successfully added to the database!")
        except Exception as e:
            await update.message.reply_text(f"Failed to post anime in the chat. Error: {e}")
            return
    except Exception as e:
        await update.message.reply_text(
            f"An error occurred while processing your request. Error: {e}\n"
            f"If you believe this is a bug, please report it at {SUPPORT_CHAT}."
        )

async def reload_anime_data(update: Update, context: CallbackContext) -> None:
    """Reload anime data from the database."""
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        # Fetch all anime data from the database
        global anime_cache
        anime_cache = await collection.find().to_list(length=None)
        
        await update.message.reply_text("Anime Sanctum Data Has Been Reloaded From DB ☑️.")
    except Exception as e:
        await update.message.reply_text(f"Failed to reload data from the database. Error: {str(e)}")

async def get_anime(update: Update, context: CallbackContext) -> None:
    """Fetch anime details based on the provided name."""
    anime_name = update.message.text.strip().lower()

    # Search in the global anime cache
    for anime in anime_cache:
        if anime["name"].lower() == anime_name:
            # Create inline keyboard with a link to the post URL
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=anime["name"], url=anime["post_url"])]]
            )

            # Send anime details as a photo with caption and button
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=anime["img_url"],
                caption=f"Watch <b>{anime['name']}</b> Here 👇",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

    # If no anime found, send a fallback message
    await update.message.reply_text("Anime not found in the database. Please check the name and try again.")

# Handler registration
ADD_ANIME_HANDLER = CommandHandler("addanime", add_anime, block=False)
RELOAD_HANDLER = CommandHandler("reload", reload_anime_data, block=False)
ANIME_FETCH_HANDLER = MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime, block=False)

# Adding handlers to the application
application.add_handler(ADD_ANIME_HANDLER)
application.add_handler(RELOAD_HANDLER)
application.add_handler(ANIME_FETCH_HANDLER)
