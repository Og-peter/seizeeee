from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, top_global_groups_collection, user_collection

OWNER_ID = 6835013483


async def broadcast(update: Update, context: CallbackContext) -> None:
    """Broadcast a message based on command arguments."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message
    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    # Extract command arguments
    args = context.args
    if not args:
        await update.message.reply_text(
            "Please specify the broadcast type:\n"
            "`/broadcast -user` for users only\n"
            "`/broadcast -group` for groups only\n"
            "`/broadcast -both` for both users and groups\n"
            "`/broadcast -pin` for groups with pinning",
            parse_mode="Markdown",
        )
        return

    all_groups = await top_global_groups_collection.distinct("group_id")
    all_users = await user_collection.distinct("id")

    # Determine broadcast type
    option = args[0].lower()
    targets = []
    target_type = ""

    if option == "-user":
        targets = all_users
        target_type = "Users"
    elif option == "-group":
        targets = all_groups
        target_type = "Groups"
    elif option == "-both":
        targets = list(set(all_users + all_groups))
        target_type = "Both Users and Groups"
    elif option == "-pin":
        targets = all_groups
        target_type = "Groups (with Pin)"
    else:
        await update.message.reply_text(
            "Invalid option. Use:\n"
            "`/broadcast -user` for users only\n"
            "`/broadcast -group` for groups only\n"
            "`/broadcast -both` for both users and groups\n"
            "`/broadcast -pin` for groups with pinning",
            parse_mode="Markdown",
        )
        return

    # Start broadcasting
    failed_sends = 0
    success_sends = 0

    for target in targets:
        try:
            sent_message = await context.bot.forward_message(
                chat_id=target,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id,
            )
            success_sends += 1

            if option == "-pin":
                try:
                    await context.bot.pin_chat_message(chat_id=target, message_id=sent_message.message_id)
                except Exception as e:
                    print(f"Failed to pin message in {target}: {e}")

        except Exception as e:
            print(f"Failed to send message to {target}: {e}")
            failed_sends += 1

    await update.message.reply_text(
        f"Broadcast complete to {target_type}.\n\n"
        f"✅ Successfully sent to: {success_sends}\n"
        f"❌ Failed to send to: {failed_sends}\n"
        f"Total: {len(targets)}"
    )


# Register the command handler
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
