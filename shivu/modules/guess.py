from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import application, user_collection

# Replace OWNER_ID with the actual owner's user ID
OWNER_ID = 6402009857

async def transfer(update, context):
    try:
        user_id = update.effective_user.id

        # Check if the user is the owner
        if user_id != OWNER_ID:
            await update.message.reply_text("🚫 You are not authorized to use this command.")
            return

        # Ensure the command has the correct number of arguments
        if len(context.args) != 2:
            await update.message.reply_text("⚠️ Please provide two valid user IDs for the transfer.")
            return

        sender_id = int(context.args[0])
        receiver_id = int(context.args[1])

        # Retrieve sender's and receiver's information
        sender = await user_collection.find_one({"id": sender_id})
        receiver = await user_collection.find_one({"id": receiver_id})

        if not sender:
            await update.message.reply_text(f"❌ Sender with ID {sender_id} not found.")
            return

        if not receiver:
            await update.message.reply_text(f"❌ Receiver with ID {receiver_id} not found.")
            return

        # Collect information about the sender's waifus
        sender_waifus = sender.get("characters", [])
        total_waifus = len(sender_waifus)
        sender_name = sender.get("name", "Unknown")
        rarity_counts = {}

        # Count waifus by rarity
        for waifu in sender_waifus:
            rarity = waifu.get("rarity", "Unknown")
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

        # Create a summary of the sender's waifus
        rarity_summary = "\n".join([f"✨ {rarity}: {count}" for rarity, count in rarity_counts.items()])
        info_message = (
            "┎━─━─━─━─━─━─━─━─━┒\n"
            "🎴 **Sender Information (Old Account)** 🎴\n"
            "┖━─━─━─━─━─━─━─━─━┚\n"
            f"👤 **User ID**: `{sender_id}`\n"
            f"📝 **Name**: `{sender_name}`\n"
            f"🔢 **Total Waifus**: `{total_waifus}`\n"
            "📊 **Rarity Summary**:\n"
            f"{rarity_summary}\n"
            "━━━━━━━༺༻━━━━━━━"
        )

        # Send the summary and ask for confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_transfer|{sender_id}|{receiver_id}"),
                InlineKeyboardButton("❌ Reject", callback_data="reject_transfer"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(info_message, reply_markup=reply_markup, parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text("⚠️ Invalid User IDs provided.")

async def handle_transfer_response(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if "accept_transfer" in data:
        _, sender_id, receiver_id = data.split("|")
        sender_id = int(sender_id)
        receiver_id = int(receiver_id)

        # Double-check if the user is the receiver
        if user_id != receiver_id:
            await query.edit_message_text("🚫 You are not authorized to accept this transfer.")
            return

        # Retrieve sender's and receiver's information
        sender = await user_collection.find_one({"id": sender_id})
        receiver = await user_collection.find_one({"id": receiver_id})

        if not sender or not receiver:
            await query.edit_message_text("❌ Transfer failed: Sender or receiver not found.")
            return

        # Transfer all waifus from sender to receiver
        receiver_waifus = receiver.get("characters", [])
        receiver_waifus.extend(sender.get("characters", []))

        # Update receiver's waifus
        await user_collection.update_one({"id": receiver_id}, {"$set": {"characters": receiver_waifus}})

        # Remove waifus from the sender
        await user_collection.update_one({"id": sender_id}, {"$set": {"characters": []}})

        await query.edit_message_text("✅ Transfer accepted! All waifus have been successfully transferred.")

    elif data == "reject_transfer":
        await query.edit_message_text("❌ Transfer rejected.")

# Register the handlers
application.add_handler(CommandHandler("transfer", transfer))
application.add_handler(CallbackQueryHandler(handle_transfer_response))
