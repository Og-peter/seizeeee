import time
from datetime import timedelta
from telegram import Update, InputMediaVideo
from telegram.ext import CommandHandler, CallbackContext
from shivu import application

# Store the bot's start time
BOT_START_TIME = time.time()

# Ping Command with Image and Bot Mention
async def ping(update: Update, context: CallbackContext) -> None:
    # Image URL for the ping response
    image_url = "https://files.catbox.moe/7jvh55.jpg"  # Replace with an appropriate image URL
    
    # Start time for latency calculation
    start_time = time.time()
    
    # Sending an initial response with a cute waifu sticker
    await update.message.reply_sticker("CAACAgQAAxkBAAOxZydY5130mqDr6GKX6kucio9IHRQAAlgRAAKLAdBR7L2HepOERFIeBA")  # Replace with your preferred sticker ID
    message = await update.message.reply_text('⏳ Seize is calculating...')

    # End time for latency calculation
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    
    # Edit the message with latency information and the image
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=image_url,
        caption=(
            f'🌸 **@{context.bot.username} Pong!**\n\n'
            f'⏱️ Latency: `{elapsed_time}ms`\n\n'
            f'✨ Fast as ever, just for you, {update.effective_user.mention_html()} 💖'
        ),
        parse_mode="HTML"
    )

# Alive Command with Video, Real Uptime, Bot Mention, and Waifu Features
async def alive(update: Update, context: CallbackContext) -> None:
    # Video URL for the alive response
    video_url = "https://example.com/alive_video.mp4"  # Replace with an appropriate video URL

    # Calculate real uptime
    uptime_seconds = time.time() - BOT_START_TIME
    uptime = str(timedelta(seconds=int(uptime_seconds)))

    # Alive message with unique text, emojis, bot mention, and interactive elements
    alive_message = (
        f"👋 **Hello, Master! I'm @{context.bot.username}** 🌸\n\n"
        "❄️ **Status:** `Fully Operational`\n"
        f"🌋 **Uptime:** `{uptime}`\n"
        f"🥂 **Bot Name:** `@{context.bot.username}`\n"
        "📊 **Version:** `1.0.0`\n\n"
        f"Thanks for keeping me alive, {update.effective_user.mention_html()} 😊💕"
    )

    # Sending the video with the styled alive message
    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=video_url,
        caption=alive_message,
        parse_mode="HTML"
    )

# Adding handlers for ping and alive commands
application.add_handler(CommandHandler("ping", ping))
application.add_handler(CommandHandler("alive", alive))
