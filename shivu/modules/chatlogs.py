import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from shivu import shivuu as app, LEAVELOGS, JOINLOGS

# Template for custom welcome messages
WELCOME_TEMPLATE = """
❀ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ {chat_title} ɢʀᴏᴜᴘ ❀

๏ ɴᴀᴍᴇ ➛ {user_mention}
๏ ɪᴅ ➛ `{user_id}`
๏ ᴜsᴇʀɴᴀᴍᴇ ➛ @{user_username}
๏ ᴍᴀᴅᴇ ʙʏ ➛ [ᴅʏɴᴀᴍɪᴄ sᴜᴘᴘᴏʀᴛ](https://t.me/dynamic_supports)
"""

# Bot added in group notification format
JOIN_TEXT_TEMPLATE = """
⬤ ʙᴏᴛ ᴀᴅᴅᴇᴅ ɪɴ ᴀ #ɴᴇᴡ_ɢʀᴏᴜᴘ

● ɢʀᴏᴜᴘ ɴᴀᴍᴇ ➠ {chat_title}
● ɢʀᴏᴜᴘ ɪᴅ ➠ `{chat_id}`
● ɢʀᴏᴜᴘ ᴜsᴇʀɴᴀᴍᴇ ➠ @{chat_username}
● ɢʀᴏᴜᴘ ʟɪɴᴋ ➠ {chat_link}
● ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ➠ {total_members}
⬤ ᴀᴅᴅᴇᴅ ʙʏ ➠ {added_by_mention}
"""

# Handler for new chat members
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    total_members = await client.get_chat_members_count(message.chat.id)

    # Leave if the group has less than 15 members
    if total_members < 15:
        leave_note = "🌿 𝗦𝗼𝗿𝗿𝘆, 𝗹𝗲𝗮𝘃𝗶𝗻𝗴 𝗮𝘀 𝘁𝗵𝗲 𝗴𝗿𝗼𝘂𝗽 𝗵𝗮𝘀 𝗹𝗲𝘀𝘀 𝘁𝗵𝗮𝗻 𝟭𝟱 𝗺𝗲𝗺𝗯𝗲𝗿𝘀. 🌱"
        leave_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
        await send_photo_message(message.chat.id, leave_note, leave_photo_url)
        await client.leave_chat(message.chat.id)
        return

    for user in message.new_chat_members:
        name = user.first_name
        user_id = user.id
        username = user.username if user.username else "No Username"

        welcome_text = WELCOME_TEMPLATE.format(
            chat_title=message.chat.title,
            user_mention=user.mention,
            user_id=user_id,
            user_username=username
        )

        # Inline keyboard buttons for the welcome message
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✜ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ✜", url="https://t.me/Seize_Characters_Bot?startgroup=new")]
            ]
        )

        welcome_photo_url = "https://files.catbox.moe/h8hiod.jpg"

        # Send welcome message with photo and buttons
        await send_photo_message(message.chat.id, welcome_text, welcome_photo_url, buttons)

        # Send notification to the user who added the bot
        if user.id == (await client.get_me()).id:
            added_by = message.from_user
            profile_photos = await app.get_user_photos(added_by.id, limit=1)
            profile_photo = profile_photos[0].file_id if profile_photos else None
            thank_you_message = (
                f"🌟 **Thank You for Adding Me!** 🌟\n\n"
                f"👤 **Name:** {added_by.first_name}\n"
                f"🆔 **ID:** `{added_by.id}`\n"
                f"🌐 I’m thrilled to be a part of the group **{message.chat.title}**!\n\n"
                f"Feel free to explore my features and let me know if I can assist in any way. 💖"
            )

            if profile_photo:
                await app.send_photo(
                    chat_id=added_by.id,
                    photo=profile_photo,
                    caption=thank_you_message
                )
            else:
                await app.send_message(added_by.id, text=thank_you_message)

            # Log the bot being added to a new group
            join_text = JOIN_TEXT_TEMPLATE.format(
                chat_title=message.chat.title,
                chat_id=message.chat.id,
                chat_username=message.chat.username or "No Username",
                chat_link=f"https://t.me/{message.chat.username}" if message.chat.username else "No Link",
                total_members=total_members,
                added_by_mention=added_by.mention
            )
            join_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
            await send_photo_message(JOINLOGS, join_text, join_photo_url)

# Helper function to send a photo with a message
async def send_photo_message(chat_id: int, message: str, photo_url: str, reply_markup=None):
    await app.send_photo(chat_id=chat_id, photo=photo_url, caption=message, reply_markup=reply_markup)
