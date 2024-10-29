from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivu import collection, user_collection, shivuu as app
import math
from html import escape 
import random
from itertools import groupby
from datetime import datetime

# Global dictionary to store user data and timestamps
user_data = {}

async def hmode(client, message):
    user_id = message.from_user.id
    # Store user ID and a timestamp in global user_data
    user_data[user_id] = {"id": user_id, "timestamp": datetime.now()}

    keyboard = [
        [
            InlineKeyboardButton("sᴏʀᴛ ʙʏ ʀᴀʀɪᴛʏ", callback_data="sort_rarity"),
        ],
        [InlineKeyboardButton("ʀᴇsᴇᴛ ᴘʀᴇғᴇʀᴇɴᴄᴇs", callback_data="reset_preferences")],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_photo(
        photo="https://telegra.ph/file/1fc98964f8a467b947853.jpg",
        caption="🎉 **sᴇᴛ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ:**\n\nᴄʜᴏᴏsᴇ ʏᴏᴜᴛ ᴘʀᴇғᴇʀᴇɴᴄᴇs ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ!",
        reply_markup=reply_markup,
    )

@app.on_callback_query(filters.regex(r'^sort_'))
async def hmode_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("🚫 **You are not authorized to use this button.**", show_alert=True)
        return

    # Close handler
    if data == "close":
        await callback_query.message.delete()
        return

    # Fetch user details from the database
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer("⚠️ **You Have Not Seized Any Characters Yet.**", show_alert=True)
        return

    # Sort by rarity
    if data == "sort_rarity":
        await send_rarity_preferences(callback_query)

async def send_rarity_preferences(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    # Fetch characters and sort by rarity (assuming you have a function to do this)
    characters = await get_sorted_characters_by_rarity(user_id)

    if not characters:
        await callback_query.answer("📭 **No characters available to display.**", show_alert=True)
        return

    # Create a formatted message with sorted characters
    message_text = "✨ **Your Characters Sorted By Rarity:**\n\n"
    for character in characters:
        message_text += f"🌟 **Name:** {character['name']}\n"
        message_text += f"💎 **Rarity:** {character['rarity']}\n\n"

    await callback_query.message.reply_text(message_text)

async def get_sorted_characters_by_rarity(user_id):
    """Fetch and sort characters by rarity for a given user."""
    characters = await user_collection.find_one({'id': user_id})
    if characters and 'characters' in characters:
        # Sort by rarity with a custom order
        rarity_order = {
            "Common": 0,
            "Limited Edition": 1,
            "Premium": 2,
            "Exotic": 3,
            "Exclusive": 4,
            "Chibi": 5,
            "Legendary": 6,
            "Rare": 7,
            "Medium": 8,
            "Astral": 9,
            "Valentine": 10
        }
        return sorted(characters['characters'], key=lambda x: rarity_order.get(x['rarity'], 99))  # Default to a high value if rarity not found
    return []

async def send_rarity_preferences(callback_query: CallbackQuery):
    """sᴇɴᴅ ᴜsᴇʀ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴄʜᴏᴏss ᴛʜᴇɪʀ ᴘʀᴇғᴇʀʀᴇᴅ ʀᴀʀɪᴛʏ ᴏғ ᴄʜᴀʀᴀᴄᴛᴇʀs."""
    rarity_order = [
        "⚪️ Common",
        "🔮 Limited Edition",
        "🫧 Premium",
        "🌸 Exotic",
        "💮 Exclusive",
        "👶 Chibi",
        "🟡 Legendary",
        "🟠 Rare",
        "🔵 Medium",
        "🎐 Astral",
        "💞 Valentine"
    ]
    
    # Create a dynamic keyboard with rarity options
    keyboard = [
        [InlineKeyboardButton(f"✨ {rarity} ✨", callback_data=f"rarity_{rarity.split(' ')[-1]}")] for rarity in rarity_order
    ]
    keyboard.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="harem_menu")])  # Back to main menu
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the previous message to prompt user for rarity preference
    await callback_query.message.edit_text(
        "🎴 **ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʀᴀʀɪᴛʏ:**\n\n"
        "sᴇʟᴇᴄᴛ ғʀᴏᴍ ᴛʜᴇ ᴏᴘᴛɪᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ғɪʟᴛᴇʀ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ!",
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r'^rarity_'))
async def rarity_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("🚫 You are not authorized to use this button.", show_alert=True)
        return

    if data.startswith("rarity_"):
        rarity = data.split("_")[1]
        
        # Update user preference in the database
        await user_collection.update_one({'id': user_id}, {'$set': {'rarity_preference': rarity}})

        # Success message with additional feedback
        await callback_query.message.edit_text(
            f"✨ **ʜᴀʀᴇᴍ ɪɴᴛᴇʀғᴀᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ!** ✨\n"
            f"ʏᴏᴜʀ ʀᴀʀɪᴛʏ ᴘʀᴇғᴇʀᴇɴᴄᴇ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ: **{rarity}**\n\n"
            "🔄 ɴᴀᴠɪɢᴀᴛɪɴɢ ʏᴏᴜ ʙᴀᴄᴋ ᴛᴏ ᴛʜᴇ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ..."
        )
        
        # Optionally, add a delay before returning to harem mode for a smoother transition
        await asyncio.sleep(2)  # Adding a brief pause for effect
        await harem(client, callback_query.message)

@app.on_callback_query(filters.regex(r'reset_preferences'))
async def reset_preferences(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("🚫 You are not authorized to use this button.", show_alert=True)
        return

    # Reset user preference in the database
    await user_collection.update_one({'id': user_id}, {'$unset': {'rarity_preference': ''}})
    
    # Enhanced success message
    await callback_query.message.edit_text(
        "🌋 **ʀᴀʀɪᴛʏ ᴘʀᴇғᴇʀᴇɴᴄᴇs ʀᴇsᴇᴛ!** 🌋\n"
        "ʏᴏᴜʀ ᴘʀᴇғᴇʀᴇɴᴄᴇs ʜᴀᴠᴇ ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ. ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ sᴇᴛ ɴᴇᴡ ᴏɴᴇs ᴀɴʏᴛɪᴍᴇ!\n\n"
        "🔄 ʀᴇᴛᴜʀɴɪɴɢ ᴛᴏ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ..."
    )

    # Optional delay for smooth transition
    await asyncio.sleep(2)
    await harem(client, callback_query.message)

@app.on_message(filters.command("hmode"))
async def hmode_command(client, message):
    await hmode(client, message)

@app.on_message(filters.command("reset_preferences"))
async def reset_preferences_command(client, message):
    await reset_preferences(client, message)
