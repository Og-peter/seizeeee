from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, user_collection
import logging
import random

# Emoji animations and cool text for a more engaging user experience
ANIMATED_EMOJIS = ['✨', '🎉', '💫', '🌟', '🔥', '🌀', '🎇', '💖', '🎆', '💥', '🌈']
SUCCESS_EMOJIS = ['✅', '✔️', '🆗', '🎯', '🏅']
CANCEL_EMOJIS = ['❌', '🚫', '⚠️', '🔴', '🚷']

# Dictionary to hold rarity emojis and colors
RARITY_EMOJIS = {
    '𝘾𝙊𝙈𝙈𝙊𝙉': ('⚪️', 'Common'),
    '𝙈𝙀𝘿𝙄𝙐𝙈': ('🔵', 'Medium'),
    '𝘾𝙃𝙄𝘽𝙄': ('👶', 'Chibi'),
    '𝙍𝘼𝙍𝙀': ('🟠', 'Rare'),
    '𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔': ('🟡', 'Legendary'),
    '𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀': ('💮', 'Exclusive'),
    '𝙋𝙍𝙀𝙈𝙄𝙐𝙈': ('🫧', 'Premium'),
    '𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉': ('🔮', 'Limited Edition'),
    '𝙀𝙓𝙊𝙏𝙄𝘾': ('🌸', 'Exotic'),
    '𝘼𝙎𝙏𝙍𝘼𝙇': ('🎐', 'Astral'),
    '𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀': ('💞', 'Valentine')
}

# Initialize user_data if not already present
if not hasattr(app, 'user_data'):
    app.user_data = {}

@app.on_message(filters.command("fav"))
async def fav(client: Client, message):
    user_id = message.from_user.id

    # Check if the command has enough arguments
    if len(message.command) < 2:
        await message.reply_text(
            f'{random.choice(CANCEL_EMOJIS)} **Invalid usage!**\n'
            f'Use `/fav (waifu_id)` to set your favorite waifu.\n'
            f'**Example:** `/fav 32`.'
        )
        return

    character_id = message.command[1]

    # Fetch user from database
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await message.reply_text('😔 **You haven\'t seized any characters yet!**')
        return

    # Find the character in the user's collection
    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        await message.reply_text('🙄 **This character is not in your harem!**')
        return

    # Extract character details
    name = character.get('name', 'Unknown Name')
    anime = character.get('anime', 'Unknown Anime')
    rarity = character.get('rarity', 'Common')
    rarity_emoji, rarity_display = RARITY_EMOJIS.get(rarity, ('', rarity))

    # Send character photo with confirmation message and inline buttons
    confirmation_message = await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🌟 **Are you sure you want to set this character as your favorite?** 🌟\n\n"
            f"🧃 **Name:** `{name}`\n"
            f"⚜️ **Anime:** `{anime}`\n"
            f"🥂 **Rarity:** {rarity_emoji} `{rarity_display}`\n\n"
            "🔍 **Choose an option:**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Confirm", callback_data=f"fav_yes_{character_id}"),
                InlineKeyboardButton("🔴 Cancel", callback_data=f"fav_no_{character_id}")
            ]
        ])
    )

    # Store the character ID with the message for callback
    app.user_data.setdefault("fav_confirmations", {})
    app.user_data["fav_confirmations"][confirmation_message.message_id] = character_id

@app.on_callback_query(filters.regex(r"^fav_(yes|no)_.+"))
async def handle_fav_confirmation(client: Client, callback_query):
    data_parts = callback_query.data.split("_")

    # Validate data format
    if len(data_parts) < 3:
        logging.error("Invalid callback data format")
        await callback_query.answer("Invalid data received.")
        return
    
    action = data_parts[1]
    character_id = "_".join(data_parts[2:])  # Reconstruct character ID

    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await callback_query.answer("😔 **You haven't seized any characters yet.**")
        return

    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        logging.error(f"Character ID {character_id} not found in user's collection.")
        await callback_query.answer("🙄 **This character is not in your collection.**")
        return

    # Handle "yes" or "no" action
    if action == "yes":
        # Update user's favorite character in the database
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'favorites': [character_id]}}
        )
        await callback_query.message.edit_caption(
            caption=(
                f"🔒 **Locked!** You've chosen `{character['name']}` as your latest favorite character! "
                f"{random.choice(SUCCESS_EMOJIS)}"
            ),
            reply_markup=None  # Disable buttons after confirmation
        )

        # Send the favorite character's image and details to the user's PM
        try:
            # Extract character details
            name = character.get('name', 'Unknown Name')
            anime = character.get('anime', 'Unknown Anime')
            rarity = character.get('rarity', 'Common')
            rarity_emoji, rarity_display = RARITY_EMOJIS.get(rarity, ('', rarity))

            # Send photo with character details to the user’s PM
            await client.send_photo(
                chat_id=user_id,
                photo=character['img_url'],
                caption=(
                    f"🎊 **Congratulations!** You've successfully set **{name}** as your favorite character! "
                    f"{random.choice(SUCCESS_EMOJIS)}\n\n"
                    f"🧃 **Name:** `{name}`\n"
                    f"⚜️ **Anime:** `{anime}`\n"
                    f"🥂 **Rarity:** {rarity_emoji} `{rarity_display}`\n\n"
                    f"Enjoy your time with **{name}** 🥰"
                ),
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Error sending PM to user {user_id}: {e}")

    elif action == "no":
        await callback_query.message.edit_caption(
            caption=f"{random.choice(CANCEL_EMOJIS)} **Operation cancelled.**",
            reply_markup=None  # Disable buttons after cancellation
        )

    logging.info(f"User {user_id} handled favorite confirmation successfully.")
    
@app.on_message(filters.command("unfav"))
async def unfav(client: Client, message):
    user_id = message.from_user.id
    
    # Reset user's favorite in the database
    await user_collection.update_one({'id': user_id}, {'$unset': {'favorites': ''}})
    
    # Generate an exciting message to notify the user
    exciting_message = generate_exciting_message("🎉 Your favorite character has been reset!")
    await message.reply_text(exciting_message)

# Function to add some excitement to the fav command's messages
def generate_exciting_message(base_message: str) -> str:
    return f"{random.choice(ANIMATED_EMOJIS)} {base_message} {random.choice(ANIMATED_EMOJIS)}"
