import logging
import time
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, user_totals_collection
from datetime import datetime

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
        await application.bot.send_message(LOGS_GROUP_CHAT_ID, message)
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
        # Check if user is admin
        member = await chat.get_member(user.id)
        if member.status not in ('administrator', 'creator'):
            await update.message.reply_text(
                '🛑 <b>Access Denied:</b> Only admins have the privilege to perform this action.', parse_mode='HTML'
            )
            return

        # Check for cooldown
        if is_cooldown_active(chat_id):
            await update.message.reply_text(
                '⏱️ <b>Cooldown in Effect:</b> Please wait a moment before trying again.',
                parse_mode='HTML'
            )
            return

        # Argument validation
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                '⚙️ <b>Usage Error:</b> Correct format: /changetime <code>[NUMBER]</code>.',
                parse_mode='HTML'
            )
            return

        # Frequency validation
        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text(
                '🔢 <b>Invalid Input:</b> Please provide a numerical value for the frequency.',
                parse_mode='HTML'
            )
            return

        # Frequency range check
        if new_frequency < MIN_FREQUENCY:
            await update.message.reply_text(
                f'⚠️ <b>Minimum Limit:</b> Frequency cannot be set below <code>{MIN_FREQUENCY}</code> messages.',
                parse_mode='HTML'
            )
            return
        if new_frequency > MAX_FREQUENCY:
            await update.message.reply_text(
                f'⚠️ <b>Maximum Limit:</b> Frequency cannot exceed <code>{MAX_FREQUENCY}</code> messages.',
                parse_mode='HTML'
            )
            return

        # Update frequency and confirm
        chat_frequency = await update_frequency(chat_id, new_frequency)
        if chat_frequency:
            last_change_time[chat_id] = time.time()  # Update cooldown timer
            await update.message.reply_text(
                f'✨ <b>Success!</b>\nCharacter spawn frequency updated to every <code>{new_frequency}</code> messages.',
                parse_mode='HTML'
            )

            # Log admin action
            await send_log_message(
                f"📝 <b>Admin Activity Log:</b>\n\n"
                f"👤 <b>Admin:</b> {user.mention_html()}\n"
                f"📍 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"🔄 <b>Frequency Set To:</b> Every {new_frequency} messages\n"
                f"🕒 <b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🎉 <i>Frequency successfully updated.</i>", 
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                '⚙️ <b>Update Error:</b> Unable to set the new frequency at this time. Please try again later.',
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error changing frequency for chat {chat_id}: {e}")
        await update.message.reply_text(
            '❗<b>Unexpected Error:</b> An error occurred while updating the frequency. Try again soon.',
            parse_mode='HTML'
        )
# Command to reset the frequency to default
async def reset_frequency(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    chat_id = str(chat.id)

    try:
        # Attempt to reset frequency to default
        chat_frequency = await update_frequency(chat_id, DEFAULT_FREQUENCY)
        if chat_frequency:
            await update.message.reply_text(
                f'🔄 <b>Frequency Reset:</b>\nThe character spawn rate has been reset to the default setting of every <code>{DEFAULT_FREQUENCY}</code> messages. 🌟',
                parse_mode='HTML'
            )

            # Send log message
            await send_log_message(
                f"📝 <b>Frequency Reset Log:</b>\n\n"
                f"📍 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"🔄 <b>New Frequency:</b> Reset to default ({DEFAULT_FREQUENCY} messages)\n"
                f"🕒 <b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🛠️ <i>Frequency reset completed successfully.</i>",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                '⚠️ <b>Reset Failed:</b> Could not restore the default frequency. Please try again later.',
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error resetting frequency for chat {chat_id}: {e}")
        await update.message.reply_text(
            '❗<b>Unexpected Error:</b> An error occurred while resetting the frequency. Try again soon.',
            parse_mode='HTML'
        )
# Register command handlers
application.add_handler(CommandHandler("ctime", change_time_sudo, block=False))
application.add_handler(CommandHandler("changetime", change_time, block=False))
application.add_handler(CommandHandler("resettime", reset_frequency, block=False))
