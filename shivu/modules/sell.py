from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, user_collection
import logging
import random

# Emoji animations for a more engaging user experience
ANIMATED_EMOJIS = ['✨', '🎉', '💫', '🌟', '🔥', '🌀', '🎇', '💖', '🎆', '💥', '🌈']
SUCCESS_EMOJIS = ['✅', '✔️', '🆗', '🎯', '🏅']
CANCEL_EMOJIS = ['❌', '🚫', '⚠️', '🔴', '🚷']

# Dictionary for rarity emojis and colors
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

@app.on_message(filters.command("sell"))
async def sell(client: Client, message):
    user_id = message.from_user.id

    # Check if command has a character ID
    if len(message.command) < 2:
        await message.reply_text(
            f'{random.choice(CANCEL_EMOJIS)} **Invalid usage!**\n'
            f'Use `/sell (waifu_id)` to sell a waifu.\n'
            f'**Example:** `/sell 32`.'
        )
        return

    character_id = message.command[1]

    # Fetch user data from database
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await message.reply_text('😔 **You haven\'t seized any characters yet!**')
        return

    # Find the character in user's collection
    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        await message.reply_text('🙄 **This character is not in your harem!**')
        return

    # Calculate sale value based on rarity
    rarity = character.get('rarity', '𝘾𝙊𝙈𝙈𝙊𝙉')  # Default to 'Common' if not found
    rarity_emoji, rarity_display = RARITY_EMOJIS.get(rarity, ('', rarity))
    sale_value = calculate_sale_value(rarity)  # Calculate based on rarity

    # Send character photo with confirmation message and inline buttons
    confirmation_message = await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"💸 **ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇʟʟ ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ?** 💸\n\n"
            f"🫧 **ɴᴀᴍᴇ:** `{character.get('name', 'Unknown Name')}`\n"
            f"⛩️ **ᴀɴɪᴍᴇ:** `{character.get('anime', 'Unknown Anime')}`\n"
            f"🥂 **ʀᴀʀɪᴛʏ:** {rarity_emoji} `{rarity_display}`\n"
            f"💰 **ᴄᴏɪɴ ᴠᴀʟᴜᴇ:** `{sale_value} coins`\n\n"
            "⚜️ **ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 ᴄᴏɴғɪʀᴍ", callback_data=f"sell_yes_{character_id}_{sale_value}"),
                InlineKeyboardButton("🔴 ᴄᴀɴᴄᴇʟ", callback_data=f"sell_no_{character_id}")
            ]
        ])
    )

    # Store confirmation details for callback
    app.user_data.setdefault("sell_confirmations", {})
    app.user_data["sell_confirmations"][confirmation_message.message_id] = character_id

@app.on_callback_query(filters.regex(r"^sell_(yes|no)_.+"))
async def handle_sell_confirmation(client: Client, callback_query):
    data_parts = callback_query.data.split("_")

    # Validate data format
    if len(data_parts) < 3:
        logging.error("Invalid callback data format")
        await callback_query.answer("Invalid data received.")
        return
    
    action = data_parts[1]
    character_id = data_parts[2]
    sale_value = int(data_parts[3]) if action == "yes" else 0  # Sale value only needed if confirmed

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
        # Remove character from user's collection and add tokens to balance
        await user_collection.update_one(
            {'id': user_id},
            {
                '$pull': {'characters': {'id': character_id}}, 
                '$inc': {'balance': sale_value, 'tokens': sale_value}  # Add tokens equal to sale value
            }
        )

        # Notify user of successful sale
        await callback_query.message.edit_caption(
            caption=(
                f"{random.choice(SUCCESS_EMOJIS)} **ᴄᴏɴɢʀᴀᴛs!** "
                f"ʏᴏᴜ'ᴠᴇ sᴏʟᴅ `{character.get('name', 'Unknown Name')}` ғᴏʀ `{sale_value}` ᴄᴏɪɴs "
                f"ᴀɴᴅ ʀᴇᴄᴇɪᴠᴇᴅ `{sale_value}` ᴛᴏᴋᴇɴs!"
            ),
            reply_markup=None  # Disable buttons after confirmation
        )

    elif action == "no":
        await callback_query.message.edit_caption(
            caption=f"{random.choice(CANCEL_EMOJIS)} **ᴏᴘᴇʀᴀᴛɪᴏɴ ᴄᴀɴᴄᴇʟʟᴇᴅ.**",
            reply_markup=None  # Disable buttons after cancellation
        )

    logging.info(f"User {user_id} handled sell confirmation successfully.")

# Function to calculate sale value based on rarity
def calculate_sale_value(rarity: str) -> int:
    # Sale values based on rarity levels
    sale_values = {
        '𝘾𝙊𝙈𝙈𝙊𝙉': 2000,
        '𝙈𝙀𝘿𝙄𝙐𝙈': 4000,
        '𝘾𝙃𝙄𝘽𝙄': 10000,
        '𝙍𝘼𝙍𝙀': 5000,
        '𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔': 30000,
        '𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀': 20000,
        '𝙋𝙍𝙀𝙈𝙄𝙐𝙈': 25000,
        '𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉': 40000,
        '𝙀𝙓𝙊𝙏𝙄𝘾': 45000,
        '𝘼𝙎𝙏𝙍𝘼𝙇': 50000,
        '𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀': 60000
    }
 
