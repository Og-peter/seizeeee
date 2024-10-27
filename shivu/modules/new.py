import random
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId
from shivu import user_collection, shivuu, SPECIALGRADE, GRADE1, db

backup_collection = db["backup_collection"]

# List of emojis for fun effect
EMOJIS = ['🚀', '💥', '✨', '🔥', '⚡', '🏆', '🎉', '🔄', '👑']

@shivuu.on_message(filters.command("transfer"))
async def transfer(client: Client, message):
    # Check authorization
    if str(message.from_user.id) not in SPECIALGRADE and str(message.from_user.id) not in GRADE1:
        await message.reply_text("🚫 You are not authorized to use this command.")
        return

    # Validate command usage
    if len(message.command) != 3:
        await message.reply_text(f"{random.choice(EMOJIS)} Please provide two user IDs! Usage: /transfer [Source User ID] [Target User ID]")
        return

    # Extract and validate user IDs
    try:
        source_user_id = int(message.command[1])
        target_user_id = int(message.command[2])
    except ValueError:
        await message.reply_text("⚠️ Invalid user IDs provided. Please provide valid integers.")
        return

    # Fetch source and target users
    source_user = await user_collection.find_one({'id': source_user_id})
    target_user = await user_collection.find_one({'id': target_user_id})

    # Handle cases where users don't exist or characters are empty
    if not source_user:
        await message.reply_text("❌ Source user does not exist!")
        return
    if not source_user.get('characters'):
        await message.reply_text("❌ Source user has no characters to transfer!")
        return

    # Calculate character rarity counts
    characters = source_user['characters']
    rarity_counts = {
        "Legendary": len([c for c in characters if c['rarity'] == "Legendary"]),
        "Rare": len([c for c in characters if c['rarity'] == "Rare"]),
        "Medium": len([c for c in characters if c['rarity'] == "Medium"]),
        "Common": len([c for c in characters if c['rarity'] == "Common"])
    }
    total_characters = len(characters)
    
    # Confirmation message with rarity counts
    confirm_text = (
        f"Do you want to transfer {source_user.get('name', 'None')}'s harem to {target_user.get('name', 'Unknown')}?\n\n"
        f"Name: {source_user.get('name', 'None')}\n"
        f"User ID: {source_user_id}\n"
        f"Character Count: {total_characters}\n\n"
        f"Rarity Counts:\n"
        f"╭───────────────────\n"
        f"├─➩ 🟡 Rarity: Legendary: {rarity_counts['Legendary']}\n"
        f"├─➩ 🟠 Rarity: Rare: {rarity_counts['Rare']}\n"
        f"├─➩ 🔴 Rarity: Medium: {rarity_counts['Medium']}\n"
        f"├─➩ 🔵 Rarity: Common: {rarity_counts['Common']}\n"
        f"╰───────────────────"
    )

    # Inline keyboard for confirmation
    confirm_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Transfer", callback_data=f"confirm_transfer_{source_user_id}_{target_user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_transfer")]
    ])

    await message.reply_text(confirm_text, reply_markup=confirm_keyboard)


@shivuu.on_callback_query(filters.regex(r'^confirm_transfer_'))
async def confirm_transfer(callback_query):
    # Extract source and target user IDs from callback data
    data = callback_query.data.split('_')
    source_user_id = int(data[2])
    target_user_id = int(data[3])

    # Fetch the source and target users
    source_user = await user_collection.find_one({'id': source_user_id})
    target_user = await user_collection.find_one({'id': target_user_id})

    # Handle missing users just in case
    if not source_user or not target_user:
        await callback_query.message.edit_text("❌ Transfer failed: one of the users does not exist.")
        return

    # Placeholder transfer logic
    # Here, you would transfer `characters` from `source_user` to `target_user`
    # For example, this might involve updating the `target_user` document with the characters from `source_user`.
    # await user_collection.update_one({'id': target_user_id}, {'$push': {'characters': {'$each': source_user['characters']}}})
    # await user_collection.update_one({'id': source_user_id}, {'$set': {'characters': []}})  # Clear characters from source user

    # Success response with emoji and transfer details
    source_name = source_user.get('name', 'None')
    target_name = target_user.get('name', 'Unknown')
    success_message = (
        f"🌟 Yahoo!! Harem Has Been Transferred! 🌟\n\n"
        f"🔄 From {source_name} ➡️ To {target_name}\n\n"
        f"{random.choice(EMOJIS)} Harem transferred successfully from user {source_user_id} to user {target_user_id}."
    )
    await callback_query.message.edit_text(success_message)


@shivuu.on_callback_query(filters.regex(r'^cancel_transfer'))
async def cancel_transfer(callback_query):
    await callback_query.answer("❌ Transfer canceled.")
    await callback_query.message.delete()
