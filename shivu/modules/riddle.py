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

# Function to fetch a random anime character from the database
async def get_random_character():
    try:
        pipeline = [{'$sample': {'size': 1}}]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)
        return characters[0] if characters else None
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return None

# Command handler to start the anime guess game
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
            f"<b>⚠️ {user_mention}, this feature is only available in our support group. Join here:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    # Check if there is an active game in the chat
    if chat_id in active_guesses and active_guesses[chat_id].get('active', False):
        await update.message.reply_text(f"<b>⚠️ {user_mention}, you need to finish the current game before starting a new one!</b>", parse_mode=ParseMode.HTML)
        return

    # Get the correct anime character
    correct_character = await get_random_character()
    if not correct_character:
        await update.message.reply_text("⚠️ Could not fetch characters at this time. Please try again later.")
        return

    # Store the active guess for this chat
    active_guesses[chat_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time,
        'hint_stage': 0,
        'active': True
    }

    # Store the character image link
    character_message_links[chat_id] = correct_character['img_url']

    # Send the question with the character's image
    question = f"<b>🏮 Guess the Anime Character! 🏮</b>\n"
    sent_message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode=ParseMode.HTML
    )

    # Schedule hint and timeout tasks using the correct data structure
    context.job_queue.run_once(guess_timeout, 30, context={'chat_id': chat_id, 'message_id': sent_message.message_id})
    context.job_queue.run_once(provide_hint, 10, context={'chat_id': chat_id, 'hint_stage': 0})  # First hint after 10 seconds
    context.job_queue.run_once(provide_hint, 20, context={'chat_id': chat_id, 'hint_stage': 1})  # Second hint after 20 seconds

# Function to handle guess timeout
async def guess_timeout(context: CallbackContext):
    job_data = context.job.context  # Access job data
    chat_id = job_data['chat_id']
    message_id = job_data['message_id']

    # Check if there's still an active game after 30 seconds
    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']

        # Remove the active game after the timeout
        del active_guesses[chat_id]

        # Edit the message to indicate time is up
        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"⏰ <b>Time's up!</b> The correct answer was <b><u>{correct_answer}</u></b>.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Function to provide hints at different stages
async def provide_hint(context: CallbackContext):
    job_data = context.job.context  # Access job data
    chat_id = job_data['chat_id']
    hint_stage = job_data['hint_stage']

    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']

        # Provide different hints based on stage
        if hint_stage == 0:
            # Reveal the last character
            hint = "_" * (len(correct_answer) - 1) + correct_answer[-1]
            hint_text = "<i>First Hint:</i> "
        elif hint_stage == 1:
            # Reveal the first character
            hint = correct_answer[0] + "_" * (len(correct_answer) - 2) + correct_answer[-1]
            hint_text = "<i>Second Hint:</i> "
        else:
            return  # No more hints after 2 stages

        # Update the hint stage
        active_guesses[chat_id]['hint_stage'] += 1
        await context.bot.send_message(chat_id, text=f"{hint_text}🔍 <b>{hint}</b>", parse_mode=ParseMode.HTML)

# Function to handle streaks and provide user profile data
async def guess_text_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip().lower()
    user_mention = mention_html(user_id, update.message.from_user.first_name)  # Mention the guesser

    # Check if there's an active game
    if chat_id not in active_guesses:
        return  # Ignore guesses if there's no active game

    correct_answer = active_guesses[chat_id]['correct_answer'].lower()

    # Check if the user's answer matches any word in the correct answer
    if user_answer in correct_answer.split():  # Check if the user's answer is part of the correct answer
        streak = user_streaks.get(user_id, 0) + 1
        user_streaks[user_id] = streak
        tokens_earned = 10 + (streak * 5)  # Bonus tokens for streaks

        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': tokens_earned}})

        # Award badges for streak milestones
        badges = await award_badges(user_id, streak)

        # Reply tagging the guesser
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 {user_mention} <b>guessed correctly!</b>\n\n"
                 f"🔑 The answer was: <b><u>{correct_answer}</u></b>\n"
                 f"🏅 You've earned <b>{tokens_earned} tokens!</b>\n"
                 f"🔥 Your streak is now <b>{streak}</b>. {badges}\n",
            parse_mode=ParseMode.HTML
        )

        # Remove the active game after the correct guess
        del active_guesses[chat_id]

    else:
        # Incorrect guess, show a "See Character" button
        message_link = character_message_links.get(chat_id, "#")
        keyboard = [[InlineKeyboardButton("🔍 ᴡʜᴇʀᴇ ɪs ᴄʜᴀʀᴀᴄᴛᴇʀ?", url=message_link)]]
        await update.message.reply_text(
            f'💎 {user_mention}, <b>Find the character and try again!</b>',
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
