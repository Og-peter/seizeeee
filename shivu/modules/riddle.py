from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html
from shivu import user_collection, collection, application
import asyncio
from datetime import datetime, timedelta

# Dictionary to store active guesses and cooldowns
active_guesses = {}
user_cooldowns = {}
user_streaks = {}
character_message_links = {}  # Store links to character images

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
        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ This feature is only available in our support group. Join here:",
            reply_markup=reply_markup
        )
        return

    # Check if there is an active game in the chat
    if chat_id in active_guesses:
        await update.message.reply_text("⚠️ You need to finish the current game before starting a new one!")
        return

    # Check if the user is on cooldown
    cooldown_duration = 30 - user_streaks.get(user_id, 0)  # Reduce cooldown with streaks
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
        'start_time': current_time,
        'hint_given': False
    }
    
    # Store the character image link for use with the "See Character" button
    character_message_links[chat_id] = correct_character['img_url']

    # Set the cooldown for the user
    user_cooldowns[user_id] = current_time + timedelta(seconds=cooldown_duration)

    # Send the question with the character's image
    question = "<b>🏮 Guess the Anime Character! 🏮</b>\n\nReply with the correct name:"
    sent_message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],  # Character image URL from the DB
        caption=question,
        parse_mode='HTML'
    )

    # Schedule a timeout for guessing (e.g., 15 seconds) and a hint after 10 seconds
    asyncio.create_task(guess_timeout(context, chat_id, sent_message.message_id))
    asyncio.create_task(provide_hint(context, chat_id))

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

# Function to provide a hint after 10 seconds
async def provide_hint(context: CallbackContext, chat_id: int):
    await asyncio.sleep(10)
    if chat_id in active_guesses and not active_guesses[chat_id]['hint_given']:
        correct_answer = active_guesses[chat_id]['correct_answer']
        hint = correct_answer[0] + "_" * (len(correct_answer) - 2) + correct_answer[-1]  # First and last letter as a hint
        active_guesses[chat_id]['hint_given'] = True
        await context.bot.send_message(chat_id, text=f"🔍 Hint: {hint}", parse_mode='HTML')

# Message handler to process text guesses
async def guess_text_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()

    # Check if there is an active game in this chat
    if chat_id not in active_guesses:
        return  # Ignore guesses if there is no active game

    correct_answer = active_guesses[chat_id]['correct_answer']
    correct_answer_parts = correct_answer.lower().split()  # Split the correct answer into parts (first and last name)

    # Get the user's mention (username or first name)
    user_mention = mention_html(update.message.from_user.id, update.message.from_user.first_name)

    # Check if the user's answer matches either the first or last name (case-insensitive)
    if user_answer.lower() in correct_answer_parts:
        # Increase streak and tokens
        streak = user_streaks.get(user_id, 0) + 1
        user_streaks[user_id] = streak
        tokens_earned = 10 + (streak * 10)  # Bonus tokens based on streak

        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': tokens_earned}})
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 {user_mention} guessed correctly! The answer was <b>{correct_answer}</b>. You've earned {tokens_earned} tokens! Your streak is now {streak}.",
            parse_mode='HTML'
        )
        del active_guesses[chat_id]  # End the game after the correct answer
    else:
        # Incorrect guess, show a "See Character" button
        message_link = character_message_links.get(chat_id, "#")
        keyboard = [[InlineKeyboardButton("ᴡʜᴇʀᴇ ɪs ᴄʜᴀʀᴀᴄᴛᴇʀ ? ", url=message_link)]]
        await update.message.reply_text(
            'ғɪɴᴅ ᴄʜᴀʀᴀᴄᴛᴇʀ 💎',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Add command handler for starting the anime guess game
application.add_handler(CommandHandler("guess", start_anime_guess_cmd, block=False))
# Add message handler for processing text-based guesses
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_text_handler, block=False))
