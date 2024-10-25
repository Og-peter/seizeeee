import logging
import time
from pymongo import ReturnDocument
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, user_totals_collection
from datetime import datetime
# For python-telegram-bot version 20.x or later
from telegram import Update
from telegram.constants import ParseMode

# For python-telegram-bot version before 20.x
# from telegram import Update, ParseMode

# Rest of your code...

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for frequency limits
MIN_FREQUENCY = 100
MAX_FREQUENCY = 10000
DEFAULT_FREQUENCY = 1000  # Default frequency for resetting
CHANGE_COOLDOWN = 60 * 60  # 1 hour cooldown before another change
last_change_time = {}  # Dictionary to track last frequency change time per chat

# Telegram chat ID of the logs group where notifications will be sent
LOGS_GROUP_CHAT_ID = -1002446048543  # Replace with your actual logs group chat ID

# Utility function to send log messages to the log channel
async def send_log_message(message: str):
    try:
        await application.bot.send_message(LOGS_GROUP_CHAT_ID, message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to send log message: {e}")

# Utility function to check cooldown period
def is_cooldown_active(chat_id: str) -> bool:
    now = time.time()
    if chat_id in last_change_time:
        return now - last_change_time[chat_id] < CHANGE_COOLDOWN
    return False

# Utility function for frequency update logic
async def update_frequency(chat_id: str, new_frequency: int):
    return await user_totals_collection.find_one_and_update(
        {'chat_id': chat_id},
        {'$set': {'message_frequency': new_frequency}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

# Command to change frequency for normal admins
async def change_time(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    try:
        member = await chat.get_member(user.id)
        if member.status not in ('administrator', 'creator'):
            await update.message.reply_text('🚫 <b>Access Denied:</b> You do not have permission to use this command.', parse_mode=ParseMode.HTML)
            return

        if is_cooldown_active(chat_id):
            await update.message.reply_text('⏳ <b>Cooldown Active:</b> Please wait before changing the frequency again.', parse_mode=ParseMode.HTML)
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('❌ <b>Incorrect Format:</b> Please use: /changetime <code>[NUMBER]</code>', parse_mode=ParseMode.HTML)
            return

        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text('❌ <b>Invalid Input:</b> Please provide a valid number.', parse_mode=ParseMode.HTML)
            return

        if new_frequency < MIN_FREQUENCY:
            await update.message.reply_text(f'⚠️ <b>Too Low:</b> Frequency must be greater than or equal to <code>{MIN_FREQUENCY}</code>.', parse_mode=ParseMode.HTML)
            return
        if new_frequency > MAX_FREQUENCY:
            await update.message.reply_text(f'⚠️ <b>Too High:</b> Frequency cannot exceed <code>{MAX_FREQUENCY}</code>. How about we keep it reasonable? 🤔', parse_mode=ParseMode.HTML)
            return

        chat_frequency = await update_frequency(chat_id, new_frequency)
        if chat_frequency:
            last_change_time[chat_id] = time.time()  # Update cooldown
            await update.message.reply_text(f'✅ <b>Success!</b> Character spawn rate changed to every <code>{new_frequency}</code> messages! 🎉', parse_mode=ParseMode.HTML)

            # Log the change
            await send_log_message(
                f"📝 <b>Admin Action:</b>\n\n"
                f"👤 <b>Admin:</b> {user.mention_html()}\n"
                f"🏠 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"🔄 <b>Frequency Changed:</b> Every <code>{new_frequency}</code> messages\n"
                f"📅 <b>Date & Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🎉 <i>Character spawn rate updated successfully!</i>",
            )
        else:
            await update.message.reply_text('❌ <b>Failed:</b> Could not update the spawn rate. Please try again later.', parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error changing frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ <b>Error:</b> An unexpected error occurred. Please try again later.', parse_mode=ParseMode.HTML)

# Command to change frequency for sudo users and log the change
async def change_time_sudo(update: Update, context: CallbackContext) -> None:
    sudo_user_ids = {6402009857, 5158013355, 7334126640}  # Define the list of sudo user IDs
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    try:
        if user.id not in sudo_user_ids:
            await update.message.reply_text('🚫 <b>Access Denied:</b> You do not have permission to use this command.', parse_mode=ParseMode.HTML)
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('❌ <b>Incorrect Format:</b> Please use: /ctime <code>[NUMBER]</code>', parse_mode=ParseMode.HTML)
            return

        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text('❌ <b>Invalid Input:</b> Please provide a valid number.', parse_mode=ParseMode.HTML)
            return

        if new_frequency < MIN_FREQUENCY:
            await update.message.reply_text(f'⚠️ <b>Too Low:</b> Frequency must be greater than or equal to <code>{MIN_FREQUENCY}</code>.', parse_mode=ParseMode.HTML)
            return
        if new_frequency > MAX_FREQUENCY:
            await update.message.reply_text(f'⚠️ <b>Too High:</b> Frequency cannot exceed <code>{MAX_FREQUENCY}</code>. Let’s not go overboard! 😅', parse_mode=ParseMode.HTML)
            return

        chat_frequency = await update_frequency(chat_id, new_frequency)
        if chat_frequency:
            await update.message.reply_text(f'✅ <b>Success!</b> Sudo: Character spawn rate changed to every <code>{new_frequency}</code> messages! 🔥', parse_mode=ParseMode.HTML)

            # Send a log message to the logs group
            await send_log_message(
                f"🔥 <b>Sudo Action:</b>\n\n"
                f"👑 <b>Sudo User:</b> {user.mention_html()}\n"
                f"🏠 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"🔧 <b>Frequency Changed:</b> Every <code>{new_frequency}</code> messages\n"
                f"📅 <b>Date & Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🚀 <i>Sudo user successfully updated the spawn rate!</i>"
            )
        else:
            await update.message.reply_text('❌ <b>Failed:</b> Could not update the spawn rate. Please try again later.', parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error changing sudo frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ <b>Error:</b> An unexpected error occurred. Please try again later.', parse_mode=ParseMode.HTML)

# Register command handlers
application.add_handler(CommandHandler("ctime", change_time_sudo, block=False))
application.add_handler(CommandHandler("changetime", change_time, block=False))
