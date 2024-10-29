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
            "🚧 **ᴀᴄᴛɪᴠᴇ ᴛʀᴀᴅᴇ ᴅᴇᴛᴇᴄᴛᴇᴅ!**\n\n"
            "Yᴏᴜ'ʀᴇ ᴀʟʀᴇᴀᴅʏ ᴇɴɢᴀɢᴇᴅ ɪɴ ᴀ ᴛʀᴀᴅᴇ ᴏʀ ɢɪꜰᴛ ᴇxᴄʜᴀɴɢᴇ. Pʟᴇᴀsᴇ cᴏᴍᴘʟᴇᴛᴇ ɪᴛ ғɪʀsᴛ ᴏʀ ᴜsᴇ `/reset` ᴛᴏ cʟᴇᴀʀ ᴀʟʟ pᴇɴᴅɪɴɢ ᴀᴄᴛɪᴏɴs ᴀɴᴅ sᴛᴀʀᴛ ғʀᴇsʜ."
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
            "⚠️ **ᴀᴄᴛɪᴠᴇ ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ᴀʟᴇʀᴛ!**\n\n"
            "Yᴏᴜ'ʀᴇ cᴜʀʀᴇɴᴛʟʏ ɪɴᴠᴏʟᴠᴇᴅ ɪɴ ᴀ ᴛʀᴀᴅᴇ ᴏʀ ɢɪғᴛ ᴇxᴄʜᴀɴɢᴇ. Cᴏᴍᴘʟᴇᴛᴇ ɪᴛ ꜰɪʀsᴛ ᴏʀ ᴜsᴇ **`/reset`** ᴛᴏ ᴄʟᴇᴀʀ ᴀʟʟ pᴇɴdɪɴɢ ᴀᴄᴛɪᴏɴs."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "💌 **Wʜᴏᴏᴘs!**\n\n"
            "Tᴏ ɢɪғᴛ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ, ᴘʟᴇᴀsᴇ rᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ɪɴᴛᴇɴᴅᴇᴅ ᴜsᴇʀ's mᴇssᴀɢᴇ."
        )
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("🚫 Yᴏᴜ ᴄᴀɴ'ᴛ ɢɪғᴛ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ yᴏᴜʀsᴇʟғ!")
        return

    if len(message.command) != 2:
        await message.reply_text("❗ **Cʜᴀʀᴀᴄᴛᴇʀ ID Mɪssɪɴɢ!**\n\nPʟᴇᴀsᴇ prᴏvɪdᴇ ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ID ᴛᴏ prᴏcᴇᴇd wɪᴛʜ ᴛʜᴇ ɢɪғᴛ.")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender['characters'] if character.get('id') == character_id), None)

    if not character:
        await message.reply_text("❌ **Cʜᴀʀᴀᴄᴛᴇʀ Nᴏᴛ Fᴏᴜɴᴅ!**\n\nIᴛ sᴇᴇms yᴏᴜ dᴏɴ'ᴛ ᴏᴡɴ tʜɪs cʜᴀʀᴀᴄᴛᴇʀ.")
        return

    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Cᴏɴfɪʀᴍ Gɪғᴛ ✅", callback_data="confirm_gift")],
            [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ Gɪғᴛ ❌", callback_data="cancel_gift")]
        ]
    )

    # Construct message with receiver's first name as a clickable link
    message_text = (
        f"🌬️ **Cᴏɴfɪʀᴍ Yᴏᴜʀ Gɪғᴛ!**\n\n"
        f"Dᴏ yᴏᴜ wᴀɴᴛ tᴏ sᴇɴd tʜɪs cʜᴀʀᴀᴄᴛᴇʀ tᴏ **[{receiver_first_name}](tg://user?id={receiver_id})**?\n\n"
        f"🩵 **Cʜᴀʀᴀᴄᴛᴇʀ Dᴇᴛᴀɪʟs**:\n"
        f"❄️ **Nᴀᴍᴇ:** `{character['name']}`\n"
        f"⚜️ **Rᴀʀɪᴛʏ:** `{character['rarity']}`\n"
        f"⛩️ **ᴀɴɪᴍᴇ:** `{character['anime']}`\n\n"
        f"Click 'Cᴏɴfɪʀᴍ Gɪғᴛ' tᴏ prᴏcᴇᴇd ᴏʀ 'Cᴀɴᴄᴇʟ Gɪғᴛ' tᴏ sᴛᴏp."
    )

    await message.reply_text(message_text, reply_markup=keyboard)
    
# Start a trade transaction
async def start_trade(sender_id, message):
    if not message.reply_to_message:
        await message.reply_text(
            "❌ **ɪɴᴄᴏʀʀᴇᴄᴛ ᴜsᴀɢᴇ!**\n\n"
            "ℹ️ ᴛᴏ ɪɴɪᴛɪᴀᴛᴇ ᴀ ᴛʀᴀᴅᴇ, ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡɪsʜ ᴛᴏ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ᴜsɪɴɢ:\n\n"
            "`/trade character_id_1 character_id_2`"
        )
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("🚫 ʏᴏᴜ ᴄᴀɴ'ᴛ ᴛʀᴀᴅᴇ ᴡɪᴛʜ ʏᴏᴜʀsᴇʟғ!")
        return

    if await has_ongoing_transaction(receiver_id):
        receiver = await user_collection.find_one({'id': receiver_id})
        await message.reply_text(
            f"⚠️ **ᴀʟᴇʀᴛ!**\n\n"
            f"{receiver.get('first_name')} ɪs cᴜʀʀᴇɴᴛʟʏ ɪɴᴠᴏʟᴠᴇᴅ ɪɴ ᴏɴɢᴏɪɴɢ ᴅᴇᴀʟs. "
            "Pʟᴇᴀsᴇ ᴀsᴋ ᴛʜᴇᴍ ᴛᴏ ᴜsᴇ **`/reset`** ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇɪʀ ᴏɴɢᴏɪɴɢ ᴛʀᴀɴsᴀᴄᴛɪᴏɴs."
        )
        return

    if len(message.command) != 3:
        await message.reply_text("⚠️ **ᴄʜᴀʀᴀᴄᴛᴇʀ ID ᴍɪssɪɴɢ!**\n\nYᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴛᴡᴏ ᴄʜᴀʀᴀᴄᴛᴇʀ IDs!")
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    sender_character = next((character for character in sender['characters'] if character.get('id') == sender_character_id), None)
    receiver_character = next((character for character in receiver['characters'] if character.get('id') == receiver_character_id), None)

    if not sender_character:
        await message.reply_text("❌ **ᴄʜᴀʀᴀᴄᴛᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ʏᴏᴜ'ʀᴇ ᴛʀʏɪɴɢ ᴛᴏ ᴛʀᴀᴅᴇ.")
        return

    if not receiver_character:
        await message.reply_text("❌ **ᴄʜᴀʀᴀᴄᴛᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**\n\nTʜᴇ ᴏᴛʜᴇʀ ᴜsᴇʀ ᴅᴏᴇsn't ᴘᴏssᴇss ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛʜᴇʏ'ʀᴇ ᴀttᴇᴍᴘᴛɪɴɢ ᴛᴏ ᴛʀᴀᴅᴇ.")
        return

    pending_trades[(sender_id, receiver_id)] = (sender_character, receiver_character)

    # Get rarity emojis for sender and receiver characters
    sender_rarity_emoji = get_rarity_emoji(sender_character['rarity'])
    receiver_rarity_emoji = get_rarity_emoji(receiver_character['rarity'])

    trade_info_message = (
        f"🔄 **ᴛʀᴀᴅᴇ ᴘʀᴏᴘᴏsᴀʟ**\n\n"
        f"**Yᴏᴜ:** {sender_character['name']} {sender_rarity_emoji}\n"
        f"**ᴛʀᴀᴅɪɴɢ ᴡɪᴛʜ:** [{receiver.get('first_name')}](tg://user?id={receiver_id})\n"
        f"**ᴛʜᴇʏ ᴀʀᴇ ᴏғғᴇʀɪɴɢ:** {receiver_character['name']} {receiver_rarity_emoji}\n\n"
        "Pʟᴇᴀsᴇ ʀᴇvɪᴇw ᴛʜᴇ ᴛʀᴀᴅᴇ ᴅᴇᴛᴀɪʟs ᴀɴᴅ ᴄᴏɴғɪʀᴍ ʏᴏᴜʀ dᴇcɪsɪᴏn!"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Cᴏɴғɪʀᴍ ᴛʀᴀᴅᴇ", callback_data=f"confirm_trade:{sender_id}:{receiver_id}")],
            [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ ᴛʀᴀᴅᴇ", callback_data="cancel_trade")]
        ]
    )

    await message.reply_text(trade_info_message, reply_markup=keyboard)

@app.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("confirm_trade:")))
async def on_trade_callback_query(client, callback_query):
    data = callback_query.data.split(':')
    sender_id = int(data[1])
    receiver_id = int(data[2])

    if callback_query.from_user.id != receiver_id:
        await callback_query.answer("🚫 ᴛʜɪs ᴛʀᴀᴅᴇ ᴄᴏɴғɪʀᴍᴀᴛɪᴏɴ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ!", show_alert=True)
        return

    if (sender_id, receiver_id) not in pending_trades:
        await callback_query.answer("❌ ᴛʜɪs ᴛʀᴀᴅᴇ ɪs ɴᴏ ʟᴏɴɢᴇʀ ᴀᴠᴀɪʟᴀʙʟᴇ.", show_alert=True)
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
        "🔄 **ᴛʀᴀᴅᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n"
        f"**🌟 {sender.get('first_name', 'Unknown')}** ʜᴀs ᴛʀᴀᴅᴇᴅ:\n"
        f"➡️ `{sender_character['name']}` ᴛᴏ **[{receiver.get('first_name', 'Unknown')}](tg://user?id={receiver_id})**\n\n"
        f"**🌟 {receiver.get('first_name', 'Unknown')}** ʜᴀs ᴛʀᴀᴅᴇᴅ:\n"
        f"➡️ `{receiver_character['name']}` ᴛᴏ **[{sender.get('first_name', 'Unknown')}](tg://user?id={sender_id})**\n\n"
        "✨ ᴇᴠᴇʀʏᴏɴᴇ ᴡɪɴs! ʙᴏᴛʜ ᴘʟᴀʏᴇʀs ɢᴀɪɴ ɴᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀs!"
    )

    await callback_query.message.edit_text(message_text)

    # Send private message to sender
    sender_trade_confirmation_message = (
        "✅ **ᴛʀᴀᴅᴇ sᴜᴄᴄᴇssғᴜʟ!**\n\n"
        f"**💐 {receiver.get('first_name', 'Unknown')}** ᴀᴄᴄᴇᴘᴛᴇᴅ ʏᴏᴜʀ ᴛʀᴀᴅᴇ ᴏғғᴇʀ!\n\n"
        "ℹ️ **Yᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ:**\n"
        f"**🌿 Nᴀᴍᴇ:** `{sender_character['name']}`\n"
        f"**🌋 Rᴀʀɪᴛʏ:** `{sender_character['rarity']}`\n"
        f"**⛩️ Aɴɪᴍᴇ:** `{sender_character['anime']}`\n"
        "😈 ʜᴀʜᴀʜᴀ! ʏᴏᴜ'ʀᴇ ɴᴏᴡ ᴏᴍɴɪᴘᴏᴛᴇɴᴛ!"
    )

    await app.send_photo(sender_id, photo=sender_character['img_url'], caption=sender_trade_confirmation_message)

    await callback_query.answer("✅ ᴛʀᴀᴅᴇ ᴄᴏɴғɪʀᴍᴇᴅ!")

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
        await callback_query.answer("🚫 ᴛʜɪs ᴛʀᴀᴅᴇ ᴅᴏᴇs ɴᴏᴛ ʙᴇʟᴏɴɢ ᴛᴏ ʏᴏᴜ!", show_alert=True)
        return

    del pending_trades[(trade_sender_id, receiver_id)]
    
    # Canceled trade message with advanced formatting
    cancellation_message = (
        "❌ **ᴛʀᴀᴅᴇ ᴄᴀɴᴄᴇʟᴇᴅ!** ❌\n\n"
        f"**🔔 ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ:** ᴛʜᴇ ᴛʀᴀᴅᴇ ʏᴏᴜ ɪɴɪᴛɪᴀᴛᴇᴅ ᴡɪᴛʜ **[{receiver_id}](tg://user?id={receiver_id})** ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴄᴀɴᴄᴇʟᴇᴅ.\n"
        "😢 ᴅᴏɴ'ᴛ ᴡᴏʀʀʏ! ɪᴅɪᴏᴛs ᴄᴀɴ'ᴛ ᴍᴀᴋᴇ ᴛʜɪs ᴡᴏʀᴋ.\n"
        "ɪғ ʏᴏᴜ ᴡɪsʜ ᴛᴏ ᴛʀᴀᴅᴇ ᴀɢᴀɪɴ, ᴘʟᴇᴀsᴇ ɪɴɪᴛɪᴀᴛᴇ ᴀ ɴᴇᴡ ᴛʀᴀᴅᴇ ᴜsɪɴɢ ᴛʜᴇ `/trade` ᴄᴏᴍᴍᴀɴᴅ!"
    )

    await callback_query.message.edit_text(cancellation_message)

    await callback_query.answer("✅ ᴛʀᴀᴅᴇ ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟᴇᴅ!")
    
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
        await callback_query.answer("🚫 ᴛʜɪs ɢɪғᴛ ᴅᴏᴇs ɴᴏᴛ ʙᴇʟᴏɴɢ ᴛᴏ ʏᴏᴜ!", show_alert=True)
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
            f"🥂 **ɢɪғᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ!** 🎉\n\n"
            f"❄️ **Cᴏngrᴀᴛᴜʟᴀᴛɪᴏɴs, [{sender_first_name}](tg://user?id={sender_id})!**\n\n"
            f"🌋 **Yᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ:**\n"
            f" **Nᴀᴍᴇ:** `{character_name}`\n"
            f" **Rᴀʀɪᴛʏ:** {rarity_emoji} `{rarity}`\n"
            f" **ᴀɴɪᴍᴇ:** `{anime_name}`\n\n"
            "🌪️ ʏᴏᴜ'ʀᴇ ɴᴏᴡ ᴏᴜᴛ ᴏғ ᴏᴘᴛɪᴏɴs! ᴡʜᴏᴇᴠᴇʀ sʜɪɴᴏʙᴜ ʙᴇʟɪᴇᴠᴇs ᴛʜᴇ ᴍᴀʟʟ ᴡɪʟʟ ʙᴇ ʏᴏᴜ!"
        )

        # Send message to receiver's PM
        await app.send_photo(receiver_id, photo=img_url, caption=message_text)

        await callback_query.message.edit_text("🎁 **ɢɪғᴛ sᴜᴄᴄᴇssfᴜʟʟʏ dᴇlɪvᴇʀᴇd!** 🎁\n\n" + message_text)

    elif callback_query.data.lower() == "cancel_gift":
        del pending_gifts[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌ **ɢɪғᴛ Cᴀɴᴄᴇʟᴇᴅ sᴜᴄᴄᴇssfᴜʟʟʏ!** ❌\n\n*ʏᴏᴜ ᴄᴀɴ ᴀʟᴡᴀʏs ɢɪғᴛ ᴀɢᴀɪɴ!*")

    await callback_query.answer("✅ ᴀᴄᴛɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇᴅ!")

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
        'Exotic': '🌸',
        'Astral': '🎐',
        'Valentine': '💞'
       }
    return RARITY_EMOJIS.get(rarity_name, f'⚠️ ʀᴀʀɪᴛʏ: {rarity_name}')

# Function to generate trade info message with rarity emojis
def get_trade_info_message(sender_character, receiver_character, sender_rarity_emoji, receiver_rarity_emoji):
    return (
        f"📩 **ᴛʀᴀᴅᴇ RᴇQᴜᴇsᴛ**\n\n"
        f"🔄 **Yᴏᴜ Rᴇᴄᴇɪᴠᴇ:**\n"
        f" **Nᴀᴍᴇ:** `{receiver_character['name']}`\n"
        f" **Rᴀʀɪᴛʏ:** {receiver_rarity_emoji} `{receiver_character['rarity']}`\n"
        f" **ᴀɴɪᴍᴇ:** `{receiver_character['anime']}`\n\n"
        f"➡️ **Yᴏᴜ Gɪᴠᴇ:**\n"
        f" **Nᴀᴍᴇ:** `{sender_character['name']}`\n"
        f" **Rᴀʀɪᴛʏ:** {sender_rarity_emoji} `{sender_character['rarity']}`\n"
        f" **ᴀɴɪᴍᴇ:** `{sender_character['anime']}`\n\n"
        "⚠️ Cʟɪᴄᴋ 'ᴀᴄᴄᴇᴘᴛ' ᴛᴏ ᴀᴄᴄᴇᴘᴛ ᴛʜɪs ᴏғғᴇʀ.\n"
        "❌ Cʟɪᴄᴋ 'ʀᴇjᴇct' ᴛᴏ dᴇclɪɴᴇ."
    )

# Command to reset ongoing transactions
@app.on_message(filters.command("reset"))
async def reset(client, message):
    sender_id = message.from_user.id

    if await has_ongoing_transaction(sender_id):
        pending_trades.clear()
        pending_gifts.clear()
        await message.reply_text("🗑️ **ᴛʀᴀɴsᴀcᴛɪᴏɴ Rᴇsᴇᴛ!**\n\nYᴏᴜʀ ᴏɴɢᴏɪɴɢ ᴛʀᴀᴅᴇ ᴀɴᴅ ɢɪғᴛ ᴛʀᴀɴsᴀcᴛɪᴏɴs ʜᴀᴠᴇ bᴇᴇɴ ʀᴇsᴇᴛ sᴜᴄᴄᴇssfᴜʟʟʏ! 🎉")
    else:
        await message.reply_text("🔍 **ɴᴏ ᴀᴄtɪᴠᴇ ᴛʀᴀɴsᴀcᴛɪᴏɴs!**\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴏɴɢᴏɪɴɢ ᴛʀᴀᴅᴇ ᴏʀ ɢɪғᴛ ᴛʀᴀɴsᴀcᴛɪᴏɴs ᴛᴏ ʀᴇsᴇᴛ.")
