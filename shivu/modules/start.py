import asyncio
import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CommandHandler

from shivu import application, GROUP_ID, user_collection

# Define your sudo users' IDs here
sudo_user_ids = [6402009857]  # Replace with actual user IDs of the sudo users

async def notify_sudo_users(application: Application):
    """Notify sudo users that the bot has restarted."""
    message = "The bot has restarted successfully!"
    for user_id in sudo_user_ids:
        try:
            await application.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Failed to send restart notification to user {user_id}: {e}")

# Function to escape MarkdownV2 characters
def escape_markdown(text: str) -> str:
    """Escape characters in MarkdownV2."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Define the start function
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    args = context.args
    referring_user_id = None

    if args and args[0].startswith('r_'):
        referring_user_id = int(args[0][2:])

    user_data = await user_collection.find_one({"id": user_id})

    if user_data is None:
        new_user = {
            "id": user_id,
            "first_name": first_name,
            "username": username,
            "tokens": 500,
            "characters": []
        }
        await user_collection.insert_one(new_user)

        # Handle referral
        if referring_user_id:
            referring_user_data = await user_collection.find_one({"id": referring_user_id})
            if referring_user_data:
                await user_collection.update_one({"id": referring_user_id}, {"$inc": {"tokens": 1000}})
                referrer_message = f"{first_name} referred you and you got 1000 tokens!"
                try:
                    await context.bot.send_message(chat_id=referring_user_id, text=referrer_message)
                except Exception as e:
                    print(f"Failed to send referral message: {e}")

        # Notify the group about the new user
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🎉 #**New User Alert!** 🎉\n\n"
                 f"👤 User: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
            parse_mode='HTML'
        )
    else:
        # Update user data if necessary
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"first_name": first_name, "username": username}}
            )

    if update.effective_chat.type == "private":
        caption = escape_markdown(
            f"""❖ Kᴏɴ'ɴɪᴄʜɪᴡᴀ {first_name} sᴀɴ 💌!!

๏ I'ᴍ [ᴄʜᴀʀᴀᴄᴛᴇʀ sᴇɪᴢᴇʀ ʙᴏᴛ](https://t.me/Character_seize_bot) ʏᴏᴜʀ ғʀɪᴇɴᴅʟʏ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ☄.

━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━
❖ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ sᴘᴀᴡɴ ᴀ ɴᴇᴡ ᴡᴀɪғᴜ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀғᴛᴇʀ ᴇᴠᴇʀʏ 100 ᴍᴇssᴀɢᴇs ʙʏ ᴅᴇғᴀᴜʟᴛ.
❖ ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ᴛʜᴇ sᴘᴀᴡɴ ʀᴀᴛᴇ ᴀɴᴅ ᴏᴛʜᴇʀ sᴇᴛᴛɪɴɢs ᴛᴏ ʏᴏᴜʀ ʟɪᴋɪɴɢ.
━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━
❖ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ:
 sɪᴍᴘʟʏ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.
━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━"""
        )

        keyboard = [
            [InlineKeyboardButton("❖ Λᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ❖", url='https://t.me/Character_seize_bot?startgroup=new')],
            [InlineKeyboardButton("˹ 𝙎𝙪𝙥𝙥𝙤𝙧𝙩 ˼", url='https://t.me/dynamic_gangs'),
             InlineKeyboardButton("˹ 𝙐𝙥𝙙𝙖𝙩𝙚𝙨 ˼", url='https://t.me/Seizer_updates')],
            [InlineKeyboardButton("˹ 𝙁𝘼𝙌 ˼", url='https://telegra.ph/Seizer-Faq-Menu-09-05')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/40254b3883dfcaec52120.mp4"
        sticker_url = "CAACAgUAAxkBAAEBeVpm-jtB-lkO8Oixy5SZHTAy1Ymp4QACEgwAAv75EFbYc5vQ3hQ1Ph4E"
        
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_url)
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption, reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        keyboard = [
            [InlineKeyboardButton("PM", url='https://t.me/Character_seize_bot?start=true')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/0b2e8e33d07a0d0e5914f.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=f"𝙃𝙚𝙮 𝙩𝙝𝙚𝙧𝙚! {first_name}\n\n✨𝙄 𝘼𝙈 𝘼𝙡𝙞𝙫𝙚 𝘽𝙖𝙗𝙮", reply_markup=reply_markup)

# Register the /start command handler
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)

# Run the application and notify sudo users asynchronously
async def main():
    await application.initialize()
    await application.start()
    asyncio.create_task(notify_sudo_users(application))
    await application.updater.start_polling()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
