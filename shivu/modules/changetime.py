import logging
from pymongo import ReturnDocument
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_totals_collection

# Constants for spawn rate limits and default settings
ADMIN_MIN_FREQUENCY = 100  # Minimum spawn rate for admins
ADMIN_MAX_FREQUENCY = 5000  # Maximum spawn rate for admins
SUDO_MIN_FREQUENCY = 1  # Minimum spawn rate for sudo users
SUDO_MAX_FREQUENCY = float('inf')  # Unlimited max for sudo users
DEFAULT_FREQUENCY = 1000  # Default spawn rate

# Sudo user IDs (replace these with actual IDs)
SUDO_USER_IDS = {6402009857, 5158013355, 7334126640, 5421067814, 6835013483}

# Utility function to update spawn rate in the database
async def update_spawn_rate(chat_id: str, new_frequency: int):
    """Update the spawn rate in the database."""
    return await user_totals_collection.find_one_and_update(
        {'chat_id': chat_id},
        {'$set': {'message_frequency': new_frequency}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

# Command handler for changing the spawn rate
async def change_spawn_rate(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    # Determine if the user is a sudo user
    is_sudo = user.id in SUDO_USER_IDS

    # Extract command arguments
    args = context.args
    if not args:
        # Show the current spawn rate if no argument is provided
        current_frequency = await user_totals_collection.find_one(
            {'chat_id': chat_id},
            projection={'message_frequency': 1}
        )
        current_rate = current_frequency['message_frequency'] if current_frequency else DEFAULT_FREQUENCY
        min_rate = SUDO_MIN_FREQUENCY if is_sudo else ADMIN_MIN_FREQUENCY
        max_rate = "Unlimited" if is_sudo else ADMIN_MAX_FREQUENCY
        await update.message.reply_text(
            f"<b>ℹ️ Current Spawn Rate:</b> Every <code>{current_rate}</code> messages.\n"
            f"<b>💡 Allowed Range:</b> <code>{min_rate}</code> to <code>{max_rate}</code> messages.",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )
        return

    # Ensure the user has admin or sudo privileges
    if not is_sudo:
        try:
            member = await chat.get_member(user.id)
            if member.status not in ('administrator', 'creator'):
                await update.message.reply_text(
                    "🚫 <b>Permission Denied:</b> Only administrators can change the spawn rate.",
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=update.message.message_id
                )
                return
        except Exception as e:
            logging.error(f"Error verifying admin status for user {user.id}: {e}")
            await update.message.reply_text(
                "❌ <b>Error:</b> Unable to verify your admin status. Please try again.",
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )
            return

    # Parse and validate the new frequency
    new_frequency = None
    if args[0].lower() == "reset":
        new_frequency = DEFAULT_FREQUENCY
    else:
        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Invalid Input:</b> Please provide a valid number or use <code>/changetime reset</code> to reset.",
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )
            return

        # Determine allowed limits based on user type
        min_frequency = SUDO_MIN_FREQUENCY if is_sudo else ADMIN_MIN_FREQUENCY
        max_frequency = SUDO_MAX_FREQUENCY if is_sudo else ADMIN_MAX_FREQUENCY

        if new_frequency < min_frequency:
            await update.message.reply_text(
                f"⚠️ <b>Invalid Rate:</b> The spawn rate must be at least <code>{min_frequency}</code> messages.",
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )
            return
        if new_frequency > max_frequency:
            await update.message.reply_text(
                f"⚠️ <b>Invalid Rate:</b> The spawn rate cannot exceed <code>{max_frequency}</code> messages."
                + (" (Unlimited for sudo users)" if is_sudo else ""),
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )
            return

    # Update the spawn rate in the database
    try:
        await update_spawn_rate(chat_id, new_frequency)
        message = (
            f"✅ <b>Spawn Rate Updated!</b>\n\n"
            f"💡 <b>New Rate:</b> Every <code>{new_frequency}</code> messages."
        )
        if new_frequency == DEFAULT_FREQUENCY:
            message += "\nℹ️ The spawn rate has been reset to the default."
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Error updating spawn rate for chat {chat_id}: {e}")
        await update.message.reply_text(
            "❌ <b>Error:</b> Failed to update the spawn rate. Please try again later.",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )

# Register the command handler
application.add_handler(CommandHandler("changetime", change_spawn_rate, block=False))
