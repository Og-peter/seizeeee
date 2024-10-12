from telegram import Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters
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
    current_time = datetime.now()
    user_id = update.effective_user.id

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

    # Store the active guess for all users
    active_guesses[update.message.chat_id] = {
        'correct_answer': correct_character['name'],
        'start_time': current_time
    }

    # Send the question with the character's image
    question = "<b>🧩 Guess the Anime Character! 🧩</b>\n\nReply with the correct name:"
    sent_message = await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=correct_character['img_url'],
        caption=question,
        parse_mode='HTML'
    )

    # Schedule timeout
    asyncio.create_task(guess_timeout(context, update.message.chat_id, sent_message.message_id))

# Function to handle the guess timeout
async def guess_timeout(context: CallbackContext, chat_id: int, message_id: int):
    await asyncio.sleep(15)

    if chat_id in active_guesses:
        correct_answer = active_guesses[chat_id]['correct_answer']
        del active_guesses[chat_id]

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

    if chat_id not in active_guesses:
        await update.message.reply_text("There is no active game right now.")
        return

    correct_answer = active_guesses[chat_id]['correct_answer']

    if user_answer.lower() == correct_answer.lower():
        # Correct answer
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': 80}})
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 {update.message.from_user.first_name} guessed correctly! The answer was <b>{correct_answer}</b>. You've earned 80 tokens!",
            parse_mode='HTML'
        )
        # End the game
        del active_guesses[chat_id]
    else:
        # Incorrect guess
        await update.message.reply_text(f"❌ {update.message.from_user.first_name}, incorrect guess! Try again.")

# Add command handler for starting the anime guess game
application.add_handler(CommandHandler("animeguess", start_anime_guess_cmd, block=False))
# Add message handler for processing text-based guesses
application.add_handler(MessageHandler(Filters.text & ~Filters.command, guess_text_handler, block=False))
