from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import collection, application, user_collection

async def show_database(update: Update, context: CallbackContext) -> None:
    # Bot owner ID(s)
    DEV_LIST = [6402009857]

    # Check if the user executing the command is authorized
    if update.effective_user.id not in DEV_LIST:
        await update.message.reply_text("🚫 You are not authorized to use this feature.")
        return

    try:
        # Fetch counts from the database
        total_characters = await collection.count_documents({})
        total_users = await user_collection.count_documents({"type": "user"})
        total_chats = await user_collection.count_documents({"type": "chat"})
        total_waifus = await collection.count_documents({"is_waifu": True})
        total_animes = len(await collection.distinct("anime"))
        total_harems = await user_collection.count_documents({"has_harem": True})

        # Count characters by rarity
        rarities = [
            "⚪️ Common", "🔵 Medium", "👶 Chibi", "🟠 Rare", 
            "🟡 Legendary", "💮 Exclusive", "🫧 Premium", 
            "🔮 Limited Edition", "🌸 Exotic", "🎐 Astral", "💞 Valentine"
        ]
        rarity_counts = {rarity: await collection.count_documents({"rarity": rarity}) for rarity in rarities}

        # Construct the message with a stylish format
        message = (
            "╭───────────✧───────────╮\n"
            "        🌟 **Bot Database Summary** 🌟\n"
            "╰───────────✧───────────╯\n\n"
            f"◈ **👤 Total Characters**: `{total_characters}`\n"
            f"◈ **👥 Total Users**: `{total_users}`\n"
            f"◈ **🍜 Total Chats**: `{total_chats}`\n"
            f"◈ **🍁 Total Waifus**: `{total_waifus}`\n"
            f"◈ **🍃 Total Harems**: `{total_harems}`\n"
            f"◈ **⛩️ Total Animes**: `{total_animes}`\n"
            "────────────✧────────────\n"
            "❄️ **Character Counts by Rarity:**\n"
        )
        for rarity, count in rarity_counts.items():
            message += f"   ├─➤ {rarity}: `{count}`\n"
        message += "────────────✧────────────"

        # Inline keyboard for "Close" button
        keyboard = [[InlineKeyboardButton("❌ Close", callback_data="close_message")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the constructed message with the inline keyboard
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        # Handle unexpected errors
        await update.message.reply_text(f"⚠️ An error occurred:\n`{e}`", parse_mode="Markdown")

# Callback to handle the "Close" button
async def close_message_callback(update: Update, context: CallbackContext) -> None:
    # Remove the message when the "Close" button is clicked
    try:
        await update.callback_query.message.delete()
    except Exception as e:
        await update.callback_query.answer(f"⚠️ Unable to delete the message: {e}", show_alert=True)

# Add the command handler to the application
application.add_handler(CommandHandler("stats", show_database, block=False))
application.add_handler(CallbackQueryHandler(close_message_callback, pattern="^close_message$"))
