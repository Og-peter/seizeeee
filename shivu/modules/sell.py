from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, user_collection
import logging
import random

# Dictionary for rarity values
RARITY_COIN_MAPPING = {
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

def calculate_sale_value(rarity: str) -> int:
    # Return the value corresponding to the rarity or 0 if not found
    return RARITY_COIN_MAPPING.get(rarity, 0)

@app.on_message(filters.command("sell"))
async def sell(client: Client, message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        await message.reply_text(
            f'{random.choice(CANCEL_EMOJIS)} **Invalid usage!**\n'
            f'Use `/sell (waifu_id)` to sell a waifu.\n'
            f'**Example:** `/sell 32`.'
        )
        return

    character_id = message.command[1]

    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await message.reply_text('😔 **You haven\'t seized any characters yet!**')
        return

    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        await message.reply_text('🙄 **This character is not in your harem!**')
        return

    rarity = character.get('rarity', '𝘾𝙊𝙈𝙈𝙊𝙉')
    sale_value = calculate_sale_value(rarity)

    if sale_value == 0:
        await message.reply_text(f'⚠️ **Sale value not found for rarity `{rarity}`.**')
        return

    await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"💸 **Are you sure you want to sell this character?** 💸\n\n"
            f"🫧 **Name:** `{character.get('name', 'Unknown Name')}`\n"
            f"⛩️ **Anime:** `{character.get('anime', 'Unknown Anime')}`\n"
            f"🥂 **Rarity:** {RARITY_EMOJIS.get(rarity, ('', ''))[1]} `{rarity}`\n"
            f"💰 **Coin Value:** `{sale_value} coins`\n\n"
            "⚜️ **Choose an option:**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Confirm", callback_data=f"sell_yes_{character_id}_{sale_value}"),
                InlineKeyboardButton("🔴 Cancel", callback_data=f"sell_no_{character_id}")
            ]
        ])
    )

@app.on_callback_query(filters.regex(r"^sell_(yes|no)_.+"))
async def handle_sell_confirmation(client: Client, callback_query):
    data_parts = callback_query.data.split("_")
    if len(data_parts) < 4:
        await callback_query.answer("Invalid data received.")
        return

    action = data_parts[1]
    character_id = data_parts[2]
    sale_value = int(data_parts[3]) if action == "yes" else 0

    user_id = callback_query.from_user.id
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await callback_query.answer("😔 **You haven't seized any characters yet.**")
        return

    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        await callback_query.answer("🙄 **This character is not in your collection.**")
        return

    if action == "yes":
        await user_collection.update_one(
            {'id': user_id},
            {
                '$pull': {'characters': {'id': int(character_id)}},
                '$inc': {'balance': sale_value, 'tokens': sale_value}
            }
        )

        await callback_query.message.edit_caption(
            caption=(
                f"{random.choice(SUCCESS_EMOJIS)} **Congrats!** "
                f"You've sold `{character.get('name', 'Unknown Name')}` for `{sale_value}` coins "
                f"and received `{sale_value}` tokens!"
            ),
            reply_markup=None
        )

    elif action == "no":
        await callback_query.message.edit_caption(
            caption=f"{random.choice(CANCEL_EMOJIS)} **Operation cancelled.**",
            reply_markup=None
    )
