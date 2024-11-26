import logging
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_totals_collection

# Constants for spawn rate limits and default settings
ADMIN_MIN_FREQUENCY = 100  # Minimum spawn rate for admins
ADMIN_MAX_FREQUENCY = 5000  # Maximum spawn rate for admins
SUDO_MIN_FREQUENCY = 1  # Minimum spawn rate for sudo users
SUDO_MAX_FREQUENCY = float('inf')  # Unlimited max for sudo users
DEFAULT_FREQUENCY = 1000  # Default spawn rate

# Sudo user IDs (replace these with actual IDs)
SUDO_USER_IDS = {6402009857, 5158013355, 7334126640, 5421067814}

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
        await update.message.reply_text(f"ℹ️ **Current Spawn Rate**: Every **{current_rate}** messages.")
        return

    # Ensure the user has admin or sudo privileges
    if not is_sudo:
        try:
            member = await chat.get_member(user.id)
            if member.status not in ('administrator', 'creator'):
                await update.message.reply_text("🚫 **Permission Denied**: Only administrators can change the spawn rate.")
                return
        except Exception:
            await update.message.reply_text("❌ **Error**: Unable to verify your admin status. Please try again.")
            return

    # Parse and validate the new frequency
    new_frequency = None
    if args[0].lower() == "reset":
        new_frequency = DEFAULT_FREQUENCY
    else:
        try:
            new_frequency = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ **Invalid Input**: Please provide a valid number or use `/changetime reset` to reset.")
            return

        # Determine allowed limits based on user type
        min_frequency = SUDO_MIN_FREQUENCY if is_sudo else ADMIN_MIN_FREQUENCY
        max_frequency = SUDO_MAX_FREQUENCY if is_sudo else ADMIN_MAX_FREQUENCY

        if new_frequency < min_frequency:
            await update.message.reply_text(f"⚠️ **Invalid Rate**: The spawn rate must be at least `{min_frequency}` messages.")
            return
        if new_frequency > max_frequency:
            await update.message.reply_text(
                f"⚠️ **Invalid Rate**: The spawn rate cannot exceed **{max_frequency}** messages."
                + (" (Unlimited for sudo users)" if is_sudo else "")
            )
            return

    # Update the spawn rate in the database
    try:
        await update_spawn_rate(chat_id, new_frequency)
        message = (
            f"✅ **Spawn Rate Updated!**\n\n"
            f"💡 **New Rate**: Every `{new_frequency}` messages."
        )
        if new_frequency == DEFAULT_FREQUENCY:
            message += "\nℹ️ The spawn rate has been reset to the default."
        await update.message.reply_text(message)
    except Exception as e:
        logging.error(f"Error updating spawn rate for chat {chat_id}: {e}")
        await update.message.reply_text("❌ **Error**: Failed to update the spawn rate. Please try again later.")

# Register the command handler
application.add_handler(CommandHandler("changetime", change_spawn_rate, block=False))
