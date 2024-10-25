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
        await message.reply_text(
            "🚧 **Active Trade Detected!**\n\n"
            "You’re already engaged in a trade or gift exchange. Please complete it first or use **`/reset`** to clear all pending actions and start fresh."
        )
        return

    await start_trade(sender_id, message)
# Command to initiate a gift
@app.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    # Check if the sender has ongoing transactions
    if await has_ongoing_transaction(sender_id):
        await message.reply_text(
            "⚠️ **Active Transaction Alert!**\n\n"
            "You're currently involved in a trade or gift exchange. Complete it first, or use **`/reset`** to cancel all active transactions."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "💌 **Whoops!**\n\n"
            "To gift a character, please reply to the intended user's message."
        )
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("🚫 You can't gift a character to yourself!")
        return

    if len(message.command) != 2:
        await message.reply_text("❗ **Character ID Missing!**\n\nPlease provide the character ID to proceed with the gift.")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender['characters'] if character.get('id') == character_id), None)

    if not character:
        await message.reply_text("❌ **Character Not Found!**\n\nIt seems you don't own this character.")
        return

    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Confirm Gift ✅", callback_data="confirm_gift")],
            [InlineKeyboardButton("❌ Cancel Gift ❌", callback_data="cancel_gift")]
        ]
    )

    # Construct message with receiver's first name as a clickable link
    message_text = (
        f"🎉 **Confirm Your Gift!**\n\n"
        f"Do you want to send this character to **[{receiver_first_name}](tg://user?id={receiver_id})**?\n\n"
        f"✨ **Character Details**:\n"
        f"   • **Name:** `{character['name']}`\n"
        f"   • **Rarity:** `{character['rarity']}`\n"
        f"   • **Anime:** `{character['anime']}`\n\n"
        f"Click 'Confirm Gift' to proceed or 'Cancel Gift' to stop."
    )

    await message.reply_text(message_text, reply_markup=keyboard)

# Start a trade transaction
async def start_trade(sender_id, message):
    if not message.reply_to_message:
        await message.reply_text(
            "❌ **Incorrect Usage!**\n\n"
            "ℹ️ To initiate a trade, please reply to the user you wish to trade with using:\n\n"
            "`/trade character_id_1 character_id_2`"
        )
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("🚫 You cannot trade with yourself!")
        return

    if await has_ongoing_transaction(receiver_id):
        receiver = await user_collection.find_one({'id': receiver_id})
        await message.reply_text(
            f"⚠️ **Alert!**\n\n"
            f"{receiver.get('first_name')} is currently involved in ongoing deals. "
            "Please ask them to use **`/reset`** to cancel their ongoing transactions."
        )
        return

    if len(message.command) != 3:
        await message.reply_text("⚠️ **Character ID Missing!**\n\nYou need to provide two character IDs!")
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    sender_character = next((character for character in sender['characters'] if character.get('id') == sender_character_id), None)
    receiver_character = next((character for character in receiver['characters'] if character.get('id') == receiver_character_id), None)

    if not sender_character:
        await message.reply_text("❌ **Character Not Found!**\n\nYou don't have the character you're trying to trade.")
        return

    if not receiver_character:
        await message.reply_text("❌ **Character Not Found!**\n\nThe other user doesn't possess the character they're attempting to trade.")
        return

    pending_trades[(sender_id, receiver_id)] = (sender_character, receiver_character)

    # Get rarity emojis for sender and receiver characters
    sender_rarity_emoji = get_rarity_emoji(sender_character['rarity'])
    receiver_rarity_emoji = get_rarity_emoji(receiver_character['rarity'])

    trade_info_message = (
        f"🔄 **Trade Proposal**\n\n"
        f"**You:** {sender_character['name']} {sender_rarity_emoji}\n"
        f"**Trading with:** [{receiver.get('first_name')}](tg://user?id={receiver_id})\n"
        f"**They are offering:** {receiver_character['name']} {receiver_rarity_emoji}\n\n"
        "Please review the trade details and confirm your decision!"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Confirm Trade", callback_data=f"confirm_trade:{sender_id}:{receiver_id}")],
            [InlineKeyboardButton("❌ Cancel Trade", callback_data="cancel_trade")]
        ]
    )

    await message.reply_text(trade_info_message, reply_markup=keyboard)

@app.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("confirm_trade:")))
async def on_trade_callback_query(client, callback_query):
    data = callback_query.data.split(':')
    sender_id = int(data[1])
    receiver_id = int(data[2])

    if callback_query.from_user.id != receiver_id:
        await callback_query.answer("🚫 This trade confirmation is not for you!", show_alert=True)
        return

    if (sender_id, receiver_id) not in pending_trades:
        await callback_query.answer("❌ This trade is no longer available.", show_alert=True)
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

    # Trade completion message
    message_text = (
        "🔄 **Trade Completed!**\n\n"
        f"**🌟 {sender.get('first_name', 'Unknown')}** has traded:\n"
        f"➡️ `{sender_character['name']}` to **[{receiver.get('first_name', 'Unknown')}](tg://user?id={receiver_id})**\n\n"
        f"**🌟 {receiver.get('first_name', 'Unknown')}** has traded:\n"
        f"➡️ `{receiver_character['name']}` to **[{sender.get('first_name', 'Unknown')}](tg://user?id={sender_id})**"
    )

    await callback_query.message.edit_text(message_text)

    # Send private message to sender
    sender_trade_confirmation_message = (
        "✅ **Trade Successful!**\n\n"
        f"**🎉 {receiver.get('first_name', 'Unknown')}** accepted your trade offer!\n\n"
        "ℹ️ **You received:**\n"
        f"**🌟 Name:** `{sender_character['name']}`\n"
        f"**🌟 Rarity:** `{sender_character['rarity']}`\n"
        f"**🌟 Anime:** `{sender_character['anime']}`\n"
    )

    await app.send_photo(sender_id, photo=sender_character['img_url'], caption=sender_trade_confirmation_message)

    await callback_query.answer("✅ Trade confirmed!")

# Callback query handler for rejecting trade transactions
@app.on_callback_query(filters.create(lambda _, __, query: query.data == "cancel_trade"))
async def on_cancel_trade_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id
    trade_found = False

    for (trade_sender_id, receiver_id) in pending_trades.keys():
        if trade_sender_id == sender_id:
            trade_found = True
            break

    if not trade_found:
        await callback_query.answer("🚫 This trade does not belong to you!", show_alert=True)
        return

    del pending_trades[(trade_sender_id, receiver_id)]
    
    # Canceled trade message with advanced formatting
    cancellation_message = (
        "❌ **Trade Canceled!** ❌\n\n"
        f"**🔔 Notification:** The trade you initiated with **[{receiver_id}](tg://user?id={receiver_id})** has been successfully canceled.\n"
        "If you wish to trade again, please initiate a new trade using the `/trade` command!"
    )

    await callback_query.message.edit_text(cancellation_message)

    await callback_query.answer("✅ Trade has been canceled!")

# Callback query handler for gift confirmation
@app.on_callback_query(filters.create(lambda _, __, query: query.data.lower() in ["confirm_gift", "cancel_gift"]))
async def on_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id
    trade_found = False

    for (_sender_id, receiver_id), gift in pending_gifts.items():
        if _sender_id == sender_id:
            trade_found = True
            break

    if not trade_found:
        await callback_query.answer("🚫 This gift does not belong to you!", show_alert=True)
        return

    if callback_query.data.lower() == "confirm_gift":
        sender = await user_collection.find_one({'id': sender_id})
        receiver_id = receiver_id  # Ensure receiver_id is correctly referenced
        receiver_username = gift['receiver_username']
        receiver_first_name = gift['receiver_first_name']
        sender_character = gift['character']

        # Update sender's characters
        sender_characters = sender['characters']
        sender_characters.remove(sender_character)
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender_characters}})

        # Add character to receiver's collection or create a new record
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

        # Gift confirmation message
        message_text = (
            f"🎉 **✨ Gift Completed! ✨** 🎉\n\n"
            f"🍃 **Congratulations, [{sender_first_name}](tg://user?id={sender_id})!**\n\n"
            f"📜 **You received:**\n"
            f" **Name:** `{character_name}`\n"
            f" **Rarity:** {rarity_emoji} `{rarity}`\n"
            f" **Anime:** `{anime_name}`"
        )

        # Send message to receiver's PM
        await app.send_photo(receiver_id, photo=img_url, caption=message_text)

        await callback_query.message.edit_text("🎁 **Gift Successfully Delivered!** 🎁\n\n" + message_text)

    elif callback_query.data.lower() == "cancel_gift":
        del pending_gifts[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌ **Gift Canceled Successfully!** ❌\n\n*You can always gift again!*")

    await callback_query.answer("✅ Action Completed!")

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
  
