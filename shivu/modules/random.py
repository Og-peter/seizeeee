from datetime import datetime
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, filters, Application
from telegram.helpers import mention_html

from shivu import user_collection, collection, application

# Dictionary to track active guesses
active_guesses = {}
user_streaks = {}
character_message_links = {}

# Fetch random character from database
async def get_random_character():
    pipeline = [{'$sample': {'size': 1}}]
    cursor = collection.aggregate(pipeline)
    characters = await cursor.to_list(length=1)
    return characters[0] if characters else None

# Start the anime guess game in each group every 5 minutes
async def periodic_character_guess(context: CallbackContext):
    for chat_id in context.bot.chat_ids:
        await start_anime_guess_in_group(context, chat_id)

# Start a character guessing game in a specific group
async def start_anime_guess_in_group(context: CallbackContext, chat_id: int):
    current_time = datetime.now()
    correct_character = await get_random_character()
    if not correct_character:
        return  # Skip if no character found

    # Initialize a new game in the group
    active_guesses[chat_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time,
        'attempts': 0,
        'active': True
    }
    character_message_links[chat_id] = correct_character['img_url']

    # Send the character image and question
    question = (
        "<b>❄️ Guess the Anime Character! ❄️</b>\n"
        "<i>Hint: Known for unique style and powers!</i>"
    )
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode=ParseMode.HTML
    )

    # Schedule timeout for the current game
    asyncio.create_task(guess_timeout(context, chat_id))

# Handle guess timeout
async def guess_timeout(context: CallbackContext, chat_id: int):
    await asyncio.sleep(300)  # 5 minutes timeout
    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']
        del active_guesses[chat_id]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ Time's up! The correct answer was: <b><u>{correct_answer}</u></b>.",
            parse_mode=ParseMode.HTML
        )

# Process guesses from users
async def guess_text_handler(update: Update, context: CallbackContext):
    if update.message is None:
        return  # Ignore if no message

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip().lower()
    user_mention = mention_html(user_id, update.message.from_user.first_name)

    if chat_id not in active_guesses:
        return  # No active game in this chat

    correct_answer = active_guesses[chat_id]['correct_answer'].lower()
    active_guesses[chat_id]['attempts'] += 1
    attempts = active_guesses[chat_id]['attempts']

    if user_answer in correct_answer.split():
        streak = user_streaks.get(user_id, 0) + 1
        user_streaks[user_id] = streak
        tokens_earned = 10 + (streak * 5)  # Bonus for streaks

        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': tokens_earned}})

        badges = await award_badges(user_id, streak)

        await update.message.reply_text(
            f"🎉 {user_mention} guessed correctly in {attempts} attempts!\n"
            f"🔑 Answer: <b>{correct_answer}</b>\n"
            f"🏅 You've earned <b>{tokens_earned} tokens!</b>\n"
            f"🔥 Your streak is now <b>{streak}</b>{badges}",
            parse_mode=ParseMode.HTML
        )

        del active_guesses[chat_id]

    else:
        message_link = character_message_links.get(chat_id, "#")
        feedback = "💪 Keep trying!" if attempts < 3 else "🙌 Almost there!"
        keyboard = [[InlineKeyboardButton("🔍 See Character", url=message_link)]]
        await update.message.reply_text(
            f'{feedback} {user_mention}, find the character and try again!',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

# Award badges based on streaks
async def award_badges(user_id, streak):
    if streak == 5:
        return "<b>🏅 Bronze Badge earned!</b>"
    elif streak == 10:
        return "<b>🏅 Silver Badge earned!</b>"
    elif streak == 20:
        return "<b>🏅 Gold Badge earned!</b>"
    return ""

# Set up the periodic character guess game every 5 minutes
async def periodic_character_guess_job(context: CallbackContext):
    while True:
        await periodic_character_guess(context)
        await asyncio.sleep(300)  # Send every 5 minutes

# Start periodic job when the bot starts
async def on_startup():
    asyncio.create_task(periodic_character_guess_job(application))

# Add handlers
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_text_handler))
application.add_handler(on_startup)
