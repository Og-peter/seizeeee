from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, top_global_groups_collection, SPECIALGRADE
from shivu.modules.start import collection as pm_users
import asyncio

async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Debugging user_id and SPECIALGRADE
    if user_id not in SPECIALGRADE:
        await update.message.reply_text(
            f"Access Denied! Your user ID: {user_id}. "
            f"Authorized users: {SPECIALGRADE}"
        )
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast -chat|-user|-all")
        return

    target = context.args[0]
    if target not in ["-chat", "-user", "-all"]:
        await update.message.reply_text("Invalid target specified. Use -chat, -user, or -all.")
        return

    message_to_broadcast = update.message.reply_to_message
    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    try:
        all_chats = await top_global_groups_collection.distinct("group_id")
        all_users = await pm_users.distinct("_id")
    except Exception as e:
        await update.message.reply_text("Failed to fetch targets. Please try again later.")
        return

    if target == "-chat":
        targets = all_chats
    elif target == "-user":
        targets = all_users
    elif target == "-all":
        targets = list(set(all_chats + all_users))

    failed_sends = 0
    success = 0
    status_message = await update.message.reply_text("Broadcasting... Please wait.")

    for chat_id in targets:
        try:
            await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id
            )
            success += 1
        except Exception:
            failed_sends += 1

        await asyncio.sleep(0.1)

    await status_message.edit_text(f"Broadcast completed.\nSucceed: {success}\nFailed: {failed_sends}")

application.add_handler(CommandHandler("broadcast", broadcast, block=False))
