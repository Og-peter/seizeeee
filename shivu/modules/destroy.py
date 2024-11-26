from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import db, user_collection, SPECIALGRADE
from shivu import shivuu as app
import asyncio

# Constants
HAREM_SIZE_LIMIT = 10  # Max waifu collection size

# Helper function to fetch and structure user info
async def get_user_info(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        return "❌ <b>User not found in the database.</b>", None

    # Extract user details
    first_name = user.get('first_name', 'Unknown')
    last_name = user.get('last_name', '')
    username = user.get('username', 'None')
    characters = user.get('characters', [])

    rarity_counts = {}

    # Count waifus by rarity
    for waifu in characters:
        rarity = waifu.get("rarity", "Unknown")
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

    # Create a summary of the sender's waifus
    rarity_summary = "\n".join([f"❖ │ {rarity}: {count}" for rarity, count in rarity_counts.items()])

    user_info = (
        f"─────────────────────────\n"
        f"❖ │  <b>ɴᴀᴍᴇ:</b> {first_name} {last_name}\n"
        f"─────────────────────────\n"
        f"❖ │  <b>ᴜsᴇʀɴᴀᴍᴇ:</b> @{username}\n"
        f"❖ │  <b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
        f"❖ │  <b>ᴛᴏᴛᴀʟ ᴄʜᴀʀᴀᴄᴛᴇʀs:</b> {len(characters)} / {HAREM_SIZE_LIMIT}\n"
        f"❖ │  <b>ʀᴀʀɪᴛʏ ʙʀᴇᴀᴋᴅᴏᴡɴ:</b>\n"
        f"{rarity_summary}\n"
        f"•────────•°•𑁍•°•───────•\n"
    )

    return user_info, user

# Command to fetch user info
@app.on_message(filters.command(["info"]))
async def info_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply_text("🚫 <b>This command is exclusive to Special Grade sorcerers!</b>")
        return

    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("⚠️ <b>Invalid user ID format.</b>")
            return

    if user_id:
        await message.reply_text("🔍 <i>Fetching user information...</i>")
        await asyncio.sleep(1)  # Simulating processing delay
        user_info, user = await get_user_info(user_id)

        if user:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Delete Harem", callback_data=f"delete_harem_{user_id}")]
            ])
            photo_file_id = None
            async for photo in client.get_chat_photos(user_id, limit=1):
                photo_file_id = photo.file_id
            if photo_file_id:
                await message.reply_photo(photo_file_id, caption=user_info, reply_markup=keyboard)
            else:
                await message.reply_text(user_info, reply_markup=keyboard)
        else:
            await message.reply_text(user_info)
    else:
        await message.reply_text("⚠️ <b>Please specify a user ID or reply to a user's message to get their info.</b>")

# Callback to delete user's harem
@app.on_callback_query(filters.regex(r'^delete_harem_'))
async def callback_delete_harem(client, callback_query):
    user_id = int(callback_query.data.split('_')[2])
    if str(callback_query.from_user.id) not in SPECIALGRADE:
        await callback_query.answer("🚫 You lack the authority to execute this action!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_delete_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_delete_{user_id}")]
    ])
    await callback_query.message.edit_text("⚠️ <b>Confirm harem deletion?</b>", reply_markup=keyboard)

# Callback to confirm harem deletion
@app.on_callback_query(filters.regex(r'^confirm_delete_'))
async def callback_confirm_delete(client, callback_query):
    user_id = int(callback_query.data.split('_')[2])
    if str(callback_query.from_user.id) not in SPECIALGRADE:
        await callback_query.answer("🚫 You cannot perform this action!", show_alert=True)
        return

    user = await user_collection.find_one({'id': user_id})
    if user:
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': []}})
        await callback_query.message.edit_text("🗑 <b>Harem successfully deleted.</b>")
    else:
        await callback_query.message.edit_text("❌ <b>Failed to delete harem. User not found.</b>")

# Callback to cancel harem deletion
@app.on_callback_query(filters.regex(r'^cancel_delete_'))
async def callback_cancel_delete(client, callback_query):
    await callback_query.message.edit_text("❌ <b>Harem deletion cancelled.</b>")
