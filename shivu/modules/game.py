from datetime import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.helpers import mention_html

from shivu import user_collection, collection, application
import random

# Dictionary to store active games
active_scramble_games = {}

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
        print(f"Error fetching character: {e}")
        return None

# Scramble the character name
def scramble_name(name):
    scrambled = ''.join(random.sample(name, len(name)))
    return scrambled

# Command to start the scramble game
async def start_game_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    user_mention = mention_html(user_id, update.effective_user.first_name)

    if chat_id != ALLOWED_GROUP_ID:
        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"<b>⚠️ {user_mention}, this feature is only available in our support group. Join here:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    if user_id in active_scramble_games:
        await update.message.reply_text(
            f"<b>⚠️ {user_mention}, you already have an active game! Use /endgame to terminate it before starting a new one.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    character = await get_random_character()
    if not character:
        await update.message.reply_text(
            "<b>⚠️ Could not fetch characters at this time. Please try again later.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    original_name = character['name']
    scrambled_name = scramble_name(original_name)

    active_scramble_games[user_id] = {
        'original_name': original_name.lower(),
        'scrambled_name': scrambled_name,
        'attempts_left': 5,
        'hints_used': 0,
        'character_img': character['img_url']
    }

    await update.message.reply_text(
        f"<b>🎉 Word Scramble Game Started!</b>\n\n"
        f"<i>Can you unscramble this word?</i>\n"
        f"<b>{scrambled_name}</b>\n\n"
        f"🕒 You have <b>5 attempts</b> to guess the correct word.\n"
        f"🪄 Use <b>/gethint</b> for help (up to 2 hints).\n"
        f"🚪 Use <b>/endgame</b> to terminate the game.",
        parse_mode=ParseMode.HTML
    )

# Command to provide a hint
async def get_hint(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id not in active_scramble_games:
        await update.message.reply_text(
            "<b>⚠️ You don't have an active game! Use /startgame to begin.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    game_data = active_scramble_games[user_id]
    hints_used = game_data['hints_used']

    if hints_used >= 2:
        await update.message.reply_text(
            "<b>⚠️ You have already used all your hints!</b>",
            parse_mode=ParseMode.HTML
        )
        return

    original_name = game_data['original_name']
    revealed_chars = random.sample(original_name, hints_used + 1)
    hint = ''.join([char if char in revealed_chars else '_' for char in original_name])

    game_data['hints_used'] += 1
    await update.message.reply_text(
        f"<b>🔍 Hint:</b> <i>{hint.upper()}</i>\n"
        f"💡 {2 - hints_used} hints remaining.",
        parse_mode=ParseMode.HTML
    )

# Command to terminate the game
async def end_game_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id in active_scramble_games:
        del active_scramble_games[user_id]
        await update.message.reply_text(
            "<b>❌ Your game has been terminated.</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "<b>⚠️ You don't have an active game to terminate.</b>",
            parse_mode=ParseMode.HTML
        )

# Message handler to process guesses
async def process_guess(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_guess = update.message.text.strip().lower()

    if user_id not in active_scramble_games:
        return

    game_data = active_scramble_games[user_id]
    original_name = game_data['original_name']

    if user_guess == original_name:
        img_url = game_data['character_img']
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'collection': {'name': original_name.capitalize(), 'img_url': img_url}}},
            upsert=True
        )
        del active_scramble_games[user_id]

        await update.message.reply_photo(
            photo=img_url,
            caption=f"<b>🎉 Congratulations!</b>\n"
                    f"You unscrambled the word: <b>{original_name.capitalize()}</b>\n\n"
                    f"🌟 The character has been added to your collection!",
            parse_mode=ParseMode.HTML
        )
    else:
        game_data['attempts_left'] -= 1
        attempts_left = game_data['attempts_left']

        if attempts_left > 0:
            await update.message.reply_text(
                f"<b>❌ Incorrect guess!</b>\n"
                f"🕒 You have <b>{attempts_left}</b> attempts left.",
                parse_mode=ParseMode.HTML
            )
        else:
            del active_scramble_games[user_id]
            await update.message.reply_text(
                f"<b>❌ Game Over!</b>\n"
                f"The correct word was: <b>{original_name.capitalize()}</b>.\n"
                f"Better luck next time!",
                parse_mode=ParseMode.HTML
            )

# Add command handlers
application.add_handler(CommandHandler("startgame", start_game_cmd, block=False))
application.add_handler(CommandHandler("gethint", get_hint, block=False))
application.add_handler(CommandHandler("endgame", end_game_cmd, block=False))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_guess, block=False))
