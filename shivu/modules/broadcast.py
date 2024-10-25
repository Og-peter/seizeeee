from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, top_global_groups_collection, user_collection

async def broadcast(update: Update, context: CallbackContext) -> None:
    OWNER_ID = 6402009857
    
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.", parse_mode='Markdown')
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("📩 Please reply to a message to broadcast.", parse_mode='Markdown')
        return

    # Retrieve distinct group and user IDs
    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await user_collection.distinct("id")

    # Combine and deduplicate the chat and user IDs
    recipients = set(all_chats + all_users)

    failed_sends = 0
    success_count = 0

    # Send the broadcast message
    for chat_id in recipients:
        try:
            await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id
            )
            success_count += 1  # Increment on successful send
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    # Send a summary message
    success_msg = f"✅ Broadcast complete! {success_count} messages sent successfully."
    failed_msg = f"❌ Failed to send to {failed_sends} chats/users." if failed_sends else ""
    
    await update.message.reply_text(f"{success_msg}\n{failed_msg}", parse_mode='Markdown')

# Add the command handler
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
