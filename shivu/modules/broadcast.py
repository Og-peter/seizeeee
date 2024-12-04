from telegram import Update, ChatPermissions
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, top_global_groups_collection, user_collection

async def broadcast(update: Update, context: CallbackContext) -> None:
    OWNER_ID = 6835013483

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    # Optional pinning flag
    pin_messages = "pin" in context.args if context.args else False

    # Fetch all group IDs and user IDs
    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await user_collection.distinct("id")
    recipients = list(set(all_chats + all_users))

    total_recipients = len(recipients)
    failed_sends = 0
    successful_sends = 0
    pinned_messages = 0

    # Notify the owner about the start of the broadcast
    await update.message.reply_text(
        f"Broadcast started. Sending message to {total_recipients} chats/users."
    )

    for index, chat_id in enumerate(recipients, start=1):
        try:
            # Forward the message
            forwarded_message = await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id
            )
            successful_sends += 1

            # Pin the message if enabled and permissions allow
            if pin_messages:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ["group", "supergroup"] and chat.permissions and chat.permissions.can_pin_messages:
                    await forwarded_message.pin()
                    pinned_messages += 1

        except Exception as e:
            failed_sends += 1

        # Provide periodic updates at specific intervals
        if index % max(1, total_recipients // 10) == 0 or index == total_recipients:
            await update.message.reply_text(
                f"Progress: {index}/{total_recipients} completed.\n"
                f"Successful: {successful_sends}, Failed: {failed_sends}, Pinned: {pinned_messages}."
            )

    # Final broadcast summary
    await update.message.reply_text(
        f"Broadcast complete.\n"
        f"Successful deliveries: {successful_sends}\n"
        f"Failed deliveries: {failed_sends}\n"
        f"Messages pinned: {pinned_messages}"
    )

# Add the command handler
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
