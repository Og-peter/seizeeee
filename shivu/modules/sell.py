from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, user_collection
import random

# Emoji animations for added engagement
ANIMATED_EMOJIS = ['✨', '🎉', '💫', '🌟', '🔥', '🌀', '🎇', '💖', '🎆', '💥', '🌈']
SUCCESS_EMOJIS = ['✅', '✔️', '🆗', '🎯', '🏅']
CANCEL_EMOJIS = ['❌', '🚫', '⚠️', '🔴', '🚷']

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

@app.on_message(filters.command("buy"))
async def buy(client: Client, message):
    user_id = message.from_user.id

    # Check if command has a character ID
    if len(message.command) < 2:
        await message.reply_text(
            f'{random.choice(CANCEL_EMOJIS)} **Invalid usage!**\n'
            f'Use `/buy (waifu_id)` to buy a waifu.\n'
            f'**Example:** `/buy 15`.'
        )
        return

    character_id = message.command[1]

    # Fetch user data from database
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text('😔 **You need to start your collection first!**')
        return

    # Check if user already owns the character
    if any(str(c.get('id')) == character_id for c in user.get('characters', [])):
        await message.reply_text('🤔 **You already own this character!**')
        return

    # Fetch character details from some external data source (example dictionary here)
    character = await fetch_character_data(character_id)
    if not character:
        await message.reply_text('😞 **Character not found.**')
        return

    # Calculate cost based on rarity
    rarity = character.get('rarity', 'Common')
    rarity_emoji, rarity_display = RARITY_EMOJIS.get(rarity, ('', rarity))
    cost = calculate_buy_cost(rarity)

    # Send confirmation message with inline buttons
    confirmation_message = await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🛍️ **ᴄᴏɴғɪʀᴍ ʏᴏᴜʀ ᴘᴜʀᴄʜᴀsᴇ** 🛍️\n\n"
            f"🫧 **ɴᴀᴍᴇ:** `{character.get('name', 'Unknown Name')}`\n"
            f"⛩️ **ᴀɴɪᴍᴇ:** `{character.get('anime', 'Unknown Anime')}`\n"
            f"🥂 **ʀᴀʀɪᴛʏ:** {rarity_emoji} `{rarity_display}`\n"
            f"💰 **ᴄᴏsᴛ:** `{cost} tokens`\n\n"
            "⚜️ **ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 ᴄᴏɴғɪʀᴍ", callback_data=f"buy_yes_{character_id}_{cost}"),
                InlineKeyboardButton("🔴 ᴄᴀɴᴄᴇʟ", callback_data=f"buy_no_{character_id}")
            ]
        ])
    )

    # Store confirmation details for callback
    app.user_data.setdefault("buy_confirmations", {})
    app.user_data["buy_confirmations"][confirmation_message.message_id] = character_id

@app.on_callback_query(filters.regex(r"^buy_(yes|no)_.+"))
async def handle_buy_confirmation(client: Client, callback_query):
    data_parts = callback_query.data.split("_")

    # Validate data format
    if len(data_parts) < 3:
        await callback_query.answer("Invalid data received.")
        return
    
    action = data_parts[1]
    character_id = data_parts[2]
    cost = int(data_parts[3]) if action == "yes" else 0  # Cost only relevant if confirmed

    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer("😔 **Start your collection first!**")
        return

    # Handle "yes" or "no" action
    if action == "yes":
        # Check if user has enough tokens
        if user.get('tokens', 0) < cost:
            await callback_query.answer("❌ **Not enough tokens!**")
            return

        # Fetch character details again for consistency
        character = await fetch_character_data(character_id)
        if not character:
            await callback_query.answer("😞 **Character not found.**")
            return

        # Add character to user's collection and deduct tokens
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': character}, '$inc': {'tokens': -cost}}
        )

        # Notify user of successful purchase
        await callback_query.message.edit_caption(
            caption=(
                f"{random.choice(SUCCESS_EMOJIS)} **Congratulations!** "
                f"You have successfully bought `{character.get('name', 'Unknown Name')}` "
                f"for `{cost}` tokens."
            ),
            reply_markup=None  # Disable buttons after confirmation
        )

    elif action == "no":
        await callback_query.message.edit_caption(
            caption=f"{random.choice(CANCEL_EMOJIS)} **Purchase cancelled.**",
            reply_markup=None  # Disable buttons after cancellation
        )

# Function to calculate buy cost based on rarity
def calculate_buy_cost(rarity: str) -> int:
    # Cost values based on rarity levels
    cost_values = {
        '𝘾𝙊𝙈𝙈𝙊𝙉': 1000,
        '𝙈𝙀𝘿𝙄𝙐𝙈': 2000,
        '𝘾𝙃𝙄𝘽𝙄': 5000,
        '𝙍𝘼𝙍𝙀': 2500,
        '𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔': 15000,
        '𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀': 10000,
        '𝙋𝙍𝙀𝙈𝙄𝙐𝙈': 12500,
        '𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉': 20000,
    '𝙀𝙓𝙊𝙏𝙄𝘾': 15000,
    '𝘼𝙎𝙏𝙍𝘼𝙇': 25000,
    '𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀': 30000
}
    return cost_values.get(rarity, 1000)  # Default cost for unknown rarity
