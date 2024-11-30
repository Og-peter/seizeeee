from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        return await message.reply_text("⚠️ Ara Ara~ This command only works in @dynamic_gangs, Onichan!")

    # Send typing animation
    sent_msg = await message.reply_text("Kawaii~ Let me check your bonus, Onichan! 😘")
    
    # Check if the user has already claimed the bonus recently
    user_data = await user_collection.find_one({'id': user_id}, projection={'eix_suck_claim': 1})
    if user_data and user_data.get('eix_suck_claim'):
        last_claimed_date = user_data.get('eix_suck_claim')
        if last_claimed_date and datetime.utcnow() - last_claimed_date < timedelta(hours=COOLDOWN_HOURS):
            remaining_time = int((timedelta(hours=COOLDOWN_HOURS) - (datetime.utcnow() - last_claimed_date)).total_seconds())
            time_remaining_str = format_time(remaining_time)
            await sent_msg.edit_text(
                f"🛑 Ara Ara~ You’ve already claimed your kawaii bonus, Senpai! 🕒 Come back in {time_remaining_str}. 😘"
            )
            await sent_msg.delete(delay=10)
            return

    try:
        # Check if the user has joined the MUST_JOIN group/channel
        await app.get_chat_member(MUST_JOIN, user_id)
    except UserNotParticipant:
        # Prompt the user to join
        if MUST_JOIN.isalpha():
            link = "https://t.me/" + MUST_JOIN
        else:
            chat_info = await app.get_chat(MUST_JOIN)
            link = chat_info.invite_link
        await sent_msg.edit_text(
            f"🧐 Ara Ara~ It seems you haven’t joined our kawaii support group yet, Senpai! Join now to claim your reward. 🌸",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Join Support Group", url=link)],
                ]
            )
        )
        return

    # Grant the reward
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 7500000}, '$set': {'eix_suck_claim': datetime.utcnow()}}
    )

    # Edit the message to announce the reward
    await sent_msg.edit_text(
        "🎉 Omedetou~ Onichan! 🥳\n\n"
        "💰 You just claimed a mega bonus of Ŧ<code>7,500,000</code>! 🌸\n\n"
        "🔥 Keep being amazing, Senpai! More surprises await! 😘"
    )

    # Cooldown animation message
    anime_msg = await message.reply_text("🌟 Loading kawaii vibes for you, Senpai... 🌟")
    await anime_msg.edit_text("✨ Ara Ara~ Your reward is shining brightly! Keep it up, Onichan! ✨")
    await anime_msg.delete(delay=10)

# Add the command handler
application.add_handler(CommandHandler("bonus", claim_reward, block=False))
