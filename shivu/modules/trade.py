from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import user_collection, shivuu as app

pending_trades = {}
pending_gifts = {}

# Command to initiate a trade
@app.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    if await has_ongoing_transaction(sender_id):
        await message.reply_text("You already have ongoing trade or gift transactions. Please complete them or use `/reset` to cancel.")
        return

    await start_trade(sender_id, message)

# Command to initiate a gift
@app.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    # Check if the sender has ongoing transactions
    if await has_ongoing_transaction(sender_id):
        await message.reply_text("You already have ongoing trade or gift transactions. Please complete them or use `/reset` to cancel.")
        return

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to gift a character!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("You can't gift a character to yourself!")
        return

    if len(message.command) != 2:
        await message.reply_text("You need to provide a character ID!")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender['characters'] if character.get('id') == character_id), None)

    if not character:
        await message.reply_text("You don't have this character in your collection!")
        return

    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("ᴄᴏɴғɪʀᴍ ɢɪғᴛ ✅", callback_data="confirm_gift")],
            [InlineKeyboardButton("ᴄᴀɴᴄᴇʟ ɢɪғᴛ ❌", callback_data="cancel_gift")]
        ]
    )

    # Construct message with receiver's first name as a blue link
    message_text = (
        f"Do you really want to gift this character\n"
        f"🎁 Click 'Accept' button to send:\n\n"
        f" **Name:** `{character['name']}`\n"
        f" **Rarity:** `{character['rarity']}`\n"
        f" **Anime:** `{character['anime']}`\n\n"
        f"To: [{receiver_first_name}](tg://user?id={receiver_id})"
    )

    await message.reply_text(message_text, reply_markup=keyboard)

# Start a trade transaction
async def start_trade(sender_id, message):
    if not message.reply_to_message:
        await message.reply_text("❌ Incorrect usage\n\n ℹ️ To start trade, reply the user you want to start trading with:\n\n /trade")
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("You can't trade a character with yourself!")
        return

    if await has_ongoing_transaction(receiver_id):
        receiver = await user_collection.find_one({'id': receiver_id})
        await message.reply_text(f"{receiver.get('first_name')} has ongoing deals. Please use /reset command to cancel ongoing deals.")
        return

    if len(message.command) != 3:
        await message.reply_text("You need to provide two character IDs!")
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    sender_character = next((character for character in sender['characters'] if character.get('id') == sender_character_id), None)
    receiver_character = next((character for character in receiver['characters'] if character.get('id') == receiver_character_id), None)
    
    if not sender_character:
        await message.reply_text("You don't have the character you're trying to trade!")
        return

    if not receiver_character:
        await message.reply_text("The other user doesn't have the character they're trying to trade!")
        return

    pending_trades[(sender_id, receiver_id)] = (sender_character, receiver_character)

    # Get rarity emojis for sender and receiver characters
    sender_rarity_emoji = get_rarity_emoji(sender_character['rarity'])
    receiver_rarity_emoji = get_rarity_emoji(receiver_character['rarity'])

    trade_info_message = get_trade_info_message(sender_character, receiver_character, sender_rarity_emoji, receiver_rarity_emoji)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("ᴄᴏɴғɪʀᴍ ᴛʀᴀᴅᴇ ✅", callback_data=f"confirm_trade:{sender_id}:{receiver_id}")],
            [InlineKeyboardButton("ᴄᴀɴᴄᴇʟ ᴛʀᴀᴅᴇ ❌", callback_data="cancel_trade")]
        ]
    )

    await message.reply_text(trade_info_message, reply_markup=keyboard)

# Callback query handler for trade transactions
@app.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("confirm_trade:")))
async def on_trade_callback_query(client, callback_query):
    data = callback_query.data.split(':')
    sender_id = int(data[1])
    receiver_id = int(data[2])

    if callback_query.from_user.id != receiver_id:
        await callback_query.answer("This is not for you!", show_alert=True)
        return

    if (sender_id, receiver_id) not in pending_trades:
        await callback_query.answer("This trade is no longer available.", show_alert=True)
        return

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    sender_character, receiver_character = pending_trades[(sender_id, receiver_id)]

    del pending_trades[(sender_id, receiver_id)]

    # Exchange characters
    sender_characters = sender['characters']
    sender_characters.remove(sender_character)
    sender_characters.append(receiver_character)
    await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

    receiver_characters = receiver['characters']
    receiver_characters.remove(receiver_character)
    receiver_characters.append(sender_character)
    await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_characters}})

    message_text = (
        f"ℹ️ **Trade Info:**\n\n"
        f"🔃 [{sender.get('first_name', 'Unknown')}](tg://user?id={sender_id}) gave {sender_character['name']} to [{receiver.get('first_name', 'Unknown')}](tg://user?id={receiver_id})\n"
        f"🔃 [{receiver.get('first_name', 'Unknown')}](tg://user?id={receiver_id}) gave {receiver_character['name']} to [{sender.get('first_name', 'Unknown')}](tg://user?id={sender_id})"
    )

    await callback_query.message.edit_text(message_text)

    # Send private message to sender
    sender_trade_confirmation_message = (
        f"✅ [{receiver.get('first_name', 'Unknown')}](tg://user?id={receiver_id}) accepted your offer!\n\n"
        "ℹ **You got:**\n"
        f" **Name:** {sender_character['name']}\n"
        f" **Rarity:** {sender_character['rarity']}\n"
        f" **Anime:** {sender_character['anime']}\n"
    )

    await app.send_photo(sender_id, photo=sender_character['img_url'], caption=sender_trade_confirmation_message)

    await callback_query.answer()

# Callback query handler for rejecting trade transactions
@app.on_callback_query(filters.create(lambda _, __, query: query.data == "cancel_trade"))
async def on_cancel_trade_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id

    for (sender_id, receiver_id) in pending_trades.keys():
        if sender_id == sender_id:
            break
    else:
        await callback_query.answer("This is not for you!", show_alert=True)
        return

    del pending_trades[(sender_id, receiver_id)]
    await callback_query.message.edit_text("❌ **Trade Canceled** ❌")

    await callback_query.answer()


# Callback query handler for gift confirmation
@app.on_callback_query(filters.create(lambda _, __, query: query.data.lower() in ["confirm_gift", "cancel_gift"]))
async def on_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id

    for (_sender_id, receiver_id), gift in pending_gifts.items():
        if _sender_id == sender_id:
            break
    else:
        await callback_query.answer("This is not for you!", show_alert=True)
        return

    if callback_query.data.lower() == "confirm_gift":
        sender = await user_collection.find_one({'id': sender_id})
        receiver_id = receiver_id
        receiver_username = gift['receiver_username']
        receiver_first_name = gift['receiver_first_name']

        sender_character = gift['character']
        sender_characters = sender['characters']
        sender_characters.remove(sender_character)
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

        receiver = await user_collection.find_one({'id': receiver_id})
        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': sender_character}})
        else:
            await user_collection.insert_one({
                'id': receiver_id,
                'username': receiver_username,
                'first_name': receiver_first_name,
                'characters': [sender_character],
            })

        del pending_gifts[(sender_id, receiver_id)]

        # Prepare message components
        sender_first_name = sender.get('first_name', 'Unknown')
        character_name = sender_character.get('name', 'Unknown')
        rarity_emoji = get_rarity_emoji(sender_character['rarity'])
        rarity = sender_character['rarity']
        anime_name = sender_character.get('anime', 'Unknown')
        img_url = sender_character.get('img_url', '')

        message_text = (
            f"🍁 **OwO ᴛʜᴇ ɢɪꜰᴛ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ! [{sender_first_name}](tg://user?id={sender_id})**\n\n"
            f"ℹ **You got:**\n"
            f" **Name:** `{character_name}`\n"
            f" **Rarity:** `{rarity}`\n"
            f" **Anime:** `{anime_name}`"
        )

        # Send message to receiver's PM
        await app.send_photo(receiver_id, photo=img_url, caption=message_text)

        await callback_query.message.edit_text("🎁 **Gift is completed!** 🎁\n\n" + message_text)

    elif callback_query.data.lower() == "cancel_gift":
        del pending_gifts[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌❌ **Successfully Canceled Gift** ❌❌")

    await callback_query.answer()

# Function to check if a user has an ongoing transaction (trade or gift)
async def has_ongoing_transaction(user_id):
    return await has_ongoing_trade(user_id) or await has_ongoing_gift(user_id)

# Function to check if a user has an ongoing trade transaction
async def has_ongoing_trade(user_id):
    return any(sender_id == user_id or receiver_id == user_id for (sender_id, receiver_id) in pending_trades.keys())

# Function to check if a user has an ongoing gift transaction
async def has_ongoing_gift(user_id):
    return user_id in pending_gifts

# Function to get rarity emoji based on rarity name
def get_rarity_emoji(rarity_name):
    RARITY_EMOJIS = {
        'Common': '⚪️',
        'Medium': '🔵',
        'Chibi': '👶',
        'Rare': '🟠',
        'Legendary': '🟡',
        'Exclusive': '💮',
        'Premium': '🫧',
        'Limited Edition': '🔮',
        'Cosmic': '💠',
        'Supreme': '🧿'
    }
    return RARITY_EMOJIS.get(rarity_name, f'Rarity: {rarity_name}')

# Function to generate trade info message with rarity emojis
def get_trade_info_message(sender_character, receiver_character, sender_rarity_emoji, receiver_rarity_emoji):
    return (
        f"ℹ️ **Trade Request !**\n\n"
        f"⚜️ **You get:**\n"
        f" **Name:** {receiver_character['name']}\n"
        f" **Rarity:** {receiver_character['rarity']}\n"
        f" **Anime:** {receiver_character['anime']}\n\n"
        f"🧋 **You give:**\n"
        f" **Name:** {sender_character['name']}\n"
        f" **Rarity:** {sender_character['rarity']}\n"
        f" **Anime:** {sender_character['anime']}\n\n"
        "ℹ Click 'Accept' button to accept this offer\n"
        "Otherwise, click 'Reject' button"
    )
    
# Command to reset ongoing transactions
@app.on_message(filters.command("reset"))
async def reset(client, message):
    sender_id = message.from_user.id

    if await has_ongoing_transaction(sender_id):
        pending_trades.clear()
        pending_gifts.clear()
        await message.reply_text("Your ongoing trade and gift transactions have been reset successfully!")
    else:
        await message.reply_text("You don't have any ongoing trade or gift transactions to reset.")
  
