from pyrogram import Client, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime, timedelta
from shivu import application, user_collection
from shivu import shivuu as app

MUST_JOIN = "Seizer_updates"  # Replace with your group/channel username or ID
allowed_group_id = -1002104939708  # Replace with your allowed group ID
COOLDOWN_HOURS = 5  # Cooldown period in hours

# Function to convert seconds into a readable time format
def format_time(seconds):
    duration = timedelta(seconds=seconds)
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{days} days, {hours} hours, and {minutes} minutes"

# Additional functionality for rewarding users who claim
async def claim_reward(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if the command is used in the allowed group
    if chat_id != allowed_group_id:
        return await message.reply_text("⚠️ This is an exclusive command that only works in @dynamic_gangs")

    # Send typing animation to indicate action in progress
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Check if the user has already claimed the bonus recently
    user_data = await user_collection.find_one({'id': user_id}, projection={'eix_suck_claim': 1})
    if user_data and user_data.get('eix_suck_claim'):
        last_claimed_date = user_data.get('eix_suck_claim')
        # Check if 5 hours have passed since the last claim
        if last_claimed_date and datetime.utcnow() - last_claimed_date < timedelta(hours=COOLDOWN_HOURS):
            remaining_time = int((timedelta(hours=COOLDOWN_HOURS) - (datetime.utcnow() - last_claimed_date)).total_seconds())
            time_remaining_str = format_time(remaining_time)
            await message.reply_text(f"🛑 You have already claimed your reward. Come back in {time_remaining_str}! 😉")
            return

    try:
        # Check if the user has joined the MUST_JOIN group/channel
        await app.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        # If not, prompt the user to join
        if MUST_JOIN.isalpha():
            link = "https://t.me/" + MUST_JOIN
        else:
            chat_info = await app.get_chat(MUST_JOIN)
            link = chat_info.invite_link
        try:
            await message.reply_text(
                f"🧐 It looks like you haven't joined our support group yet. Please join to claim your reward!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🚀 Join the Support Group", url=link),
                        ]
                    ]
                )
            )
            return
        except ChatWriteForbidden:
            pass

    # If the user has joined the group, grant the reward
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 7500000}, '$set': {'eix_suck_claim': datetime.utcnow()}}
    )

    # Send an animated sticker to celebrate the reward
    await message.reply_sticker("CAACAgIAAxkBAAIBIGco7pa-tLx0N3s5S-7QxNPrFtl6AALlKwACYwr5Sc3JkOBizG1-HgQ")  # Replace with the actual sticker ID
    await message.reply_html(
        "🎉 <b>Welcome Again, Champion! 😎</b>\n\n"
        "🙌 <b>Sorry for being inactive for soooo long, but here's a special bonus for you! 😪</b>\n\n"
        "💰 <b>Claimed Amount: Ŧ<code>7,500,000</code>.</b>\n\n"
        "🔥 <i>Keep rocking! We'll be here for more surprises!</i> 🎁"
    )

    # Extra animated message
    await context.bot.send_animation(chat_id=chat_id, animation="https://files.catbox.moe/wmltor.mp4")  # Example GIF URL

# Add the command handler
application.add_handler(CommandHandler("bonus", claim_reward, block=False))
