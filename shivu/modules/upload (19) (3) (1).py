import logging
import asyncio
from datetime import datetime, time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, ReplyKeyboardMarkup, KeyboardButton
from pymongo import ReturnDocument
from shivu import user_collection, collection, CHARA_CHANNEL_ID, SUPPORT_CHAT, shivuu as app, sudo_users, db
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import BadRequest

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Define the scheduled message times (in 24-hour format)
GOOD_MORNING_TIME = time(8, 0)  # 8:00 AM
GOOD_NIGHT_TIME = time(22, 0)   # 10:00 PM
NEW_CHARACTER_TIME = time(18, 0)  # 6:00 PM

# Define specific sudo user IDs and channel ID
SUDO_USER_IDS = (6402009857, 7004889403, 1135445089, 5158013355, 5630057244, 
                 1374057577, 6305653111, 5421067814, 7497950160, 7334126640, 
                 6835013483, 1993290981, 1742711103, 6180567980)  # Actual sudo user IDs as integers
CHANNEL_ID = -1002049694247  # Actual channel ID as integer

# Function to send a message to all sudo users
async def send_message_to_sudo_users(app, text):
    for user_id in SUDO_USER_IDS:
        try:
            await app.send_message(user_id, text)
        except Exception as e:
            print(f"Failed to send message to sudo user {user_id}: {e}")

# Function to send a message to a specific channel
async def send_message_to_channel(app, channel_id, text):
    try:
        await app.send_message(channel_id, text)
    except Exception as e:
        print(f"Failed to send message to channel {channel_id}: {e}")

# Notify bot restart to the sudo users
async def notify_restart(app):
    message_text = "🚨 Bot has restarted!"
    await send_message_to_sudo_users(app, message_text)

# Scheduled messaging function
async def scheduled_messages(app):
    while True:
        now = datetime.now().time()
        
        # Good Morning Message
        if now == GOOD_MORNING_TIME:
            await send_message_to_sudo_users(app, "Good morning! ☀️ Have a great day!")

        # Good Night Message
        elif now == GOOD_NIGHT_TIME:
            await send_message_to_sudo_users(app, "Good night! 🌙 Sweet dreams!")

        # New Character Notification
        elif now == NEW_CHARACTER_TIME:
            await send_message_to_channel(app, CHANNEL_ID, "📢 New character coming soon! Please wait a bit longer.")

        # Check every 30 seconds to increase reliability
        await asyncio.sleep(30)
        
# Function to get the next sequence number for unique IDs
async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

# Rarity emojis mapping
rarity_emojis = {
        '⚪️ Common': '⚪️',
        '🔮 Limited Edition': '🔮',
        '🫧 Premium': '🫧',
        '🌸 Exotic': '🌸',
        '💮 Exclusive': '💮',
        '👶 Chibi': '👶',
        '🟡 Legendary': '🟡',
        '🟠 Rare': '🟠',
        '🔵 Medium': '🔵',
        '🎐 Astral': '🎐',
        '💞 Valentine': '💞'
}
event_emojis = {
    '🩺 Nurse': '🩺',
    '🐰 Bunny': '🐰',
    '🧹 Maid': '🧹',
    '🎃 Halloween': '🎃',
    '🎄 Christmas': '🎄',
    '🎩 Tuxedo': '🎩',
    '☃️ Winter': '☃️',
    '👘 Kimono': '👘',
    '🎒 School': '🎒',
    '🥻 Saree': '🥻',
    '🏖️ Summer': '🏖️',
    '🏀 Basketball': '🏀',
    '⚽ Soccer': '⚽'
}
# Dictionary to keep track of user states
user_states = {}


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if str(message.from_user.id) in sudo_users:
        sudo_user = await app.get_users(message.from_user.id)
        sudo_user_first_name = sudo_user.first_name
        await message.reply_text(f"Hello [{sudo_user_first_name}](tg://user?id={message.from_user.id})!", reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("⚙ Admin panel ⚙")]],
            resize_keyboard=True
        ))


@app.on_message(filters.text & filters.private & filters.regex("^⚙ Admin panel ⚙$"))
async def admin_panel(client, message):
    if str(message.from_user.id) in sudo_users:
        total_waifus = await collection.count_documents({})
        total_animes = await collection.distinct("anime")
        total_harems = await user_collection.count_documents({})
        admin_panel_message = (
            f"Admin Panel:\n\n"
            f"Total Waifus: {total_waifus}\n"
            f"Total Animes: {len(total_animes)}\n"
            f"Total Harems: {total_harems}"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🆕 Add Character", callback_data="add_waifu"),
                    InlineKeyboardButton("Add Anime 🆕", callback_data="add_anime")
                ],
                [
                    InlineKeyboardButton("👾 Anime List", switch_inline_query_current_chat="choose_anime ")
                ]
            ]
        )
        await app.send_message(message.chat.id, admin_panel_message, reply_markup=keyboard)
    else:
        await message.reply_text("You are not authorized to use this command.")

# Edit command to include "Edit Event"
@app.on_message(filters.command("edit") & filters.private)
async def edit_waifu_command(client, message):
    try:
        if str(message.from_user.id) in sudo_users:
            if len(message.command) < 2:
                await message.reply_text("Please provide the waifu ID. Usage: /edit <waifu_id>")
                return

            waifu_id = message.command[1]
            waifu = await collection.find_one({"id": waifu_id})
            if waifu:
                await message.reply_photo(
                    photo=waifu["img_url"],
                    caption=f"👧 Name: {waifu['name']}\n🎥 Anime: {waifu['anime']}\n🏷 Rarity: {waifu['rarity']}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("🧩 Rename Character", callback_data=f"rename_waifu_{waifu_id}")],
                            [InlineKeyboardButton("⛱️ Change Image", callback_data=f"change_image_{waifu_id}")],
                            [InlineKeyboardButton("⛩️ Change Rarity", callback_data=f"change_rarity_{waifu_id}")],
                            [InlineKeyboardButton("🎉 Edit Event", callback_data=f"change_event_{waifu_id}")],  # New button
                            [InlineKeyboardButton("📢 Reset Character", callback_data=f"reset_waifu_{waifu_id}")],
                            [InlineKeyboardButton("🗑️ Remove Character", callback_data=f"remove_waifu_{waifu_id}")]
                        ]
                    )
                )
            else:
                await message.reply_text("Waifu not found.")
        else:
            await message.reply_text("You are not authorized to use this command.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@app.on_callback_query(filters.regex('^change_event_'))
async def change_event_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "changing_event", "waifu_id": waifu_id}
    
    # Display event options with only the emoji part in callback_data
    event_buttons = [
        [InlineKeyboardButton(event, callback_data=f"set_new_event_{event_emojis[event]}_{waifu_id}")] 
        for event in event_emojis.keys()
    ]
    event_buttons.append([InlineKeyboardButton("Skip Event", callback_data=f"set_new_event_none_{waifu_id}")])

    await callback_query.message.edit_text(
        "Choose a new event for the waifu (or skip):",
        reply_markup=InlineKeyboardMarkup(event_buttons)
    )

# Set new event for waifu
@app.on_callback_query(filters.regex('^set_new_event_'))
async def set_new_event_callback(client, callback_query):
    try:
        # Ensure callback data has the correct format and split properly
        _, event_emoji, waifu_id = callback_query.data.split('_', 2)

        # Check if "Skip Event" was chosen
        if event_emoji == "none":
            # Clear the event
            updated_waifu = await collection.find_one_and_update(
                {"id": waifu_id},
                {"$set": {"event_emoji": "", "event_name": ""}},
                return_document=ReturnDocument.AFTER
            )
            message_text = f"The event has been cleared for waifu ID '{waifu_id}'."
        else:
            # Find event name based on emoji
            event_name = next((name for name, emoji in event_emojis.items() if emoji == event_emoji), None)
            if event_name:
                # Update the waifu with the new event
                updated_waifu = await collection.find_one_and_update(
                    {"id": waifu_id},
                    {"$set": {"event_emoji": event_emoji, "event_name": event_name}},
                    return_document=ReturnDocument.AFTER
                )
                message_text = f"The event has been updated to '{event_name}' for waifu ID '{waifu_id}'."
            else:
                message_text = "Invalid event selected. Please choose a valid event."

        await callback_query.message.edit_text(message_text)
    except Exception as e:
        await callback_query.message.edit_text("An error occurred while updating the event.")
        print(f"Error in set_new_event_callback: {str(e)}")
        
@app.on_callback_query(filters.regex('^add_waifu$'))
async def add_waifu_callback(client, callback_query):
    await callback_query.message.edit_text(
        "Choose an anime to save the waifu in:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👾 Search Anime", switch_inline_query_current_chat="choose_anime "),
                    InlineKeyboardButton("⚔️ Cancel", callback_data="cancel_add_waifu")
                ]
            ]
        )
    )
    # Initialize user state if not already initialized
    if callback_query.from_user.id not in user_states:
        user_states[callback_query.from_user.id] = {
            "state": "selecting_anime",
            "anime": None,
            "name": None,
            "rarity": None,
            "action": "add",
            "event_emoji": None,
            "event_name": None
        }

@app.on_callback_query(filters.regex('^add_waifu_'))
async def choose_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "awaiting_waifu_name", "anime": selected_anime, "name": None, "rarity": None}

    # Check if message exists before attempting to edit it
    if callback_query.message:
        await callback_query.message.edit_text(
            f"You've selected {selected_anime}. Now, please enter the new waifu's name:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="cancel_add_waifu")]]
            )
        )
    else:
        await callback_query.answer(
            f"You've selected {selected_anime}. Now, please enter the new Character's name.",
            show_alert=True
            )
        
# Handle text input for waifu name and move to rarity selection
@app.on_message(filters.private & filters.text)
async def receive_text_message(client, message):
    user_data = user_states.get(message.from_user.id)
    if user_data and user_data["state"] == "awaiting_waifu_name":
        user_states[message.from_user.id]["name"] = message.text.strip()
        user_states[message.from_user.id]["state"] = "awaiting_waifu_rarity"
        
        # Prompt for rarity selection
        await message.reply_text(
            "Now, choose the waifu's rarity:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(rarity, callback_data=f"select_rarity_{rarity}")] 
                    for rarity in rarity_emojis.keys()
                ]
            )
        )

# Handle rarity selection and move to event selection
@app.on_callback_query(filters.regex('^select_rarity_'))
async def select_rarity_callback(client, callback_query):
    selected_rarity = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id]["rarity"] = selected_rarity
    user_states[callback_query.from_user.id]["state"] = "selecting_event"

    # Prompt for event selection with a "Skip" option
    event_buttons = [
        [InlineKeyboardButton(event, callback_data=f"set_event_{event}")] for event in event_emojis.keys()
    ]
    event_buttons.append([InlineKeyboardButton("Skip Event", callback_data="set_event_none")])
    
    await callback_query.message.edit_text(
        "Choose an event emoji for the waifu (or skip):",
        reply_markup=InlineKeyboardMarkup(event_buttons)
    )

# Handle event selection or skip
@app.on_callback_query(filters.regex('^set_event_'))
async def set_event_callback(client, callback_query):
    event_name = callback_query.data.split('_', 2)[-1]
    if event_name == "none":
        # Skip event by setting it to None
        user_states[callback_query.from_user.id]["event_emoji"] = ""
        user_states[callback_query.from_user.id]["event_name"] = ""
    else:
        user_states[callback_query.from_user.id]["event_emoji"] = event_emojis[event_name]
        user_states[callback_query.from_user.id]["event_name"] = event_name

    user_states[callback_query.from_user.id]["state"] = "awaiting_waifu_image"
    await callback_query.message.edit_text(f"Event '{event_name}' selected. Now, send the character's image.")

# Handle waifu image upload and save waifu details
@app.on_message(filters.private & filters.photo)
async def receive_photo(client, message):
    try:
        user_data = user_states.get(message.from_user.id)
        
        if user_data and user_data["state"] == "awaiting_waifu_image":
            photo_file_id = message.photo.file_id
            waifu_id = str(await get_next_sequence_number('character_id')).zfill(2)
            
            # Build waifu data with rarity, event emoji, and name
            character = {
                'img_url': photo_file_id,
                'name': user_data["name"],
                'anime': user_data["anime"],
                'rarity': user_data["rarity"],
                'id': waifu_id,
                'event_emoji': user_data["event_emoji"] or "",
                'event_name': user_data["event_name"] or ""
            }
            await collection.insert_one(character)
            await message.reply_text("⏳ Adding Character...")

            # Send notification with event emoji and rarity
            caption = (
                f"OwO! Check out this character!\n\n"
                f"<b>{user_data['anime']}</b>\n"
                f"{waifu_id}: {user_data['name']} [{character['event_emoji']}]\n"
                f"(𝙍𝘼𝙍𝙄𝙏𝙔: {user_data['rarity']})\n\n"
                f"{character['event_name']}\n\n"
                f"➼ ᴀᴅᴅᴇᴅ ʙʏ: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
            )
            
            await app.send_photo(chat_id=CHARA_CHANNEL_ID, photo=photo_file_id, caption=caption)
            await app.send_photo(chat_id=SUPPORT_CHAT, photo=photo_file_id, caption=caption)

            await message.reply_text("✅ Character added successfully.")
            user_states.pop(message.from_user.id, None)
        elif user_data["state"] == "changing_image" and user_data["waifu_id"]:
                # This condition handles changing the image of an existing waifu
                waifu_id = user_data["waifu_id"]
                new_image = message.photo.file_id
                waifu = await collection.find_one_and_update(
                    {"id": waifu_id},
                    {"$set": {"img_url": new_image}},
                    return_document=ReturnDocument.AFTER
                )
                if waifu:
                    await message.reply_text("The waifu's image has been changed successfully.")
                    await app.send_photo(
                        chat_id=CHARA_CHANNEL_ID,
                        photo=new_image,
                        caption=f'🖼 ᴜᴘᴅᴀᴛᴇ! ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀꜱ ɢᴏᴛ ᴀ ɴᴇᴡ ʟᴏᴏᴋ! 🖼\n'
                                f'🆔 <b>ID:</b> {waifu_id}\n'
                                f'👤 <b>Name:</b> {waifu["name"]}\n'
                                f'🎌 <b>Anime:</b> {waifu["anime"]}',
                    )
                    await app.send_photo(
                        chat_id=SUPPORT_CHAT,
                        photo=new_image,
                        caption=f'🖼 ᴜᴘᴅᴀᴛᴇ! ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀꜱ ɢᴏᴛ ᴀ ɴᴇᴡ ʟᴏᴏᴋ! 🖼\n'
                                f'🆔 <b>ID:</b> {waifu_id}\n'
                                f'👤 <b>Name:</b> {waifu["name"]}\n'
                                f'🎌 <b>Anime:</b> {waifu["anime"]}',
                    )
                else:
                    await message.reply_text("Failed to change the waifu's image.")
                user_states.pop(message.from_user.id, None)
    except Exception as e:
        await message.reply_text("An error occurred while processing your request.")
        print(f"Error in receive_photo: {str(e)}")

@app.on_inline_query()
async def search_anime(client, inline_query):
    if str(inline_query.from_user.id) not in sudo_users:
        return

    query = inline_query.query.strip().lower()
    if query.startswith("choose_anime "):
        query = query[len("choose_anime "):]
        anime_results = await collection.aggregate([
            {"$match": {"anime": {"$regex": query, "$options": "i"}}},
            {"$group": {"_id": "$anime", "waifu_count": {"$sum": 1}}},
            {"$limit": 10}
        ]).to_list(length=None)
        
        results = []
        for anime in anime_results:
            title = anime["_id"]
            waifu_count = anime["waifu_count"]
            description = f"Characters Count: {waifu_count}"
            message_text = f"✏ Title: {title}\n🏷 Waifus Count: {waifu_count}"
            
            # Ensure callback data is within the 64-byte limit
            title_encoded = title[:30]  # truncate title to ensure total length < 64 bytes
            inline_buttons = [
                [InlineKeyboardButton("Add Character", callback_data=f"add_waifu_{title_encoded}")],
                [InlineKeyboardButton("Rename Anime", callback_data=f"rename_anime_{title_encoded}")],
                [InlineKeyboardButton("Remove Anime", callback_data=f"remove_anime_{title_encoded}")],
                [InlineKeyboardButton("View Characters", callback_data=f"view_characters_{title_encoded}")],  # New button
            ]
            reply_markup = InlineKeyboardMarkup(inline_buttons)
            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description=description,
                    input_message_content=InputTextMessageContent(message_text),
                    reply_markup=reply_markup
                )
            )
        
        await inline_query.answer(results, cache_time=1)

# Callback handler to display the list of characters for a specific anime
@app.on_callback_query(filters.regex('^view_characters_'))
async def view_characters_callback(client, callback_query):
    anime_name = callback_query.data.split('_', 2)[-1]
    waifus = await collection.find({"anime": anime_name}).to_list(length=None)
    
    if waifus:
        # Safely access 'name' and 'rarity' with a default value if they are missing
        character_list = "\n".join([
            f"{waifu.get('name', 'Unknown')} ({waifu.get('rarity', 'Unknown')})" for waifu in waifus
        ])
        await callback_query.message.edit_text(
            f"Characters in '{anime_name}':\n\n{character_list}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_anime_list")]])
        )
    else:
        await callback_query.message.edit_text("No characters found for this anime.")
        
# Back button to return to the anime list
@app.on_callback_query(filters.regex('^back_to_anime_list$'))
async def back_to_anime_list(client, callback_query):
    await callback_query.message.edit_text(
        "Returning to the anime list.",
        reply_markup=None
    )

@app.on_callback_query(filters.regex('^add_anime$'))
async def add_anime_callback(client, callback_query):
    user_id = callback_query.from_user.id
    user_states[user_id] = {"state": "adding_anime"}
    logging.info(f"Set state for user {user_id} to adding_anime")

    # Prompt user for anime name
    await callback_query.message.edit_text(
        "Please enter the name of the anime you want to add:"
    )

@app.on_message(filters.private & filters.text)
async def receive_text_message(client, message):
    user_id = message.from_user.id
    user_data = user_states.get(user_id)
    logging.info(f"Received message from {user_id}: '{message.text}', user_data: {user_data}")

    # Check if user is in the 'adding_anime' state
    if user_data and user_data.get("state") == "adding_anime":
        anime_name = message.text.strip()
        logging.info(f"User {user_id} is adding anime: '{anime_name}'")
        
        try:
            # Check if the anime already exists in the database
            existing_anime = await collection.find_one({"anime": anime_name})
            if existing_anime:
                await message.reply_text(f"The anime '{anime_name}' already exists.")
                logging.info(f"Anime '{anime_name}' already exists for user {user_id}")
            else:
                # Insert the new anime into the collection
                anime_document = {"anime": anime_name}
                result = await collection.insert_one(anime_document)
                
                if result.inserted_id:
                    await message.reply_text(f"The anime '{anime_name}' has been added successfully.")
                    logging.info(f"Anime '{anime_name}' added successfully for user {user_id}")
                else:
                    await message.reply_text("Failed to add the anime due to a database error.")
                    logging.error(f"Failed to add anime '{anime_name}' for user {user_id}")

        except Exception as e:
            logging.error(f"Database error for user {user_id} while adding anime: {e}")
            await message.reply_text("An error occurred while adding the anime. Please try again later.")

        # Clean up user state regardless of outcome
        user_states.pop(user_id, None)

    # Check for waifu name input in the anime context
    elif user_data and user_data["state"] == "awaiting_waifu_name" and user_data.get("anime"):
        waifu_name = message.text.strip()
        user_states[user_id]["name"] = waifu_name
        user_states[user_id]["state"] = "awaiting_waifu_rarity"
        await message.reply_text(
            "Now, choose the character's rarity:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(rarity, callback_data=f"select_rarity_{rarity}")]
                    for rarity in rarity_emojis.keys()
                ]
            )
        )

    # Handle renaming anime state
    elif user_data and user_data["state"] == "renaming_anime" and user_data.get("anime"):
        old_anime_name = user_data["anime"]
        new_anime_name = message.text.strip()
        await collection.update_many({"anime": old_anime_name}, {"$set": {"anime": new_anime_name}})
        await message.reply_text(f"The anime '{old_anime_name}' has been renamed to '{new_anime_name}' successfully.")
        await app.send_message(CHARA_CHANNEL_ID, f"📢 The sudo user renamed the anime from '{old_anime_name}' to '{new_anime_name}'.")
        await app.send_message(SUPPORT_CHAT, f"📢 The sudo user renamed the anime from '{old_anime_name}' to '{new_anime_name}'.")
        user_states.pop(user_id, None)
        
    # Handle renaming waifu state
    elif user_data and user_data["state"] == "renaming_waifu" and user_data.get("waifu_id"):
        waifu_id = user_data["waifu_id"]
        new_waifu_name = message.text.strip()
        waifu = await collection.find_one({"id": waifu_id})
        if waifu:
            old_name = waifu["name"]
            await collection.update_one(
                {"id": waifu_id},
                {"$set": {"name": new_waifu_name}}
            )
            await message.reply_text(f"The character has been renamed to '{new_waifu_name}' successfully.")
            await app.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=waifu["img_url"],
                caption=f'💫 <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> has renamed the character\n'
                        f'🆔 <b>Waifu ID:</b> {waifu_id}\n'
                        f'👤 <b>New Name:</b> {new_waifu_name}\n'
                        f'🎌 <b>Anime:</b> {waifu["anime"]}',
            )
            await app.send_photo(
                chat_id=SUPPORT_CHAT,
                photo=waifu["img_url"],
                caption=f'💫 <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a> has renamed the character\n'
                        f'🆔 <b>Waifu ID:</b> {waifu_id}\n'
                        f'👤 <b>New Name:</b> {new_waifu_name}\n'
                        f'🎌 <b>Anime:</b> {waifu["anime"]}',
            )
        else:
            await message.reply_text("Failed to rename the waifu.")
        user_states.pop(user_id, None)
    else:
        # If there's no relevant user state, send a generic response
        await message.reply_text("Please use the appropriate command to add or edit anime information.")

@app.on_callback_query(filters.regex('^add_waifu_'))
async def choose_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "awaiting_waifu_name", "anime": selected_anime, "name": None, "rarity": None}
    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"You've selected {selected_anime}. Now, please enter the new character's name:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel_add_waifu")]]
        )
    )

@app.on_callback_query(filters.regex('^add_anime$'))
async def add_anime_callback(client, callback_query):
    await callback_query.message.edit_text(
        "Please enter the name of the anime you want to add:"
    )
    user_states[callback_query.from_user.id] = {"state": "adding_anime"}

@app.on_callback_query(filters.regex('^cancel_add_waifu$'))
async def cancel_add_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^rename_anime_'))
async def rename_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "renaming_anime", "anime": selected_anime}

    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"You've selected '{selected_anime}'. Please enter the new name for this anime:"
    )

@app.on_callback_query(filters.regex('^remove_anime_'))
async def remove_anime_callback(client, callback_query):
    selected_anime = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_removal", "anime": selected_anime}

    await app.send_message(
        chat_id=callback_query.from_user.id,
        text=f"Are you sure you want to delete the anime '{selected_anime}'?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data="confirm_remove_anime")],
                [InlineKeyboardButton("No", callback_data="cancel_remove_anime")]
            ]
        )
    )
   


@app.on_callback_query(filters.regex('^confirm_remove_anime$'))
async def confirm_remove_anime_callback(client, callback_query):
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_removal" and user_data.get("anime"):
        selected_anime = user_data["anime"]
        await collection.delete_many({"anime": selected_anime})
        await callback_query.message.edit_text(f"The anime '{selected_anime}' has been deleted successfully.")
        await app.send_message(CHARA_CHANNEL_ID, f"📢 The sudo user deleted the anime '{selected_anime}'.")
        await app.send_message(SUPPORT_CHAT, f"📢 The sudo user deleted the anime '{selected_anime}'.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_remove_anime$'))
async def cancel_remove_anime_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")


@app.on_callback_query(filters.regex('^rename_waifu_'))
async def rename_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "renaming_waifu", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"You've selected waifu ID: '{waifu_id}'. Please enter the new name for this character:"
    )


@app.on_callback_query(filters.regex('^change_image_'))
async def change_image_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "changing_image", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"You've selected waifu ID: '{waifu_id}'. Please send the new image for this character:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel_change_image")]]
        )
    )


@app.on_callback_query(filters.regex('^cancel_change_image$'))
async def cancel_change_image_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^change_rarity_'))
async def change_rarity_callback(client, callback_query):
    try:
        # Extracting the waifu_id from the callback data
        _, waifu_id = callback_query.data.rsplit('_', 1)

        # Now you have the waifu_id, you can proceed with your logic here
        rarity_keyboard = [
            [InlineKeyboardButton(rarity, callback_data=f"set_rarity_{rarity}_{waifu_id}")]
            for rarity in rarity_emojis.keys()
        ]
        await callback_query.message.edit_text(
            "Choose a new rarity:",
            reply_markup=InlineKeyboardMarkup(rarity_keyboard)
        )
    except Exception as e:
        await callback_query.answer("An error occurred while processing your request.", show_alert=True)
        print(f"Error in change_rarity_callback: {str(e)}")

@app.on_callback_query(filters.regex('^set_rarity_'))
async def set_rarity_callback(client, callback_query):
    try:
        # Extracting the rarity and waifu_id from the callback data
        _, new_rarity, waifu_id = callback_query.data.rsplit('_', 2)

        # Now you have the new_rarity and waifu_id, you can proceed with your logic here
        waifu = await collection.find_one({"id": waifu_id})
        
        if not waifu:
            await callback_query.answer("Character not found.", show_alert=True)
            return

        old_rarity = waifu["rarity"]
        await collection.update_one({"id": waifu_id}, {"$set": {"rarity": new_rarity}})
        
        updated_waifu = await collection.find_one({"id": waifu_id})

        # Send update message to the sudo user
        update_message = (
            f'🏅 Rᴀʀɪᴛʏ ᴜᴘᴅᴀᴛᴇ 🏅\n'
            f'🆔 <b>ID:</b> {updated_waifu["id"]}\n'
            f'👤 <b>Name:</b> {updated_waifu["name"]}\n'
            f'🎌 <b>Anime:</b> {updated_waifu["anime"]}\n'
            f'🎖 <b>New Rarity:</b> {new_rarity}\n'
            f'💥 <i>{updated_waifu["name"]} ɪꜱ ɴᴏᴡ ᴍᴏʀᴇ ᴠᴀʟᴜᴀʙʟᴇ!</i>'
        )
        await app.send_photo(callback_query.from_user.id, photo=updated_waifu["img_url"], caption=update_message)

        # Send update message to CHARA_CHANNEL_ID and SUPPORT_CHAT
        await app.send_photo(CHARA_CHANNEL_ID, photo=updated_waifu["img_url"], caption=update_message)
        await app.send_photo(SUPPORT_CHAT, photo=updated_waifu["img_url"], caption=update_message)

        await callback_query.message.edit_text(f"Rarity changed to {new_rarity} successfully.")
    except Exception as e:
        await callback_query.answer("An error occurred while processing your request.", show_alert=True)
        print(f"Error in set_rarity_callback: {str(e)}")

@app.on_callback_query(filters.regex('^reset_waifu_'))
async def reset_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_reset", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"Are you sure you want to reset the character ID '{waifu_id}' to global grabbed 0?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data=f"confirm_reset_waifu_{waifu_id}")],
                [InlineKeyboardButton("No", callback_data="cancel_reset_waifu")]
            ]
        )
    )

@app.on_callback_query(filters.regex('^confirm_reset_waifu_'))
async def confirm_reset_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 3)[-1]  # Extract waifu ID
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_reset" and user_data.get("waifu_id") == waifu_id:
        waifu = await collection.find_one_and_update(
            {"id": waifu_id},
            {"$set": {"global_grabbed": 0}},
            return_document=ReturnDocument.AFTER
        )
        if waifu:
            # Remove from everyone's harem
            await collection.update_many({}, {"$pull": {"harem": waifu_id}})
            await callback_query.message.edit_text(f"The character ID '{waifu_id}' has been reset successfully.")
            await app.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=waifu["img_url"],
                caption=f'🔄 ʀᴇꜱᴇᴛ ɴᴏᴛɪᴄᴇ 🔄\n'
                        f'🆔 <b>ID:</b> {waifu_id}\n'
                        f'👤 <b>Name:</b> {waifu["name"]}\n'
                        f'🎌 <b>Anime:</b> {waifu["anime"]}\n\n'
                        f'⚠️ <i>Tʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀꜱ ʙᴇᴇɴ ʀᴇꜱᴇᴛ ᴀɴᴅ ɪꜱ ʀᴇᴀᴅʏ ꜰᴏʀ ɴᴇᴡ ᴏᴡɴᴇʀꜱ!</i>',
            )
        else:
            await callback_query.message.edit_text("Failed to reset the waifu.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_reset_waifu$'))
async def cancel_reset_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")

@app.on_callback_query(filters.regex('^remove_waifu_'))
async def remove_waifu_callback(client, callback_query):
    waifu_id = callback_query.data.split('_', 2)[-1]
    user_states[callback_query.from_user.id] = {"state": "confirming_waifu_removal", "waifu_id": waifu_id}
    await callback_query.message.edit_text(
        f"Are you sure you want to remove the character ID '{waifu_id}'?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Yes", callback_data="confirm_remove_waifu")],
                [InlineKeyboardButton("No", callback_data="cancel_remove_waifu")]
            ]
        )
    )

@app.on_callback_query(filters.regex('^confirm_remove_waifu$'))
async def confirm_remove_waifu_callback(client, callback_query):
    user_data = user_states.get(callback_query.from_user.id)
    if user_data and user_data.get("state") == "confirming_waifu_removal" and user_data.get("waifu_id"):
        waifu_id = user_data["waifu_id"]
        waifu = await collection.find_one_and_delete({"id": waifu_id})
        if waifu:
            await callback_query.message.edit_text(f"The Character ID '{waifu_id}' has been removed successfully.")
            await app.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=waifu["img_url"],
                caption=f'🗑️ ᴄʜᴀʀᴀᴄᴛᴇʀ ʀᴇᴍᴏᴠᴀʟ 🗑️\n'
                        f'👤 <b>Name:</b> {waifu["name"]}\n'
                        f'🎌 <b>Anime:</b> {waifu["anime"]}\n\n'
                        f'❌ <i>Tʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ʟɪꜱᴛ!</i>',
            )
            await app.send_photo(
                chat_id=SUPPORT_CHAT,
                photo=waifu["img_url"],
                caption=f'🗑️ ᴄʜᴀʀᴀᴄᴛᴇʀ ʀᴇᴍᴏᴠᴀʟ 🗑️\n'
                        f'👤 <b>Name:</b> {waifu["name"]}\n'
                        f'🎌 <b>Anime:</b> {waifu["anime"]}\n\n'
                        f'❌ <i>Tʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ʟɪꜱᴛ!</i>',
            )
        else:
            await callback_query.message.edit_text("Failed to remove the waifu.")
        user_states.pop(callback_query.from_user.id, None)

@app.on_callback_query(filters.regex('^cancel_remove_waifu$'))
async def cancel_remove_waifu_callback(client, callback_query):
    user_states.pop(callback_query.from_user.id, None)
    await callback_query.message.edit_text("Operation canceled successfully.")
         
# Main function to run the bot
async def main():
    await app.start()
    await notify_restart()  # Notify sudo users on bot startup
    asyncio.create_task(scheduled_messages())  # Start the scheduled messages
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
