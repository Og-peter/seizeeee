from datetime import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html

from shivu import user_collection, collection, application

# Dictionary to store active guesses and user data
active_guesses = {}
user_streaks = {}
character_message_links = {}

# Allowed group and support group URL
ALLOWED_GROUP_ID = -1002104939708  # Replace with your allowed group's chat ID
SUPPORT_GROUP_URL = "https://t.me/dynamic_gangs"  # Replace with your actual support group URL

async def start_anime_guess_cmd(update: Update, context: CallbackContext):
    current_time = datetime.now()
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    user_mention = mention_html(user_id, update.effective_user.first_name)  # Mention the command user

    # Check if the command is used in the allowed group
    if chat_id != ALLOWED_GROUP_ID:
        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"<b>⚠️ {user_mention}, this feature is exclusive to our support group. Join here:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    # Check if there is an active game in the chat
    if chat_id in active_guesses and active_guesses[chat_id].get('active', False):
        await update.message.reply_text(
            f"<b>⚠️ {user_mention}, you must complete the current game before starting a new one!</b>",
            parse_mode=ParseMode.HTML
        )
        return

    # Get the correct anime character
    correct_character = await get_random_character()
    if not correct_character:
        await update.message.reply_text("⚠️ Unable to fetch characters at this moment. Please try again later.")
        return

    # Store the active guess for this chat
    active_guesses[chat_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time,
        'attempts': 0,
        'active': True
    }

    # Store the character image link
    character_message_links[chat_id] = correct_character['img_url']

    # Send the question with the character's image
    question = (
        "<b>✨🎭 𝗚𝗨𝗘𝗦𝗦 𝗧𝗛𝗘 𝗔𝗡𝗜𝗠𝗘 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥! 🎭✨</b>\n\n"
        "<i>Think you know who this character is? Give it your best shot!</i>"
    )
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode=ParseMode.HTML
    )

    # Schedule timeout for the game
    asyncio.create_task(guess_timeout(context, chat_id))

# Function to handle guess timeout
async def guess_timeout(context: CallbackContext, chat_id: int):
    await asyncio.sleep(20)

    # Check if there's still an active game after timeout
    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']

        # Remove the active game after the timeout
        del active_guesses[chat_id]

        # Send a message to indicate time is up
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ <b>Time's up!</b> The correct answer was <b><u>{correct_answer}</u></b>.",
            parse_mode=ParseMode.HTML
        )

# Function to handle user guesses and track attempts
async def guess_text_handler(update: Update, context: CallbackContext):
    # Check if update.message is not None to avoid AttributeError
    if update.message is None:
        return  # Ignore if the update does not contain a message

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip().lower()
    user_mention = mention_html(user_id, update.message.from_user.first_name)  # Mention the guesser

    # Check if there's an active game
    if chat_id not in active_guesses:
        return  # Ignore guesses if there's no active game

    correct_answer = active_guesses[chat_id]['correct_answer'].lower()

    # Track the number of attempts
    active_guesses[chat_id]['attempts'] += 1
    attempts = active_guesses[chat_id]['attempts']

    # Check if the user's answer matches any word in the correct answer
    if user_answer in correct_answer.split():  # Check if the user's answer is part of the correct answer
        streak = user_streaks.get(user_id, 0) + 1
        user_streaks[user_id] = streak
        tokens_earned = 10 + (streak * 5)  # Bonus tokens for streaks

        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': tokens_earned}})

        # Award badges for streak milestones
        badges = await award_badges(user_id, streak)

        # Reply tagging the guesser directly
        await update.message.reply_text(
            f"🎉 {user_mention} <b>guessed correctly in {attempts} attempts!</b>\n\n"
            f"🔑 The answer was: <b><u>{correct_answer}</u></b>\n"
            f"🏅 You've earned <b>{tokens_earned} tokens!</b>\n"
            f"🔥 Your streak is now <b>{streak}</b>{badges}\n",
            parse_mode=ParseMode.HTML
        )

        # Remove the active game after the correct guess
        del active_guesses[chat_id]

    else:
        # Incorrect guess, show a "See Character" button
        message_link = character_message_links.get(chat_id, "#")
        feedback = "💪 Keep trying!" if attempts < 3 else "🙌 Almost there, don't give up!"
        keyboard = [[InlineKeyboardButton("🔍 ᴡʜᴇʀᴇ ɪs ᴄʜᴀʀᴀᴄᴛᴇʀ?", url=message_link)]]
        await update.message.reply_text(
            f'{feedback} {user_mention}, <b>Find the character and try again!</b>',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

# Award badges based on streaks
async def award_badges(user_id, streak):
    if streak == 5:
        return "<b>🏅 You've earned the Bronze Badge!</b>"
    elif streak == 10:
        return "<b>🏅 You've earned the Silver Badge!</b>"
    elif streak == 20:
        return "<b>🏅 You've earned the Gold Badge!</b>"
    return ""

# Add command handler for starting the anime guess game
application.add_handler(CommandHandler("guess", start_anime_guess_cmd, block=False))
# Add message handler for processing text-based guesses
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_text_handler, block=False))
