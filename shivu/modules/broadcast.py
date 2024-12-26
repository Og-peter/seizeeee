from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, top_global_groups_collection, SPECIALGRADE
from shivu.modules.start import collection as pm_users
import asyncio

async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is authorized
    if user_id not in SPECIALGRADE:
        await update.message.reply_text("Access Denied!")
        return

    # Check for valid arguments
    if not context.args:
        await update.message.reply_text("Usage: /broadcast -chat|-user|-all")
        return

    target = context.args[0]
    if target not in ["-chat", "-user", "-all"]:
        await update.message.reply_text("Invalid target specified. Use -chat, -user, or -all.")
        return

    # Ensure a message is replied to for broadcasting
    message_to_broadcast = update.message.reply_to_message
    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    try:
        # Fetch all groups and users from the database
        all_chats = await top_global_groups_collection.distinct("group_id")
        all_users = await pm_users.distinct("_id")

        # Debugging: Log fetched data
        print(f"All Chats: {all_chats}")
        print(f"All Users: {all_users}")
    except Exception as e:
        await update.message.reply_text("Failed to fetch targets. Please try again later.")
        print(f"Error fetching data: {e}")
        return

    # Determine targets based on the argument
    if target == "-chat":
        targets = all_chats
    elif target == "-user":
        targets = all_users
    elif target == "-all":
        targets = list(set(all_chats + all_users))

    # Debugging: Log the targets
    print(f"Targets for broadcasting: {targets}")

    # If no targets, inform the user
    if not targets:
        await update.message.reply_text("No valid targets found for broadcasting.")
        return

    # Initialize counters
    failed_sends = 0
    success = 0

    # Inform the user that broadcasting is starting
    status_message = await update.message.reply_text("Broadcasting... Please wait.")

    # Loop through each target and broadcast the message
    for chat_id in targets:
        try:
            await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id
            )
            success += 1
        except Exception as e:
            failed_sends += 1
            print(f"Failed to send to {chat_id}: {e}")

        # Add delay to prevent hitting rate limits
        await asyncio.sleep(0.1)

    # Update the user with the broadcast results
    await status_message.edit_text(
        f"Broadcast completed.\nSucceed: {success}\nFailed: {failed_sends}"
    )

# Add the handler to the application
application.add_handler(CommandHandler("broadcast", broadcast, block=False))
