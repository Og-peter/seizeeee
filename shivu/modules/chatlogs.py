import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from shivu import shivuu as app, LEAVELOGS, JOINLOGS

# Templates for messages
WELCOME_TEMPLATE = """
❀ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ {chat_title} ɢʀᴏᴜᴘ ❀

๏ ɴᴀᴍᴇ ➛ {user_mention}
๏ ɪᴅ ➛ `{user_id}`
๏ ᴜsᴇʀɴᴀᴍᴇ ➛ @{user_username}
๏ ᴍᴀᴅᴇ ʙʏ ➛ [ᴅʏɴᴀᴍɪᴄ sᴜᴘᴘᴏʀᴛ](https://t.me/dynamic_supports)
"""

JOIN_TEXT_TEMPLATE = """
⬤ ʙᴏᴛ ᴀᴅᴅᴇᴅ ɪɴ ᴀ #ɴᴇᴡ_ɢʀᴏᴜᴘ

● ɢʀᴏᴜᴘ ɴᴀᴍᴇ ➠ {chat_title}
● ɢʀᴏᴜᴘ ɪᴅ ➠ `{chat_id}`
● ɢʀᴏᴜᴘ ᴜsᴇʀɴᴀᴍᴇ ➠ @{chat_username}
● ɢʀᴏᴜᴘ ʟɪɴᴋ ➠ {chat_link}
● ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ➠ {total_members}
⬤ ᴀᴅᴅᴇᴅ ʙʏ ➠ {added_by_mention}
"""

# Function to download images
async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return BytesIO(await response.read())
    return None

# Overlay welcome text on user profile image
async def generate_welcome_image(user_photo_url, user_name):
    base_image = Image.open(await download_image(user_photo_url)).convert("RGBA")
    overlay = Image.new("RGBA", base_image.size, (255, 255, 255, 0))

    draw = ImageDraw.Draw(overlay)
    font_size = int(base_image.size[0] * 0.1)
    font = ImageFont.truetype("arial.ttf", font_size)

    text = f"Welcome, {user_name}!"
    text_width, text_height = draw.textsize(text, font=font)
    text_position = ((base_image.size[0] - text_width) // 2, base_image.size[1] - text_height - 10)

    draw.text(text_position, text, fill="white", font=font)

    combined = Image.alpha_composite(base_image, overlay)
    output = BytesIO()
    combined.save(output, format="PNG")
    output.seek(0)
    return output

# Function to send group profile image with join text
async def send_group_profile_image(client, chat, join_text):
    group_photo = await client.get_chat(chat.id)
    if group_photo.photo:
        file_id = group_photo.photo.big_file_id
        file = await client.download_media(file_id)
        await client.send_photo(
            chat_id=JOINLOGS,
            photo=file,
            caption=join_text
        )
        os.remove(file)
    else:
        await client.send_message(JOINLOGS, text=join_text)

# Advanced handler for new chat members
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    total_members = await client.get_chat_members_count(message.chat.id)

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

        # Get user profile photo
        user_info = await app.get_users(user_id)
        profile_photo = user_info.photo
        user_photo_url = photos[0].file_id if photos else None

        if user_photo_url:
            user_photo_bytes = await generate_welcome_image(user_photo_url, name)
            await app.send_photo(
                chat_id=message.chat.id,
                photo=user_photo_bytes,
                caption=WELCOME_TEMPLATE.format(
                    chat_title=message.chat.title,
                    user_mention=user.mention,
                    user_id=user_id,
                    user_username=username
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("✜ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ✜", url="https://t.me/Seize_Characters_Bot?startgroup=new")]]
                )
            )
        else:
            await app.send_message(
                chat_id=message.chat.id,
                text=WELCOME_TEMPLATE.format(
                    chat_title=message.chat.title,
                    user_mention=user.mention,
                    user_id=user_id,
                    user_username=username
                )
            )

    if (await client.get_me()).id in [user.id for user in message.new_chat_members]:
        added_by = message.from_user
        join_text = JOIN_TEXT_TEMPLATE.format(
            chat_title=message.chat.title,
            chat_id=message.chat.id,
            chat_username=message.chat.username or "No Username",
            chat_link=f"https://t.me/{message.chat.username}" if message.chat.username else "No Link",
            total_members=total_members,
            added_by_mention=added_by.mention
        )
        await send_group_profile_image(client, message.chat, join_text)

# Helper function to send a photo with a message
async def send_photo_message(chat_id: int, message: str, photo_url: str, reply_markup=None):
    await app.send_photo(chat_id=chat_id, photo=photo_url, caption=message, reply_markup=reply_markup)
