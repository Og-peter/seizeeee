import os
import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes
from shivu import PHOTO_URL, GROUP_ID, sudo_users
from shivu import user_collection, refeer_collection

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    first_name = escape(update.effective_user.first_name)
    username = update.effective_user.username or "Unknown"
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

        if referring_user_id:
            referring_user_data = await user_collection.find_one({"id": referring_user_id})
            if referring_user_data:
                await user_collection.update_one(
                    {"id": referring_user_id},
                    {"$inc": {"tokens": 1000}}
                )
                referrer_message = f"{first_name} referred you and you got 1000 tokens!"
                try:
                    await context.bot.send_message(chat_id=referring_user_id, text=referrer_message)
                except Exception as e:
                    print(f"Failed to send referral message: {e}")

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"We Got New User \n#NEWUSER\n User: <a href='tg://user?id={user_id}'>{first_name}</a>",
            parse_mode='HTML'
        )
    else:
        # Update the user's name or username if changed
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"first_name": first_name, "username": username}}
            )

    # Send a welcome message in private chat
    if update.effective_chat and update.effective_chat.type == "private":
        caption = f"""❖ Kᴏɴ'ɴɪᴄʜɪᴡᴀ {first_name} sᴀɴ 💌 !!

๏ I'ᴍ [ᴄʜᴀʀᴀᴄᴛᴇʀ sᴇɪᴢᴇʀ ʙᴏᴛ](https://t.me/Character_seize_bot) ʏᴏᴜʀ ғʀɪᴇɴᴅʟʏ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ☄.

━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━
❖ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ sᴘᴀᴡɴ ᴀ ɴᴇᴡ ᴡᴀɪғᴜ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀғᴛᴇʀ ᴇᴠᴇʀʏ 100 ᴍᴇssᴀɢᴇs ʙʏ ᴅᴇғᴀᴜʟᴛ.
❖ ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ᴛʜᴇ sᴘᴀᴡɴ ʀᴀᴛᴇ ᴀɴᴅ ᴏᴛʜᴇʀ sᴇᴛᴛɪɴɢs ᴛᴏ ʏᴏᴜʀ ʟɪᴋɪɴɢ.
━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━
❖ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ:
 sɪᴍᴘʟʏ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.
━━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━"""
        
        keyboard = [
            [InlineKeyboardButton("❖ Λᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ❖", url=f'https://t.me/Character_seize_bot?startgroup=new')],
            [InlineKeyboardButton("˹ sᴜᴘᴘᴏʀᴛ ˼", url='https://t.me/dynamic_gangs'),
             InlineKeyboardButton("˹ ᴜᴘᴅᴀᴛᴇ ˼", url='https://t.me/Seizer_updates')],
            [InlineKeyboardButton("˹ ғᴀǫ ˼", url='https://telegra.ph/Seizer-Faq-Menu-09-05')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/40254b3883dfcaec52120.mp4"
        sticker_url = "CAACAgUAAxkBAAEBeVpm-jtB-lkO8Oixy5SZHTAy1Ymp4QACEgwAAv75EFbYc5vQ3hQ1Ph4E"
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_url)
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video_url,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
    else:
        keyboard = [[InlineKeyboardButton("PM", url='https://t.me/Character_seize_bot?start=true')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/0b2e8e33d07a0d0e5914f.mp4"
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video_url,
            caption=f"𝙃𝙚𝙮 𝙩𝙝𝙚𝙧𝙚! {first_name}\n\n✨𝙄 𝘼𝙢 𝘼𝙡𝙞𝙫𝙚 𝘽𝙖𝙗𝙮",
            reply_markup=reply_markup
        )

# Define the function to notify bot restart
async def notify_restart(application: Application) -> None:
    for sudo_user in sudo_users:
        try:
            await application.bot.send_message(chat_id=sudo_user, text="🚀 Bot has restarted successfully!")
        except Exception as e:
            print(f"Failed to notify sudo user {sudo_user}: {e}")

# Create an asynchronous function to start the bot and set up restart notification
async def main():
    # Create the application instance
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Register the /start command handler
    application.add_handler(CommandHandler('start', start))
    
    # Schedule the restart notification to run immediately
    application.job_queue.run_once(lambda context: notify_restart(application), 1)  # Delay by 1 second to ensure bot is ready
    
    # Start the bot
    await application.start()
    await application.idle()  # Keeps the bot running

# Run the bot using asyncio to manage the event loop
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
