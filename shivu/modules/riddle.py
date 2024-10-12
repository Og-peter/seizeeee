from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html
from shivu import user_collection, collection, application
import asyncio
from datetime import datetime, timedelta

# Dictionary to store active guesses
active_guesses = {}
# Dictionary to store user cooldowns
user_cooldowns = {}

# Define allowed group and support group URL
ALLOWED_GROUP_ID = -1002104939708  # Replace with your allowed group's chat ID
SUPPORT_GROUP_URL = "https://t.me/dynamic_gangs"  # Replace with your actual support group URL

# Function to fetch a random anime character from the database
async def get_random_character():
    try:
        pipeline = [
            {'$sample': {'size': 1}}  # Get one random character
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)
        if characters:
            return characters[0]
        return None
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return None

# Command handler to start the anime guess game
async def start_anime_guess_cmd(update: Update, context: CallbackContext):
    current_time = datetime.now()
    user_id = update.effective_user.id
    chat_id = update.message.chat_id

    # Check if the command is used in the allowed group
    if chat_id != ALLOWED_GROUP_ID:
        # Send message with a button linking to the support group
        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ This feature is only available in our support group. Join here:",
            reply_markup=reply_markup
        )
        return

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        remaining_time = (user_cooldowns[user_id] - current_time).total_seconds()
        await update.message.reply_text(f"⏳ Please wait {int(remaining_time)} seconds before starting a new guess.")
        return

    # Get the correct anime character
    correct_character = await get_random_character()

    if not correct_character:
        await update.message.reply_text("⚠️ Could not fetch characters at this time. Please try again later.")
        return

    # Store the active guess for this chat
    active_guesses[chat_id] = {
        'correct_answer': correct_character['name'],  # Store the full name of the character
        'start_time': current_time
    }

    # Set the cooldown for the user (e.g., 30 seconds)
    user_cooldowns[user_id] = current_time + timedelta(seconds=30)

    # Send the question with the character's image
    question = "<b>🏮 Guess the Anime Character! 🏮</b>\n\nReply with the correct name:"
    sent_message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],  # Character image URL from the DB
        caption=question,
        parse_mode='HTML'
    )

    # Schedule a timeout for guessing (e.g., 15 seconds)
    asyncio.create_task(guess_timeout(context, chat_id, sent_message.message_id))

# Function to handle the guess timeout
async def guess_timeout(context: CallbackContext, chat_id: int, message_id: int):
    await asyncio.sleep(15)

    # Check if there is still an active game after 15 seconds
    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']
        del active_guesses[chat_id]  # Remove active guess after timeout

        # Edit the message to indicate the time is up
        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"⏰ Time's up! The correct answer was <b>{correct_answer}</b>.",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Message handler to process text guesses
async def guess_text_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()

    # Check if there is an active game in this chat
    if chat_id not in active_guesses:
        return  # Ignore guesses if there is no active game

    correct_answer = active_guesses[chat_id]['correct_answer']
    correct_first_name = correct_answer.split()[0].lower()  # Extract and lowercase the first name

    # Get the user's mention (username or first name)
    user_mention = mention_html(update.message.from_user.id, update.message.from_user.first_name)

    # Check if the user's answer matches the first name (case-insensitive)
    if user_answer.lower() == correct_first_name:
        # Correct answer
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': 80}})
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 {user_mention} guessed correctly! The answer was <b>{correct_answer}</b>. You've earned 80 tokens!",
            parse_mode='HTML'
        )
        # End the game
        del active_guesses[chat_id]
    else:
        # Incorrect guess, provide feedback with the username mention
        await update.message.reply_text(f"❌ {user_mention}, that's incorrect! Try again.", parse_mode='HTML')

# Add command handler for starting the anime guess game
application.add_handler(CommandHandler("guess", start_anime_guess_cmd, block=False))
# Add message handler for processing text-based guesses
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_text_handler, block=False))
