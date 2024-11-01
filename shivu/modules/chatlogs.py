import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from shivu import user_collection, shivuu as app, LEAVELOGS, JOINLOGS

# Welcome messages with styled text and emojis
WELCOME_MESSAGES = [
    "🎉✨ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲, {user}! ✨ Thrilled to have you here!",
    "😊 𝗛𝗲𝗹𝗹𝗼, {user}! Happy to see you! 🎈",
    "🚀 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗮𝗯𝗼𝗮𝗿𝗱, {user}! Let’s make magic! 🌟",
    "🌼 𝗪𝗲𝗹𝗰𝗼𝗺𝗲, {user}! We’re glad you joined! 🌈"
]

# Fun facts or quotes for messages
FACTS_QUOTES = [
    "🔍 𝗗𝗶𝗱 𝘆𝗼𝘂 𝗸𝗻𝗼𝘄? The Eiffel Tower grows 15 cm in summer!",
    "✨ “𝗧𝗵𝗲 𝗳𝘂𝘁𝘂𝗿𝗲 𝗶𝘀 𝗯𝗮𝘀𝗲𝗱 𝗼𝗻 𝘁𝗼𝗱𝗮𝘆.” – 𝗢𝗿𝗲𝘀𝘁𝗲𝘀",
    "🍯 𝗙𝘂𝗻 𝗳𝗮𝗰𝘁: Honey never spoils, even after 3000 years!"
]

# Group rules message
RULES = (
    "🚨 **𝗚𝗿𝗼𝘂𝗽 𝗥𝘂𝗹𝗲𝘀** 🚨\n\n"
    "1️⃣ Be respectful at all times.\n"
    "2️⃣ No spamming or self-promotion.\n"
    "3️⃣ Stay on topic.\n"
    "4️⃣ Follow Telegram's terms.\n\n"
    "🚫 Violation may result in removal."
)

# Template for custom welcome messages
WELCOME_TEMPLATE = """
╭─────────★
🌟 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 🌟
╰─────────★

👤 **Name:** {name}
🆔 **ID:** `{user_id}`
🔗 **Username:** @{username}
👥 **Total Members:** {total_members}

🔰 Enjoy your stay and feel free to interact with our community!
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
        # Custom welcome message using the template
        name = user.first_name
        user_id = user.id
        username = user.username if user.username else "No Username"

        welcome_text = WELCOME_TEMPLATE.format(
            name=name,
            user_id=user_id,
            username=username,
            total_members=total_members
        )

        # Inline keyboard buttons for the welcome message
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("❖ ᴠɪєᴡ ᴍєϻʙєʀ ❖", url=f"tg://user?id={user_id}")],
                [InlineKeyboardButton("✜ ᴧᴅᴅ ϻє ɪη ʏσυʀ ɢʀσυᴘ ✜", url="https://t.me/Character_seize_bot?startgroup=new")]
            ]
        )

        # Welcome photo URL
        welcome_photo_url = "https://files.catbox.moe/h8hiod.jpg"
        
        # Send welcome message with photo and buttons
        await send_photo_message(message.chat.id, welcome_text, welcome_photo_url)
        
        # Fun fact after welcome message
        fun_fact = random.choice(FACTS_QUOTES)
        await app.send_message(message.chat.id, text=fun_fact)
        
        # Send group rules after a delay
        await asyncio.sleep(5)
        await app.send_message(message.chat.id, text=RULES)

        # Log the bot being added to a new group, if applicable
        if user.id == (await client.get_me()).id:
            added_by = message.from_user
            join_text = (
                f"✨ 𝗕𝗼𝘁 𝗔𝗱𝗱𝗲𝗱 𝗶𝗻 𝗮 𝗡𝗲𝘄 𝗚𝗿𝗼𝘂𝗽 ✨\n\n"
                f"🏠 **Group**: {message.chat.title}\n"
                f"🆔 **Chat ID**: {message.chat.id}\n"
                f"👥 **Members**: {total_members}\n"
                f"🔗 **Link**: @{message.chat.username or 'none'}\n"
                f"👤 **Added by**: {added_by.mention}"
            )
            join_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
            await send_photo_message(JOINLOGS, join_text, join_photo_url)

# Helper function to send a photo with a message
async def send_photo_message(chat_id: int, message: str, photo_url: str, reply_markup=None):
    await app.send_photo(chat_id=chat_id, photo=photo_url, caption=message, reply_markup=reply_markup)
