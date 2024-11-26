from pyrogram import filters
from shivu import db, user_collection, SPECIALGRADE, GRADE1
from shivu import shivuu as app
import random
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

backup_collection = db["backup_collection"]

# Back up user characters to the backup collection
async def backup_characters(user_id, characters):
    await backup_collection.insert_one({'user_id': user_id, 'characters': characters})

# Function to count characters by rarity
def count_characters_by_rarity(characters):
    rarity_count = {}
    for character in characters:
        rarity = character.get("rarity", "Unknown")
        rarity_count[rarity] = rarity_count.get(rarity, 0) + 1
    return rarity_count

# Erase characters for a user
async def erase_characters_for_user(user_id, num_characters):
    user = await user_collection.find_one({'id': user_id})

    if user:
        total_characters = len(user.get('characters', []))
        
        if total_characters == 0:
            return f"User <a href='tg://user?id={user_id}'>{user.get('first_name', 'User')}</a> has no characters in their harem."

        num_characters_to_remove = min(num_characters, total_characters)
        
        if num_characters_to_remove > 0:
            characters_to_remove = random.sample(user['characters'], num_characters_to_remove)
            user_characters = [character for character in user['characters'] if character not in characters_to_remove]
            
            # Backup characters before erasing
            await backup_characters(user_id, user['characters'])

            # Update user collection with remaining characters
            await user_collection.update_one(
                {'id': user_id},
                {'$set': {'characters': user_characters}}
            )

            # Count the rarity of removed characters and remaining characters
            rarity_count_removed = count_characters_by_rarity(characters_to_remove)
            rarity_count_remaining = count_characters_by_rarity(user_characters)

            # Determine the most erased rarity
            max_erased_rarity = max(rarity_count_removed, key=rarity_count_removed.get)
            max_erased_count = rarity_count_removed[max_erased_rarity]

            # Create messages for rarity counts
            removed_rarity_message = "\n".join([f"{rarity}: {count}" for rarity, count in rarity_count_removed.items()])
            remaining_rarity_message = "\n".join([f"{rarity}: {count}" for rarity, count in rarity_count_remaining.items()])

            return (
                f"🗑️ **Erase Summary**:\n"
                f"User: <a href='tg://user?id={user_id}'>{user.get('first_name', 'User')}</a>\n\n"
                f"**Total Erased Characters:** {num_characters_to_remove}\n"
                f"**Total Remaining Characters:** {len(user_characters)}\n"
                f"**Most Erased Rarity:** {max_erased_rarity} ({max_erased_count} characters)\n\n"
                f"**Removed Characters by Rarity:**\n{removed_rarity_message}\n\n"
                f"**Remaining Characters by Rarity:**\n{remaining_rarity_message}"
            )
        else:
            return f"Cannot remove characters. User <a href='tg://user?id={user_id}'>{user.get('first_name', 'User')}</a> has no characters to erase."
    else:
        return f"User with ID {user_id} not found."

# Send notification to Special Grade users about the erase action
async def send_notification_to_specialgrade(eraser_id, eraser_name, target_id, target_name, num_characters):
    message = (
        f"⚠️ **Action: Erase Characters**\n"
        f"Eraser: <a href='tg://user?id={eraser_id}'>{eraser_name}</a>\n"
        f"Target: <a href='tg://user?id={target_id}'>{target_name}</a> (ID: {target_id})\n"
        f"Number of characters erased: {num_characters}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reverse", callback_data=f"reverse_{target_id}")]
    ])
    for user_id in SPECIALGRADE:
        await app.send_message(user_id, message, reply_markup=keyboard)

# Restore characters from backup
async def restore_characters(user_id):
    backup = await backup_collection.find_one({'user_id': user_id})
    if backup:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': backup['characters']}}
        )
        await backup_collection.delete_one({'user_id': user_id})
        return True
    return False

# Command to erase characters
@app.on_message(filters.command(["erase"]))
async def erase_characters_command(client, message):
    user_id = str(message.from_user.id)
    
    # Check if the user has sufficient permissions
    if user_id not in SPECIALGRADE and user_id not in GRADE1:
        await message.reply_text("🚫 This command can only be used by Special Grade and Grade 1 sorcerers.")
        return

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id_to_erase_characters_for = message.reply_to_message.from_user.id
        if len(message.command) == 2:
            num_characters_to_erase_str = message.command[1]
            if not num_characters_to_erase_str.isdigit():
                await message.reply_text("❌ Please enter a valid integer for the number of characters to erase.")
                return
            num_characters_to_erase = int(num_characters_to_erase_str)
            result_message = await erase_characters_for_user(user_id_to_erase_characters_for, num_characters_to_erase)
            await message.reply_text(result_message)
            if "Successfully removed" in result_message:
                eraser_id = message.from_user.id
                eraser_name = message.from_user.first_name
                target_id = message.reply_to_message.from_user.id
                target_name = message.reply_to_message.from_user.first_name
                await send_notification_to_specialgrade(eraser_id, eraser_name, target_id, target_name, num_characters_to_erase)
        else:
            await message.reply_text("Usage: /erase {num_characters}")
    else:
        await message.reply_text("❌ Please reply to a user's message to erase their characters.")

# Handle callback to reverse erase operation
@app.on_callback_query(filters.regex(r"^reverse_\d+$"))
async def reverse_erase(client, callback_query: CallbackQuery):
    target_id = int(callback_query.data.split("_")[1])

    # Ensure the user has permissions to reverse the erase
    if str(callback_query.from_user.id) in SPECIALGRADE:
        restored = await restore_characters(target_id)
        if restored:
            await callback_query.answer("✅ The erase operation has been reversed.")
            await callback_query.edit_message_text("✅ The erase operation has been reversed.")
        else:
            await callback_query.answer("⚠️ No backup found to restore.", show_alert=True)
    else:
        await callback_query.answer("🚫 You do not have permission to reverse this operation.", show_alert=True)
