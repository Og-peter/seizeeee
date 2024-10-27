from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import db, user_collection, SPECIALGRADE
from shivu import shivuu as app
import asyncio
import time

# Collections
backup_collection = db["backup_collection"]
log_collection = db["log_collection"]
reputation_collection = db["reputation_collection"]

# Constants
HAREM_SIZE_LIMIT = 10  # Set a limit on waifu collection size
RESTORE_COOLDOWN = 60 * 10  # 10 minutes cooldown for reverse action

LOG_CHANNEL_ID = -1002446048543  # Replace with your log channel ID

async def log_action(action, user_id, initiator_id):
    """ Log deletion or restoration actions """
    log_message = (
        f"📝 <b>Action:</b> {action.capitalize()}\n"
        f"👤 <b>User ID:</b> {user_id}\n"
        f"👮‍♂️ <b>Initiator ID:</b> {initiator_id}\n"
        f"🕒 <b>Timestamp:</b> {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}"
    )
    
    # Insert log in the database
    await log_collection.insert_one({
        'action': action,
        'user_id': user_id,
        'initiator_id': initiator_id,
        'timestamp': time.time()
    })
    
    # Send log message to the log channel
    try:
        await app.send_message(LOG_CHANNEL_ID, log_message, parse_mode="html")
    except Exception as e:
        print(f"Failed to send log to channel: {e}")
        


async def backup_characters(user_id, characters):
    await backup_collection.insert_one({
        'user_id': user_id,
        'characters': characters,
        'backup_time': time.time()
    })

async def delete_harem(client, user_id):
    user = await user_collection.find_one({'id': user_id})
    if user:
        # Backup the harem before deleting it
        await backup_characters(user_id, user['characters'])
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': []}})
        return True
    return False

async def send_notification_to_specialgrade(eraser_id, eraser_name, target_id, target_name):
    message = (
        f"🚨 <b>Action:</b> Delete Harem\n"
        f"✍️ <b>Eraser:</b> <a href='tg://user?id={eraser_id}'>{eraser_name}</a>\n"
        f"🎯 <b>Target:</b> <a href='tg://user?id={target_id}'>async def get_user_info(user_id):
    user = await user_collection.find_one({'id': user_id})

    if user:
        characters = user.get('characters', [])
        harem_size = len(characters)

        # Calculating rarity counts
        rarity_counts = {
            'legendary': sum(1 for char in characters if char.get('rarity') == 'legendary'),
            'rare': sum(1 for char in characters if char.get('rarity') == 'rare'),
            'medium': sum(1 for char in characters if char.get('rarity') == 'medium'),
            'common': sum(1 for char in characters if char.get('rarity') == 'common'),
            'chibi': sum(1 for char in characters if char.get('rarity') == 'chibi'),
            'limited edition': sum(1 for char in characters if char.get('rarity') == 'limited edition'),
            'premium': sum(1 for char in characters if char.get('rarity') == 'premium'), 
            'exclusive': sum(1 for char in characters if char.get('rarity') == 'exclusive'),
            'exotic': sum(1 for char in characters if char.get('rarity') == 'exotic'),
            'astral': sum(1 for char in characters if char.get('rarity') == 'astral'),
            'valentine': sum(1 for char in characters if char.get('rarity') == 'valentine')
        }

        user_info = (
            f"🎭 <b>User Profile:</b>\n\n"
            f"🪪 <b>Name:</b> {user.get('first_name', 'Unknown')} {user.get('last_name', '')}\n"
            f"🧪 <b>Username:</b> @{user.get('username', 'None')}\n"
            f"🔩 <b>User ID:</b> <code>{user_id}</code>\n"
            f"👒 <b>Waifu Count:</b> {harem_size} / {HAREM_SIZE_LIMIT} <b>(Max)</b>\n"
            f"🌟 <b>Status:</b> {'👑 Harem Master' if harem_size >= HAREM_SIZE_LIMIT else '✨ Keep Collecting!'}\n\n"
            f"✳️ <b>Rarity Counts:</b>\n"
            f"╭───────────────────\n"
            f"├─➩ 🟡 <b>Legendary:</b> {rarity_counts['legendary']}\n"
            f"├─➩ 🟠 <b>Rare:</b> {rarity_counts['rare']}\n"
            f"├─➩ 🔵 <b>Medium:</b> {rarity_counts['medium']}\n"
            f"├─➩ ⚪ <b>Common:</b> {rarity_counts['common']}\n"
            f"├─➩ 🟢 <b>Chibi:</b> {rarity_counts['chibi']}\n"
            f"├─➩ 🟣 <b>Limited Edition:</b> {rarity_counts['limited edition']}\n"
            f"├─➩ 🟤 <b>Premium:</b> {rarity_counts['premium']}\n"
            f"├─➩ 🔶 <b>Exclusive:</b> {rarity_counts['exclusive']}\n"
            f"├─➩ 🔷 <b>Exotic:</b> {rarity_counts['exotic']}\n"
            f"├─➩ ✨ <b>Astral:</b> {rarity_counts['astral']}\n"
            f"├─➩ 💖 <b>Valentine:</b> {rarity_counts['valentine']}\n"
            f"╰───────────────────"
        )

        return user_info, user
    else:
        return "❌ <b>User not found in the database.</b>", None{target_name}</a>\n"
        "⚔️ The user's harem has been <b>eliminated</b>."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧬 Reverse", callback_data=f"reverse_{target_id}")]
    ])
    for user_id in SPECIALGRADE:
        await app.send_message(user_id, message, reply_markup=keyboard)

async def notify_user(user_id, message):
    try:
        await app.send_message(user_id, message)
    except Exception as e:
        print(f"Failed to send message to user {user_id}: {e}")

async def restore_characters(user_id):
    backup = await backup_collection.find_one({'user_id': user_id})
    if backup:
        # Ensure cooldown time for restoration has passed
        if time.time() - backup['backup_time'] < RESTORE_COOLDOWN:
            return False, "⏳ Cooldown: You must wait before restoring the harem!"
        
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': backup['characters']}}
        )
        await backup_collection.delete_one({'user_id': user_id})
        return True, "🔄 Harem restored successfully!"
    return False, "❌ No backup found for this user."

async def increase_reputation(user_id, points=1):
    await reputation_collection.update_one(
        {'user_id': user_id},
        {'$inc': {'reputation': points}},
        upsert=True
    )

@app.on_message(filters.command(["info"]))
async def info_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply_text("🚫 <b>This command is exclusive to Special Grade Sorcerers!</b>")
        return

    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        user_id = int(message.command[1])

    if user_id:
        await message.reply_text("🔍 <i>Retrieving user information...</i>")
        await asyncio.sleep(1)  # Adding delay for cool effect
        user_info, user = await get_user_info(user_id)

        if user:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧪 Delete Harem", callback_data=f"delete_harem_{user_id}")]
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
        await message.reply_text("⚠️ <b>Please specify a user ID or reply to a user's message to fetch their info.</b>")

@app.on_callback_query(filters.regex(r'^delete_harem_'))
async def callback_delete_harem(client, callback_query):
    user_id = int(callback_query.data.split('_')[2])
    callback_user_id = callback_query.from_user.id

    if str(callback_user_id) not in SPECIALGRADE:
        await callback_query.answer("🚫 You lack the authority to execute this! 🤷‍♂️", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💥 Yes, DELETE", callback_data=f"confirm_delete_{user_id}")],
        [InlineKeyboardButton("🙅‍♂️ No, CANCEL", callback_data=f"cancel_delete_{user_id}")]
    ])

    confirmation_message = (
        "⚠️ <b>Are you absolutely sure you want to delete this user's harem?</b>\n\n"
        "🔍 This action is irreversible! 💔\n\n"
        "Please confirm your choice!"
    )

    await callback_query.message.reply_text(confirmation_message, reply_markup=keyboard)
    await callback_query.answer()  # Clear the callback query after responding

@app.on_callback_query(filters.regex(r'^confirm_delete_'))
async def callback_confirm_delete(client, callback_query):
    user_id = int(callback_query.data.split('_')[2])
    callback_user_id = callback_query.from_user.id

    if str(callback_user_id) not in SPECIALGRADE:
        await callback_query.answer("🚫 You lack the authority to perform this action! ❌", show_alert=True)
        return

    success = await delete_harem(client, user_id)
    if success:
        # Notify the user that their harem was deleted with a styled message
        await callback_query.message.reply_text("🔫 Your harem has been successfully eliminated!\n\n"
                                                "Such is the fate of those who cross the Special Grade!")
        
        # Log the action in the database
        await log_action('delete', user_id, callback_user_id)
        
        # Get the eraser's name and target's name for the notification
        eraser_name = callback_query.from_user.first_name
        target_name = (await app.get_users(user_id)).first_name
        
        # Send notification to SpecialGrade users
        await send_notification_to_specialgrade(callback_user_id, eraser_name, user_id, target_name)
        
        # Notify the user whose harem was deleted
        await notify_user(user_id, f"⚔️ Your harem has been deleted by Special Grade sorcerer {eraser_name}.")
        
        # Add reputation for the eraser
        await increase_reputation(callback_user_id, 1)

        # Send log to the log channel
        log_message = (
            f"🚨 Action: Delete Harem\n"
            f"👤 Eraser: {eraser_name}\n"
            f"🎯 Target: {target_name}\n"
            "⚔️ The user's harem has been eliminated."
        )
        await app.send_message(LOG_CHANNEL_ID, log_message)

    else:
        await callback_query.message.reply_text("❌ Failed to delete harem. User not found or already eliminated.")
        
@app.on_callback_query(filters.regex(r'^cancel_delete_'))
async def callback_cancel_delete(client, callback_query):
    await callback_query.message.reply_text("💨 The harem deletion has been successfully cancelled.\n"
                                             "All characters are safe for now!")

@app.on_callback_query(filters.regex(r'^reverse_\d+$'))
async def reverse_erase(client, callback_query):
    target_id = int(callback_query.data.split("_")[1])

    if str(callback_query.from_user.id) in SPECIALGRADE:
        restored, message = await restore_characters(target_id)
        if restored:
            await callback_query.answer("✅ Restoration Successful!")
            await callback_query.edit_message_text("🔄 The erase operation has been successfully reversed!\n"
                                                    "✨ Your characters have returned! 🎉")
            await log_action('restore', target_id, callback_query.from_user.id)
            await increase_reputation(callback_query.from_user.id, -1)  # Remove reputation for reversal
        else:
            await callback_query.answer(f"❌ Error: {message}", show_alert=True)
    else:
        await callback_query.answer("❌ Access Denied!\nYou do not have permission to reverse this operation.", show_alert=True)
