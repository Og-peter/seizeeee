import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import collection, application, user_collection, backup_collection

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# List of authorized developers (bot owners)
DEV_LIST = [
    6402009857, 7004889403, 1135445089, 5158013355,
    5630057244, 1374057577, 6305653111, 5421067814,
    7497950160, 7334126640, 6835013483
]

# Global variables for pagination
PAGE_SIZE = 5  # Number of items to display per page
page_state = {}

# Custom Inline Keyboard options for detailed database stats
STATS_OPTIONS = [
    [
        InlineKeyboardButton("📊 Character Stats", callback_data='char_stats'),
        InlineKeyboardButton("👥 User Stats", callback_data='user_stats')
    ],
    [
        InlineKeyboardButton("🏆 Top Contributors", callback_data='top_contributors'),
        InlineKeyboardButton("🗃 Backup Stats", callback_data='backup_stats')
    ],
]

# Helper function to send animated updates
async def send_animated_progress(update: Update, messages: list, delay: float = 1.5):
    """
    Helper function to send animated progress messages.
    Sends each message one by one with a small delay between them.
    """
    for msg in messages:
        await update.message.reply_text(msg, parse_mode="Markdown")
        await asyncio.sleep(delay)

# Command to show a detailed database summary with buttons
async def show_database(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    logging.info(f"User {user_id} requested the database summary.")

    # Check if the user executing the command is in the authorized DEV_LIST
    if user_id not in DEV_LIST:
        await update.message.reply_text("❌ *You are not authorized to use this feature.*", parse_mode="Markdown")
        logging.warning(f"Unauthorized access attempt by user {user_id}.")
        return

    try:
        # Send initial animated progress message
        await send_animated_progress(update, [
            "🧮 **Connecting to the database...**",
            "🔍 **Fetching available statistics...**"
        ])

        # Present buttons for detailed statistics
        await update.message.reply_text(
            "📊 **Please select which statistics you'd like to see:**",
            reply_markup=InlineKeyboardMarkup(STATS_OPTIONS),
            parse_mode="Markdown"
        )

    except Exception as e:
        # Log any error that occurs during the process
        logging.error(f"Error occurred while fetching database summary: {str(e)}")
        await update.message.reply_text("⚠️ *An error occurred while fetching the database summary. Please try again later.*", parse_mode="Markdown")

# Callback query handler for detailed stats
async def handle_stats_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    try:
        # Handle different types of statistics based on callback data
        if data == 'char_stats':
            await query.message.edit_text("🔄 **Fetching character statistics...**")
            total_characters = await collection.count_documents({})
            rarity_levels = [
                "⚪️ Common", "🔵 Medium", "👶 Chibi", "🟠 Rare", "🟡 Legendary", 
                "💮 Exclusive", "🫧 Premium", "🔮 Limited Edition", 
                "🌸 Exotic", "🎐 Astral", "💞 Valentine"
            ]
            rarity_counts = {}
            for rarity in rarity_levels:
                rarity_counts[rarity] = await collection.count_documents({"rarity": rarity})
            message = f"🎴 **Total Characters**: `{total_characters}`\n\n"
            for rarity, count in rarity_counts.items():
                percentage = (count / total_characters) * 100 if total_characters > 0 else 0
                message += f"{rarity}: `{count}` ({percentage:.2f}%)\n"
            await query.message.edit_text(message, parse_mode="Markdown")

        elif data == 'user_stats':
            await query.message.edit_text("🔄 **Fetching user statistics...**")
            total_users = await user_collection.count_documents({})
            message = f"👥 **Total Users**: `{total_users}`\n"
            await query.message.edit_text(message, parse_mode="Markdown")

        elif data == 'top_contributors':
            await display_top_contributors(update, context, page=1)

        elif data.startswith('next_page') or data.startswith('prev_page'):
            # Handle pagination
            current_page = int(data.split('_')[-1])
            await display_top_contributors(update, context, page=current_page)

        elif data == 'backup_stats':
            await query.message.edit_text("🔄 **Fetching backup statistics...**")
            total_backups = await backup_collection.count_documents({})
            message = f"📁 **Total Backups**: `{total_backups}`\n"
            await query.message.edit_text(message, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error handling stats callback: {str(e)}")
        await query.message.edit_text("⚠️ *An error occurred. Please try again later.*", parse_mode="Markdown")

# Display paginated top contributors
async def display_top_contributors(update: Update, context: CallbackContext, page=1):
    query = update.callback_query

    # Calculate the skip value based on the current page
    skip_value = (page - 1) * PAGE_SIZE

    # Fetch top contributors for the current page
    top_contributors = await collection.aggregate([
        {"$group": {"_id": "$owner_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$skip": skip_value},
        {"$limit": PAGE_SIZE}
    ]).to_list(None)

    message = f"🏆 **Top Contributors - Page {page}**:\n"
    for index, contributor in enumerate(top_contributors):
        user = await user_collection.find_one({"_id": contributor["_id"]})
        user_name = user.get("name", "Unknown User")
        message += f"{index + 1}. 👤 {user_name}: `{contributor['count']}` characters\n"

    # Create pagination buttons
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'prev_page_{page - 1}'))
    if len(top_contributors) == PAGE_SIZE:
        navigation_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f'next_page_{page + 1}'))

    # Show the paginated top contributors with navigation buttons
    await query.message.edit_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([navigation_buttons] if navigation_buttons else None)
    )

# Periodic task to send daily summaries to developers
async def daily_summary():
    while True:
        now = datetime.utcnow()
        next_summary_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_time = (next_summary_time - now).total_seconds()
        await asyncio.sleep(wait_time)

        # Send daily summary to all developers
        try:
            total_characters = await collection.count_documents({})
            total_users = await user_collection.count_documents({})
            total_backups = await backup_collection.count_documents({})

            message = (
                f"📊 **Daily Summary - {datetime.utcnow().strftime('%Y-%m-%d')}**\n\n"
                f"🎴 **Total Characters**: `{total_characters}`\n"
                f"👥 **Total Users**: `{total_users}`\n"
                f"📁 **Total Backups**: `{total_backups}`"
            )

            for dev_id in DEV_LIST:
                try:
                    await application.bot.send_message(chat_id=dev_id, text=message, parse_mode="Markdown")
                except Exception as send_error:
                    logging.error(f"Error sending summary to {dev_id}: {send_error}")

        except Exception as summary_error:
            logging.error(f"Error generating daily summary: {summary_error}")

# Log command usage with timestamps
async def log_command_usage(user_id, command):
    logging.info(f"User {user_id} used the command: {command} at {datetime.now()}")

# Add the handler to the application
application.add_handler(CommandHandler("db", show_database, block=False))
application.add_handler(CallbackQueryHandler(handle_stats_callback))

# Start the bot and schedule daily summaries
async def start_bot():
    await application.start()
    asyncio.create_task(daily_summary())
    logging.info("Bot is running!")
    await application.idle()
