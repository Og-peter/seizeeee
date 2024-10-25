import urllib.request
import os
from pymongo import ReturnDocument
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, user_collection
from shivu import shivuu as bot
from pyrogram import Client, filters, types as t
import random

async def check_character(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Usage: /check <character_id> 🎯')
            return
            
        character_id = args[0]
        character = await collection.find_one({'id': character_id})
        
        if character:
            global_count = await user_collection.count_documents({'characters.id': character['id']})
            
            # Create animated loading message
            loading_message = await update.message.reply_text("🔍 Searching for the character... Please wait! ⏳")
            
            # Update message with the character info and emojis
            response_message = (
                f"<b>🌟✨ Meet Your Special Character ✨🌟</b>\n\n"
                f"<b>ID:</b> {character['id']} 🔢\n"
                f"<b>Name:</b> {character['name']} 💖\n"
                f"<b>Anime:</b> {character['anime']} 🎬\n"
                f"<b>Rarity:</b> {character['rarity']} 🏅\n"
                f"<b>✨ Description:</b> {character.get('description', 'No description available.')} 📜"
            )
            
            # Add animated emoji labels for special cases
            special_cases = {
                '🐇': "Bunny 🐇",
                '👩‍🏫': "Teacher 📚",
                '🎒': "Student 🎒",
                '👘': "Kimono 👘",
                '🏖': "Summer Event 🏖",
                '🎄': "Christmas Event 🎄",
                '🧹': "Maid Role 🧹",
                '🥻': "Saree Outfit 🥻",
                '🩺': "Nurse Role 🩺",
                '❄️': "Winter Event ❄️"
            }
            
            for emoji, label in special_cases.items():
                if emoji in character['name']:
                    response_message += f"\n\n✨ <b>Special:</b> {label} ✨"
                    break  # Stop checking after finding the first match

            # Inline keyboard with dynamic emoji progress bar and total owners
            keyboard = InlineKeyboardMarkup=[
                [InlineKeyboardButton(f"🌍 Total Owners: {global_count}", callback_data=f"slaves_{character['id']}_{global_count}")],
                 InlineKeyboardButton("📖 More Info", callback_data=f"info_{character['id']}")],
                [InlineKeyboardButton("❤️ Favorite", callback_data=f"favorite_{character['id']}")]
            ]
            
            # Simulate a delay for effect
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=character['img_url'],
                caption=response_message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            await loading_message.delete()
        else:
            await update.message.reply_text('❌ Invalid character ID. Please check and try again!')

    except Exception as e:
        await update.message.reply_text(f'⚠️ Error: {str(e)}. Please try again later.')

# Random character feature to surprise users with a random character
async def random_character(update: Update, context: CallbackContext) -> None:
    try:
        # Get a random character from the collection
        characters_count = await collection.count_documents({})
        random_skip = random.randint(0, characters_count - 1)
        random_character = await collection.find_one(skip=random_skip)

        if random_character:
            global_count = await user_collection.count_documents({'characters.id': random_character['id']})
            response_message = (
                f"<b>🎲 Random Character 🎲</b>\n\n"
                f"<b>ID:</b> {random_character['id']}\n"
                f"<b>Name:</b> {random_character['name']} 💫\n"
                f"<b>Anime:</b> {random_character['anime']} 🎥\n"
                f"<b>Rarity:</b> {random_character['rarity']} 🌟"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🌍 Total Owners", callback_data=f"slaves_{random_character['id']}_{global_count}")],
                [InlineKeyboardButton("📖 More Info", callback_data=f"info_{random_character['id']}")]
            ])

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=random_character['img_url'],
                caption=response_message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text('❌ Could not retrieve a random character.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# Handle callback queries for favorites, info, and owners
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')

    if data[0] == 'slaves':
        character_id = data[1]
        global_count = data[2]
        await query.answer(f"🌍 Total Characters Owned: {global_count}.", show_alert=True)

    elif data[0] == 'info':
        character_id = data[1]
        character = await collection.find_one({'id': character_id})

        if character:
            detailed_info = (
                f"<b>Name:</b> {character['name']} 💫\n"
                f"<b>Anime:</b> {character['anime']} 🎥\n"
                f"<b>Rarity:</b> {character['rarity']} 🌟\n"
                f"<b>Description:</b> {character.get('description', 'Description unavailable.')}\n"
                f"<b>Global Seizure Count:</b> {await user_collection.count_documents({'characters.id': character_id})} 🌍"
            )
            await query.edit_message_caption(
                caption=detailed_info,
                parse_mode='HTML'
            )
        else:
            await query.answer("Character information not available.", show_alert=True)

    elif data[0] == 'favorite':
        character_id = data[1]
        user_id = query.from_user.id
        
        # Add favorite functionality
        user_favorites = await user_collection.find_one({'user_id': user_id})
        if user_favorites and 'favorites' in user_favorites:
            if character_id in user_favorites['favorites']:
                await query.answer("❤️ Already in your favorites!", show_alert=True)
            else:
                await user_collection.update_one(
                    {'user_id': user_id},
                    {'$push': {'favorites': character_id}},
                    upsert=True
                )
                await query.answer("❤️ Character added to favorites!", show_alert=True)
        else:
            await user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'favorites': [character_id]}},
                upsert=True
            )
            await query.answer("❤️ Character added to favorites!", show_alert=True)

# Register the handlers
CHECK_HANDLER = CommandHandler('check', check_character, block=False)
RANDOM_HANDLER = CommandHandler('random', random_character, block=False)

# Add the handlers to the bot
application.add_handler(CHECK_HANDLER)
application.add_handler(RANDOM_HANDLER)
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern='(slaves_|info_|favorite_)', block=False))
