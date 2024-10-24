import logging
import time
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, user_totals_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for frequency limits
MIN_FREQUENCY = 100
MAX_FREQUENCY = 10000
DEFAULT_FREQUENCY = 1000  # Default frequency for resetting
CHANGE_COOLDOWN = 60 * 60  # 1 hour cooldown before another change
BOOST_DURATION = 60 * 30  # 30 minutes for boost
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
        member = await chat.get_member(user.id)
        if member.status not in ('administrator', 'creator'):
            await update.message.reply_text('🚫 You do not have permission to use this command.')
            return

        if is_cooldown_active(chat_id):
            await update.message.reply_text('⏳ Please wait before changing the frequency again.')
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('❌ Incorrect format. Please use: /changetime <NUMBER>')
            return

        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text('❌ Please provide a valid number.')
            return

        if new_frequency < MIN_FREQUENCY:
            await update.message.reply_text(f'⚠️ The message frequency must be greater than or equal to {MIN_FREQUENCY}.')
            return
        if new_frequency > MAX_FREQUENCY:
            await update.message.reply_text(f'⚠️ The frequency cannot exceed {MAX_FREQUENCY}.')
            return

        chat_frequency = await update_frequency(chat_id, new_frequency)
        if chat_frequency:
            last_change_time[chat_id] = time.time()  # Update cooldown
            await update.message.reply_text(f'✅ Character spawn rate changed to every {new_frequency} messages 🎉')

            # Log the change
            await send_log_message(f"📝 Admin {user.mention_html()} changed the frequency in chat {chat_id} to {new_frequency} messages.", parse_mode='HTML')

        else:
            await update.message.reply_text('❌ Failed to update the spawn rate.')

    except Exception as e:
        logger.error(f"Error changing frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ Failed to change character appearance frequency.')

# Command to change frequency for sudo users and log the change
async def change_time_sudo(update: Update, context: CallbackContext) -> None:
    sudo_user_ids = {6402009857, 5158013355, 7334126640}  # Define the list of sudo user IDs
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    try:
        if user.id not in sudo_user_ids:
            await update.message.reply_text('🚫 You do not have permission to use this command.')
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('❌ Incorrect format. Please use: /ctime <NUMBER>')
            return

        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text('❌ Please provide a valid number.')
            return

        if new_frequency < 1:
            await update.message.reply_text('⚠️ The message frequency must be greater than or equal to 1.')
            return
        if new_frequency > MAX_FREQUENCY:
            await update.message.reply_text(f'⚠️ The frequency cannot exceed {MAX_FREQUENCY}.')
            return

        chat_frequency = await update_frequency(chat_id, new_frequency)
        if chat_frequency:
            await update.message.reply_text(f'✅ Sudo: Character spawn rate changed to every {new_frequency} messages 🔥')

            # Send a log message to the logs group
            await send_log_message(f"📝 Sudo user {user.mention_html()} has changed the frequency in chat {chat_id} to {new_frequency} messages.", parse_mode='HTML')
        else:
            await update.message.reply_text('❌ Failed to update the spawn rate.')

    except Exception as e:
        logger.error(f"Error changing sudo frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ Failed to change character appearance frequency.')

# Command to reset the frequency to default
async def reset_frequency(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    chat_id = str(chat.id)

    try:
        chat_frequency = await update_frequency(chat_id, DEFAULT_FREQUENCY)
        if chat_frequency:
            await update.message.reply_text(f'🔄 Frequency reset to default: Every {DEFAULT_FREQUENCY} messages 🌀')
            await send_log_message(f"🔄 Frequency reset to default: Every {DEFAULT_FREQUENCY} messages in chat {chat_id}.")
        else:
            await update.message.reply_text('❌ Failed to reset the spawn rate.')

    except Exception as e:
        logger.error(f"Error resetting frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ Failed to reset the spawn rate.')

# Command to temporarily boost frequency
async def temporary_boost(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    chat_id = str(chat.id)

    try:
        current_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if current_frequency and 'message_frequency' in current_frequency:
            boosted_frequency = max(current_frequency['message_frequency'] // 2, MIN_FREQUENCY)
            chat_frequency = await update_frequency(chat_id, boosted_frequency)
            if chat_frequency:
                await update.message.reply_text(f'⚡ Boost Mode Activated! Frequency reduced to {boosted_frequency} for 30 minutes 🎉')

                # Send a log message to the logs group
                await send_log_message(f"⚡ Boost mode activated in chat {chat_id}. Frequency reduced to {boosted_frequency} for 30 minutes.")

                # Reset frequency after boost duration
                await context.job_queue.run_once(lambda _: update_frequency(chat_id, current_frequency['message_frequency']), BOOST_DURATION)
            else:
                await update.message.reply_text('❌ Failed to activate boost mode.')
        else:
            await update.message.reply_text('ℹ️ No frequency set to boost.')

    except Exception as e:
        logger.error(f"Error boosting frequency for chat {chat_id}: {e}")
        await update.message.reply_text('❌ Failed to activate boost mode.')

# Register command handlers
application.add_handler(CommandHandler("ctime", change_time_sudo, block=False))
application.add_handler(CommandHandler("changetime", change_time, block=False))
application.add_handler(CommandHandler("resettime", reset_frequency, block=False))
application.add_handler(CommandHandler("boosttime", temporary_boost, block=False))
