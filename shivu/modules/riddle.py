from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram import Client, filters
from shivu import user_collection, collection, application
import asyncio
import random
from datetime import datetime, timedelta

# Dictionary to store active guesses
active_guesses = {}
# Dictionary to store user cooldowns
user_cooldowns = {}

# Function to fetch a random anime character from the database
async def get_random_character():
    try:
        pipeline = [
            {'$sample': {'size': 1}}  # Adjust size if needed
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
    user_id = update.effective_user.id
    current_time = datetime.now()

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

    # Generate wrong options by fetching random characters
    wrong_characters = []
    while len(wrong_characters) < 3:
        character = await get_random_character()
        if character and character['_id'] != correct_character['_id']:
            wrong_characters.append(character)

    # Combine correct and wrong answers, then shuffle
    answers = [correct_character['name']] + [char['name'] for char in wrong_characters]
    random.shuffle(answers)

    # Store the active guess
    active_guesses[user_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time
    }

    # Display the image and provide the user with answer options
    question = "<b>🧩 Guess the Anime Character! 🧩</b>\n\nChoose the correct name below:"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(str(answers[0]), callback_data=f'guess_answer_{user_id}_{answers[0]}'), InlineKeyboardButton(str(answers[1]), callback_data=f'guess_answer_{user_id}_{answers[1]}')],
            [InlineKeyboardButton(str(answers[2]), callback_data=f'guess_answer_{user_id}_{answers[2]}'), InlineKeyboardButton(str(answers[3]), callback_data=f'guess_answer_{user_id}_{answers[3]}')],
        ]
    )

    # Send the question with the character's image
    sent_message = await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=correct_character['img_url'],
        caption=question,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    # Schedule timeout
    asyncio.create_task(guess_timeout(context, user_id, sent_message.chat_id, sent_message.message_id))

# Function to handle the guess timeout
async def guess_timeout(context: CallbackContext, user_id: int, chat_id: int, message_id: int):
    await asyncio.sleep(15)

    if user_id in active_guesses:
        correct_answer = active_guesses[user_id]['correct_answer']
        del active_guesses[user_id]

        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"⏰ Time's up! The correct answer was <b>{correct_answer}</b>.",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Callback handler to process the anime guess answer
async def guess_answer_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    guess_user_id = int(data[2])
    answer = data[3]

    if user_id != guess_user_id:
        await query.answer("This guess is not for you.", show_alert=True)
        return

    if guess_user_id not in active_guesses:
        await query.answer("You are not currently participating in any guess.", show_alert=True)
        return

    correct_answer = active_guesses[guess_user_id]['correct_answer']

    if answer == correct_answer:
        # Correct answer
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': 80}})
        await query.message.edit_caption("🎉 Correct guess! You got 80 tokens.", parse_mode='HTML')
    else:
        # Incorrect answer
        await query.message.edit_caption(f"❌ Incorrect guess. The correct answer was <b>{correct_answer}</b>.", parse_mode='HTML')

    # Remove the active guess
    del active_guesses[guess_user_id]
    # Set user cooldown for 30 seconds
    user_cooldowns[guess_user_id] = datetime.now() + timedelta(seconds=30)

# Add command handler for starting the anime guess game
application.add_handler(CommandHandler("animeguess", start_anime_guess_cmd, block=False))
# Add callback query handler for the anime guess answers
application.add_handler(CallbackQueryHandler(guess_answer_callback, pattern=r'guess_answer_', block=False))
