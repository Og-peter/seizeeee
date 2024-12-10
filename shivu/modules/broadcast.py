from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import application, top_global_groups_collection, user_collection

OWNER_ID = 6835013483


async def broadcast(update: Update, context: CallbackContext) -> None:
    """Initiate broadcast with options for user/group/combined broadcasts."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message
    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_groups = await top_global_groups_collection.distinct("group_id")
    all_users = await user_collection.distinct("id")

    # Store the broadcast data in the context
    context.user_data["broadcast_data"] = {
        "message_id": message_to_broadcast.message_id,
        "chat_id": message_to_broadcast.chat_id,
        "users": all_users,
        "groups": all_groups,
    }

    # Create a keyboard with broadcast options
    keyboard = [
        [
            InlineKeyboardButton("📤 Broadcast to Users", callback_data="broadcast_users"),
            InlineKeyboardButton("📤 Broadcast to Groups", callback_data="broadcast_groups"),
        ],
        [
            InlineKeyboardButton("📤 Broadcast to Both", callback_data="broadcast_both"),
            InlineKeyboardButton("📌 Broadcast + Pin in Groups", callback_data="broadcast_pin"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select a broadcast option:",
        reply_markup=reply_markup,
    )


async def handle_broadcast(update: Update, context: CallbackContext) -> None:
    """Process the broadcast based on the selected option."""
    query = update.callback_query
    await query.answer()

    broadcast_data = context.user_data.get("broadcast_data", {})
    if not broadcast_data:
        await query.edit_message_text("Broadcast data not found. Please try again.")
        return

    # Extract details
    message_id = broadcast_data["message_id"]
    chat_id = broadcast_data["chat_id"]
    users = broadcast_data["users"]
    groups = broadcast_data["groups"]

    # Determine the broadcast type
    option = query.data
    if option == "broadcast_users":
        targets = users
        target_type = "Users"
    elif option == "broadcast_groups":
        targets = groups
        target_type = "Groups"
    elif option == "broadcast_both":
        targets = list(set(users + groups))
        target_type = "Both Users and Groups"
    elif option == "broadcast_pin":
        targets = groups
        target_type = "Groups (with Pin)"
    elif option == "cancel_broadcast":
        await query.edit_message_text("Broadcast cancelled.")
        context.user_data.pop("broadcast_data", None)
        return
    else:
        await query.edit_message_text("Invalid option selected.")
        return

    # Start broadcasting
    failed_sends = 0
    success_sends = 0

    for target in targets:
        try:
            sent_message = await context.bot.forward_message(
                chat_id=target, from_chat_id=chat_id, message_id=message_id
            )
            success_sends += 1

            # Pin the message if required
            if option == "broadcast_pin":
                try:
                    await context.bot.pin_chat_message(chat_id=target, message_id=sent_message.message_id)
                except Exception as e:
                    print(f"Failed to pin message in {target}: {e}")

        except Exception as e:
            print(f"Failed to send message to {target}: {e}")
            failed_sends += 1

    # Send final stats
    await query.edit_message_text(
        f"Broadcast complete to {target_type}.\n\n"
        f"✅ Successfully sent to: {success_sends}\n"
        f"❌ Failed to send to: {failed_sends}\n"
        f"Total: {len(targets)}"
    )
    # Clean up broadcast data
    context.user_data.pop("broadcast_data", None)


# Register handlers
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
application.add_handler(CallbackQueryHandler(handle_broadcast, pattern="^broadcast_.*$"))
