from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivu import db, collection, user_collection
from shivu import shivuu as app
from shivu import SPECIALGRADE, GRADE1
import asyncio
import random
import time

LOGS_CHANNEL_ID = -1002446048543  # Replace with your actual logs channel ID

backup_collection = db["backup_collection"]

async def send_log_message(log_message: str):
    try:
        await app.send_message(LOGS_CHANNEL_ID, log_message)
    except Exception as e:
        print(f"Failed to send log message: {e}")
        
async def backup_characters(user_id):
    user = await user_collection.find_one({'id': user_id})
    if user:
        await backup_collection.insert_one({'user_id': user_id, 'characters': user['characters'], 'timestamp': time.time()})

async def restore_characters(user_id, timestamp):
    backup = await backup_collection.find_one({'user_id': user_id, 'timestamp': {'$lte': timestamp}}, sort=[('timestamp', -1)])
    if backup:
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': backup['characters']}})
        return True
    return False

async def update_user_rank(user_id):
    # Implementation for updating user rank
    pass

async def send_action_notification(message: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reverse", callback_data=f"reverse_{time.time()}")]
    ])
    for user_id in SPECIALGRADE:
        try:
            await app.send_message(user_id, message, reply_markup=keyboard)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

async def give_character_batch(receiver_id, character_ids):
    # Fetch the characters based on the provided IDs
    characters = await collection.find({'id': {'$in': character_ids}}).to_list(length=len(character_ids))
    
    if characters:
        try:
            # Update the user's character list with the new characters
            await user_collection.update_one(
                {'id': receiver_id},
                {'$push': {'characters': {'$each': characters}}}
            )
            await update_user_rank(receiver_id)

            # Prepare a success message summarizing the characters added
            character_names = ', '.join([char['name'] for char in characters])
            await notify_user(receiver_id, f"🎉 You have received new characters: {character_names}!\n\nTotal characters: {len(characters)} added! 🚀")
            return characters

        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("⚠️ <b>Some characters not found.</b> Please check the character IDs provided.")

@app.on_message(filters.command(["daan"]) & filters.reply)
async def give_character_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE and str(message.from_user.id) not in GRADE1:
        await message.reply_text("This command can only be used by Special Grade and Grade 1 sorcerers.")
        return

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give a character!")
        return

    try:
        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id
        receiver_first_name = message.reply_to_message.from_user.first_name

        # Ensure the bot has interacted with the receiver
        try:
            await client.get_chat(receiver_id)
        except Exception as e:
            await message.reply_text(f"Error interacting with the receiver: {e}")
            return

        # Backup user characters before giving
        await backup_characters(receiver_id)

        character = await give_character_batch(receiver_id, [character_id])

        if character:
            img_url = character[0]['img_url']
            user_link = f"[{receiver_first_name}](tg://user?id={receiver_id})"
            caption = (
                f"Successfully Given To The Bhikari {user_link}\n"
                f"Information As Follows\n"
                f" ✅ Rarity: {character[0]['rarity']}\n"
                f"🫂 Anime: {character[0]['anime']}\n"
                f"💕 Name: {character[0]['name']}\n"
                f"🍿 ID: {character[0]['id']}"
            )
            await message.reply_photo(photo=img_url, caption=caption)

            # Send notification to SPECIALGRADE users
            notification_message = (
                f"Action: Give Character\n"
                f"Given by: {message.from_user.first_name}\n"
                f"Receiver: {user_link}\n"
                f"Character ID: {character[0]['id']}"
            )
            await send_action_notification(notification_message)
            # Send log to logs channel
            log_message = (
                f"📝 <b>Character Given</b>\n\n"
                f"👤 <b>By:</b> {message.from_user.first_name}\n"
                f"🎁 <b>Receiver:</b> [{receiver_first_name}](tg://user?id={receiver_id})\n"
                f"🍿 <b>Character ID:</b> {character[0]['id']}\n"
                                )
            await send_log_message(log_message)

    except IndexError:
        await message.reply_text("Please provide a character ID.")
    except ValueError as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in give_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

@app.on_message(filters.command(["kill"]) & filters.reply)
async def remove_character_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE and str(message.from_user.id) not in GRADE1:
        await message.reply_text("This command can only be used by Special Grade and Grade 1 sorcerers.")
        return

    try:
        if not message.reply_to_message:
            await message.reply_text("You need to reply to a user's message to remove a character!")
            return

        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id

        # Ensure the bot has interacted with the receiver
        try:
            await client.get_chat(receiver_id)
        except Exception as e:
            await message.reply_text(f"Error interacting with the receiver: {e}")
            return

        # Backup user characters before removing
        await backup_characters(receiver_id)

        character = await collection.find_one({'id': character_id})

        if character:
            await user_collection.update_one({'id': receiver_id}, {'$pull': {'characters': {'id': character_id}}})

            await update_user_rank(receiver_id)  # Update user rank after removing character

            await message.reply_text(f"Successfully removed character ID {character_id} from user {receiver_id}.")

            # Send notification to SPECIALGRADE users
            notification_message = (
                f"Action: Remove Character\n"
                f"Removed by: {message.from_user.first_name}\n"
                f"Receiver ID: {receiver_id}\n"
                f"Character ID: {character_id}"
            )
            await send_action_notification(notification_message)
            # Send log to logs channel
            log_message = (
                f"❌ <b>Character Removed</b>\n\n"
                f"👤 <b>By:</b> {message.from_user.first_name}\n"
                f"🎯 <b>From User:</b> {receiver_id}\n"
                f"🍿 <b>Character ID:</b> {character_id}\n"
            )
            await send_log_message(log_message)
        else:
            await message.reply_text("Character not found.")
    except (IndexError, ValueError) as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in remove_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

@app.on_message(filters.command(["given"]))
async def random_characters_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE and str(message.from_user.id) not in GRADE1:
        await message.reply_text("This command can only be used by Special Grade and Grade 1 sorcerers.")
        return

    try:
        if not message.reply_to_message:
            await message.reply_text("You need to reply to a user's message to give characters!")
            return

        if len(message.command) < 2:
            await message.reply_text("Please provide the amount of random characters to give.")
            return

        try:
            amount = int(message.command[1])
        except ValueError:
            await message.reply_text("Invalid amount. Please provide a valid number.")
            return

        amount = min(amount, 2000)

        receiver_id = message.reply_to_message.from_user.id

        # Ensure the bot has interacted with the receiver
        try:
            await client.get_chat(receiver_id)
        except Exception as e:
            await message.reply_text(f"Error interacting with the receiver: {e}")
            return

        # Backup user characters before giving
        await backup_characters(receiver_id)

        all_characters_cursor = collection.find({})
        all_characters = await all_characters_cursor.to_list(length=None)

        # Check for 'id' field presence
        all_characters = [character for character in all_characters if 'id' in character]

        if len(all_characters) < amount:
            await message.reply_text("Not enough characters available to give.")
            return

        random_characters = random.sample(all_characters, amount)
        random_character_ids = [character['id'] for character in random_characters]

        # Process tasks in batches to optimize performance
        batch_size = 100  # Adjust batch size as needed
        tasks = [
            give_character_batch(receiver_id, random_character_ids[i:i + batch_size])
            for i in range(0, amount, batch_size)
        ]

        await asyncio.gather(*tasks)

        user_link = f"[{message.reply_to_message.from_user.first_name}](tg://user?id={receiver_id})"

        # Send summary notification to the owner
        notification_message = (
            f"Action: Give Random Characters\n"
            f"Given by: {message.from_user.first_name}\n"
            f"Amount: {amount}\n"
            f"Receiver: {user_link}\n"
        )
        await send_action_notification(notification_message)
        # Send log to logs channel
        log_message = (
            f"📝 <b>Character Given</b>\n\n"
            f"👤 <b>By:</b> {message.from_user.first_name}\n"
            f"🎁 <b>Receiver:</b> [{receiver_first_name}](tg://user?id={receiver_id})\n"
            f"🍿 <b>Character ID:</b> {character[0]['id']}\n"
         )
        await send_log_message(log_message)
        await message.reply_text(f"Success! {amount} character(s) added to {user_link}'s collection.")
    except Exception as e:
        print(f"Error in random_characters_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

@app.on_callback_query(filters.regex(r'^reverse_\d+\.\d+$'))
async def reverse_action(client, callback_query: CallbackQuery):
    timestamp = float(callback_query.data.split("_")[1])
    target_id = callback_query.message.chat.id

    if str(callback_query.from_user.id) in SPECIALGRADE:
        restored = await restore_characters(target_id, timestamp)
        if restored:
            await callback_query.edit_message_text("The action has been reversed.")
        else:
            await callback_query.answer("Failed to reverse the action or no backup found.", show_alert=True)
    else:
        await callback_query.answer("You don't have permission to reverse actions.", show_alert=True)
        
