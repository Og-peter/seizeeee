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

# Farewell messages
FAREWELL_MESSAGES = [
    "😢 𝗚𝗼𝗼𝗱𝗯𝘆𝗲 {user}, you will be missed!",
    "👋 𝗧𝗮𝗸𝗲 𝗰𝗮𝗿𝗲, {user}. Come back soon!",
    "🌟 𝗙𝗮𝗿𝗲𝘄𝗲𝗹𝗹 {user}, stay awesome!"
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

# Helper function to send a text message
async def send_message(chat_id: int, message: str):
    await app.send_message(chat_id=chat_id, text=message)

# Helper function to send a photo with a message
async def send_photo_message(chat_id: int, message: str, photo_url: str):
    await app.send_photo(chat_id=chat_id, photo=photo_url, caption=message)

# New chat members handler with welcome message, photo, and inline buttons
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    total_members = await client.get_chat_members_count(message.chat.id)
    
    if total_members < 15:
        leave_note = "🌿 𝗦𝗼𝗿𝗿𝘆, 𝗹𝗲𝗮𝘃𝗶𝗻𝗴 𝗮𝘀 𝘁𝗵𝗲 𝗴𝗿𝗼𝘂𝗽 𝗵𝗮𝘀 𝗹𝗲𝘀𝘀 𝘁𝗵𝗮𝗻 𝟭𝟱 𝗺𝗲𝗺𝗯𝗲𝗿𝘀. 🌱"
        leave_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
        await send_photo_message(message.chat.id, leave_note, leave_photo_url)
        await client.leave_chat(message.chat.id)
    else:
        for user in message.new_chat_members:
            welcome_text = random.choice(WELCOME_MESSAGES).format(user=user.mention)
            fun_fact = random.choice(FACTS_QUOTES)
            combined_message = f"{welcome_text}\n\n{fun_fact}"

            # Inline keyboard buttons
            buttons = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🎯 𝗝𝗼𝗶𝗻 𝗦𝘂𝗽𝗽𝗼𝗿𝘁", url="https://t.me/dynamic_gangs")]
                ]
            )
            await app.send_message(message.chat.id, text=combined_message, reply_markup=buttons)

            # Send group rules after 5 seconds delay
            await asyncio.sleep(5)
            await app.send_message(message.chat.id, text=RULES)

            # Log the bot being added to a new group
            if user.id == (await client.get_me()).id:
                added_by = message.from_user
                chat_title = message.chat.title
                chat_id = message.chat.id
                chat_username = f"@{message.chat.username}" if message.chat.username else "@none"
                join_text = (
                    f"✨ 𝗕𝗼𝘁 𝗔𝗱𝗱𝗲𝗱 𝗶𝗻 𝗮 𝗡𝗲𝘄 𝗚𝗿𝗼𝘂𝗽 ✨\n\n"
                    f"🏠 **Group**: {chat_title}\n"
                    f"🆔 **Chat ID**: {chat_id}\n"
                    f"👥 **Members**: {total_members}\n"
                    f"🔗 **Link**: {chat_username}\n"
                    f"👤 **Added by**: {added_by.mention}"
                )
                join_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
                await send_photo_message(JOINLOGS, join_text, join_photo_url)

                # Thanks message for the user who added the bot
                thanks_message = (
                    f"🌸 𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 [{added_by.mention}](tg://user?id={added_by.id}) 𝗳𝗼𝗿 𝗮𝗱𝗱𝗶𝗻𝗴 𝗺𝗲 𝘁𝗼 "
                    f"{chat_title}! 🌸\n\n"
                    f"🍃..𝗦𝘁𝗮𝘆 𝗔𝘄𝗲𝘀𝗼𝗺𝗲....🍂"
                )
                await send_message(added_by.id, thanks_message)

# Handler for when the bot is removed from a chat
@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        removed_by = message.from_user.mention if message.from_user else "@none"
        chat_title = message.chat.title
        chat_id = message.chat.id
        chat_username = f"@{message.chat.username}" if message.chat.username else "@none"
        total_members = await app.get_chat_members_count(chat_id)
        
        leave_text = (
            f"🚫 𝗟𝗲𝗳𝘁 𝗚𝗿𝗼𝘂𝗽 🚫\n\n"
            f"🏠 **Group**: {chat_title}\n"
            f"🆔 **Chat ID**: {chat_id}\n"
            f"👥 **Members**: {total_members}\n"
            f"🔗 **Link**: {chat_username}\n"
            f"👤 **Removed by**: {removed_by}"
        )
        leave_photo_url = "https://i.ibb.co/0B6KsPm/photo-2024-10-25-11-14-35.jpg"
        await send_photo_message(LEAVELOGS, leave_text, leave_photo_url)

# Spam words list
SPAM_WORDS = ["spamword1", "spamword2", "example.com"]

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

# Custom welcome message handler
@app.on_message(filters.new_chat_members)
async def custom_welcome_message(client: Client, message: Message):
    total_members = await client.get_chat_members_count(message.chat.id)
    for user in message.new_chat_members:
        name = user.first_name
        user_id = user.id
        username = user.username if user.username else "No Username"

        welcome_text = WELCOME_TEMPLATE.format(
            name=name,
            user_id=user_id,
            username=username,
            total_members=total_members
        )

        # Inline keyboard buttons
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👤 VIEW NEW MEMBER 👤", url=f"tg://user?id={user_id}")],
                [InlineKeyboardButton("➕ KIDNAP ME ➕", url="https://t.me/example_bot")]
            ]
        )

        # Send welcome message with photo (optional)
        welcome_photo_url = "https://files.catbox.moe/h8hiod.jpg"
        await send_photo_message(message.chat.id, welcome_text, welcome_photo_url, reply_markup=buttons)
        
@app.on_message(filters.text)
async def spam_filter(client: Client, message: Message):
    if any(word in message.text.lower() for word in SPAM_WORDS):
        await message.delete()
        await message.reply(f"🚫 𝗦𝗽𝗮𝗺 𝗱𝗲𝘁𝗲𝗰𝘁𝗲𝗱 𝗮𝗻𝗱 𝗿𝗲𝗺𝗼𝘃𝗲𝗱! Be cautious, {message.from_user.mention}.")
        
# Periodic reminders for group rules with a random fun fact
async def schedule_reminders():
    while True:
        await asyncio.sleep(3600)  # Remind every hour
        chat_id = -1002104939708  # Replace with your group chat ID
        rules_message = f"{RULES}\n\n💡 **Did You Know?** {random.choice(FACTS_QUOTES)}"
        await app.send_message(chat_id=chat_id, text=rules_message)

# Start the bot and schedule tasks
async def start_bot():
    await app.start()
    asyncio.create_task(schedule_reminders())
    print("Bot is running!")
    await app.idle()
