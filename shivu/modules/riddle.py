from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html
from shivu import user_collection, collection, application
import asyncio
from datetime import datetime, timedelta

# Dictionary to store active guesses and user data
active_guesses = {}
user_streaks = {}
character_message_links = {}
user_profiles = {}

# Allowed group and support group URL
ALLOWED_GROUP_ID = -1002104939708  # Replace with your allowed group's chat ID
SUPPORT_GROUP_URL = "https://t.me/dynamic_gangs"  # Replace with your actual support group URL

# Function to fetch a random anime character from the database
async def get_random_character():
    try:
        pipeline = [{'$sample': {'size': 1}}]
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
    user_mention = mention_html(user_id, update.effective_user.first_name)  # Mention the command user

    # Check if the command is used in the allowed group
    if chat_id != ALLOWED_GROUP_ID:
        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"<b>⚠️ {user_mention}, this feature is only available in our support group. Join here:</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return

    # Check if there is an active game in the chat
    if chat_id in active_guesses and active_guesses[chat_id].get('active', False):
        await update.message.reply_text(f"<b>⚠️ {user_mention}, you need to finish the current game before starting a new one!</b>", parse_mode='HTML')
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
    question = f"<b>🏮 Guess the Anime Character! 🏮</b>\n\n<u>Reply with the correct name, {user_mention}:</u>"
    sent_message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode='HTML'
    )

    # Schedule hint and timeout tasks
    asyncio.create_task(guess_timeout(context, chat_id, sent_message.message_id))
    asyncio.create_task(provide_hint(context, chat_id, 10))  # First hint after 10 seconds
    asyncio.create_task(provide_hint(context, chat_id, 20))  # Second hint after 20 seconds

# Function to handle guess timeout
async def guess_timeout(context: CallbackContext, chat_id: int, message_id: int):
    await asyncio.sleep(30)

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
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Function to provide hints at different stages
async def provide_hint(context: CallbackContext, chat_id: int, delay: int):
    await asyncio.sleep(delay)
    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']
        hint_stage = active_guesses[chat_id]['hint_stage']

        # Provide different hints based on stage
        if hint_stage == 0:
            hint = correct_answer[0] + "_" * (len(correct_answer) - 2) + correct_answer[-1]
            hint_text = "<i>First Hint:</i> "
        elif hint_stage == 1:
            hint = correct_answer[:2] + "_" * (len(correct_answer) - 3) + correct_answer[-1]
            hint_text = "<i>Second Hint:</i> "
        else:
            return  # No more hints after 2 stages

        active_guesses[chat_id]['hint_stage'] += 1
        await context.bot.send_message(chat_id, text=f"{hint_text}🔍 <b>{hint}</b>", parse_mode='HTML')

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

    # Check if the user's answer matches
    if user_answer == correct_answer:
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
                 f"🔥 Your streak is now <b>{streak}</b>. {badges}",
            parse_mode='HTML'
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
            parse_mode='HTML'
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
