import asyncio
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CommandHandler
from shivu import application, GROUP_ID, user_collection

# Define your sudo users' IDs here
sudo_user_ids = [6402009857]  # Replace with actual user IDs of the sudo users
SUPPORT_GROUP_ID = "@dynamic_gangs"  # Replace with the actual group username or ID
IMAGE_URL = "https://files.catbox.moe/sn06ft.jpg"  # Replace with the actual image URL

async def notify_sudo_users(application: Application):
    """Notify sudo users that the bot has restarted."""
    message = "The bot has restarted successfully!"
    for user_id in sudo_user_ids:
        try:
            await application.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Failed to send restart notification to user {user_id}: {e}")

def escape_markdown(text: str) -> str:
    """Escape characters in MarkdownV2."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    args = context.args
    referring_user_id = None

    try:
        # Check if user has joined the support group
        member_status = await context.bot.get_chat_member(SUPPORT_GROUP_ID, user_id)
        if member_status.status == 'left':
            join_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("๏ Join Support ๏", url=f"https://t.me/{SUPPORT_GROUP_ID.lstrip('@')}")]
            ])
            await update.message.reply_photo(
                photo=IMAGE_URL,
                caption="๏ It appears you haven't joined our Support Group yet. Please join to access my features!",
                reply_markup=join_button
            )
            return
    except Exception as e:
        print(f"Error checking user membership in support group: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return

    # Handle referral if present
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
                await user_collection.update_one({"id": referring_user_id}, {"$inc": {"tokens": 1000}})
                referrer_message = f"{first_name} used your referral link and you've received 1000 tokens!"
                try:
                    await context.bot.send_message(chat_id=referring_user_id, text=referrer_message)
                except Exception as e:
                    print(f"Failed to send referral message: {e}")

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🎉 #**New User Joined!** 🎉\n\n"
                 f"👤 User: <a href='tg://user?id={user_id}'>{first_name}</a>",
            parse_mode='HTML'
        )
    else:
        # Update user info if it has changed
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"first_name": first_name, "username": username}}
            )

    if update.effective_chat.type == "private":
        caption = (
            f"┬── ⋅ ⋅ ───── ᯽ ───── ⋅ ⋅ ──┬\n"
            f" Kᴏɴ'ɴɪᴄʜɪᴡᴀ <a href='tg://user?id={user_id}'>{first_name}</a>!\n"
            f"┴── ⋅ ⋅ ───── ᯽ ───── ⋅ ⋅ ──┴\n\n"
            f"─────────────────────────\n"
            f"│ ᴡєʟᴄσϻє ᴛσ ˹<b>{context.bot.username}</b>˼ ʏᴏᴜʀ ғʀɪᴇɴᴅʟʏ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ☄ │\n"
            f"─────────────────────────\n\n"
            f"╭── ⋅ ⋅ ───── ✩ ───── ⋅ ⋅ ──╮\n"
            f" ❖ ᴡᴀɪғᴜ sᴇɪᴢᴇʀ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ sᴘᴀᴡɴ ᴀ ɴᴇᴡ ᴡᴀɪғᴜ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ ᴀғᴛᴇʀ ᴇᴠᴇʀʏ 100 ᴍᴇssᴀɢᴇs ʙʏ ᴅᴇғᴀᴜʟᴛ.\n"
            f" ❖ ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ᴛʜᴇ sᴘᴀᴡɴ ʀᴀᴛᴇ ᴀɴᴅ ᴏᴛʜᴇʀ sᴇᴛᴛɪɴɢs ᴛᴏ ʏᴏᴜʀ ʟɪᴋɪɴɢ.\n"
            f"╰── ⋅ ⋅ ───── ✩ ───── ⋅ ⋅ ──╯\n\n"
            f"──────────────────────\n"
            f"❖ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ:\n"
            f" sɪᴍᴘʟʏ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
            f"─────────────────────────\n"
           )

        keyboard = [
            [InlineKeyboardButton("Add Me to Your Group ➕", url=f'https://t.me/{context.bot.username}?startgroup=new')],
            [InlineKeyboardButton("Support Group", url=f'https://t.me/{SUPPORT_GROUP_ID.lstrip("@")}'),
             InlineKeyboardButton("Updates Channel", url='https://t.me/Seizer_updates')],
            [InlineKeyboardButton("FAQ", url='https://telegra.ph/Seizer-Faq-Menu-09-05')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/40254b3883dfcaec52120.mp4"
        sticker_url = "CAACAgUAAxkBAAEBeVpm-jtB-lkO8Oixy5SZHTAy1Ymp4QACEgwAAv75EFbYc5vQ3hQ1Ph4E"
        
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_url)
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption, reply_markup=reply_markup, parse_mode='HTML')
    else:
        keyboard = [
            [InlineKeyboardButton("PM me", url=f'https://t.me/{context.bot.username}?start=true')],
            [InlineKeyboardButton("Support Group", url=f'https://t.me/{SUPPORT_GROUP_ID.lstrip("@")}'),
             InlineKeyboardButton("Updates Channel", url='https://t.me/Seizer_updates')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        video_url = "https://telegra.ph/file/0b2e8e33d07a0d0e5914f.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=f"👋 Hi there, <a href='tg://user?id={user_id}'>{first_name}</a>!\n\n✨ I'm online and ready to assist!", reply_markup=reply_markup, parse_mode='HTML')
        
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)

async def main():
    await application.initialize()
    await application.start()
    asyncio.create_task(notify_sudo_users(application))
    await application.updater.start_polling()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
