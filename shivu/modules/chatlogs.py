import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from shivu import user_collection, shivuu as app, LEAVELOGS, JOINLOGS

# Predefined welcome messages
WELCOME_MESSAGES = [
    "Welcome to the group, {user}! 🎉",
    "Hello {user}, glad to have you here! 😊",
    "Hey {user}, welcome aboard! 🚀",
    "Hi {user}, let's make this group even better! 🌟"
]

# Predefined farewell messages
FAREWELL_MESSAGES = [
    "Goodbye {user}, we'll miss you! 😢",
    "Take care, {user}. Hope to see you soon! 👋",
    "Farewell {user}, wish you all the best! 🌟"
]

# Predefined fun facts or quotes
FACTS_QUOTES = [
    "Did you know? The Eiffel Tower can be 15 cm taller during the summer.",
    "“The only limit to our realization of tomorrow is our doubts of today.” – Franklin D. Roosevelt",
    "Fun fact: Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible!"
]

# Reminder message for rules or announcements
RULES = (
    "🚨 **Group Rules** 🚨\n\n"
    "1. Be respectful to everyone.\n"
    "2. No spamming or self-promotion.\n"
    "3. Stick to the group's topic.\n"
    "4. Follow Telegram's terms of service.\n\n"
    "Failure to comply will result in removal."
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
        leave_note = "Sorry, this group has fewer than 15 members. I'm leaving... 🍂"
        leave_photo_url = "https://telegra.ph/file/4d1b9889c4dd3316c945d.jpg"
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
                    [InlineKeyboardButton("👤 Join Support", url="https://t.me/dynamic_gangs")]
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
                    f"❖ Waifu Bot Added In A #ɴᴇᴡ_ɢʀᴏᴜᴘ ❖\n\n"
                    f"● Chat Name ➥: {chat_title}\n"
                    f"● Chat Id ➥ : {chat_id}\n"
                    f"● Chat Members ➥: {total_members}\n"
                    f"● Chat Link ➥: {chat_username}\n"
                    f"❖ Added By ➥: {added_by.mention}"
                )
                join_photo_url = "https://telegra.ph/file/4d1b9889c4dd3316c945d.jpg"
                await send_photo_message(JOINLOGS, join_text, join_photo_url)

                # Thanks message for the user who added the bot
                thanks_message = (
                    f"ᴀʀɪɢᴀᴛᴏ sᴇɴᴘᴀɪ [{added_by.mention}](tg://user?id={added_by.id}) ᴛʜᴀɴᴋ𝐬 ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ "
                    f"{chat_title}....🫧💫\n\n"
                    f"🍂..ᴛʜᴀɴᴋ ʏᴏᴜ....🍃"
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
            f"⦾ 𝐋𝐄𝐅𝐓 𝐆𝐑𝐎𝐔𝐏🍂\n\n"
            f"⋟ Cʜᴀᴛ Tɪᴛʟᴇ: {chat_title}\n"
            f"⋟ Cʜᴀᴛ ID: {chat_id}\n"
            f"⋟ Mᴇᴍʙᴇʀs: {total_members}\n"
            f"⋟ Cʜᴀᴛᴜɴᴀᴍᴇ: {chat_username}\n"
            f"⋟ Rᴇᴍᴏᴠᴇᴅ ʙʏ: {removed_by}"
        )
        leave_photo_url = "https://telegra.ph/file/4d1b9889c4dd3316c945d.jpg"
        await send_photo_message(LEAVELOGS, leave_text, leave_photo_url)

SPAM_WORDS = ["spamword1", "spamword2", "example.com"]

@app.on_message(filters.text)
async def spam_filter(client: Client, message: Message):
    if any(word in message.text.lower() for word in SPAM_WORDS):
        await message.delete()
        await message.reply(f"Spam detected and removed! Watch your behavior, {message.from_user.mention}.")
        
# Periodic reminders for group rules
async def schedule_reminders():
    while True:
        await asyncio.sleep(3600)  # Remind every hour
        chat_id = -1002104939708  # Replace with your group chat ID
        await app.send_message(chat_id=chat_id, text=RULES)

# Start the bot and schedule tasks
async def start_bot():
    await app.start()
    asyncio.create_task(schedule_reminders())
    print("Bot is running!")
    await app.idle()
