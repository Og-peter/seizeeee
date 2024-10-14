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
           InlineKeyboardButton("🍜 Sort By Rarity", callback_data="sort_rarity"),
        ],
           [InlineKeyboardButton("🌐 Reset Preference", callback_data="reset_preferences")],
           [InlineKeyboardButton("🚮 Close", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await message.reply_photo(
        photo="https://telegra.ph/file/1fc98964f8a467b947853.jpg",
        caption="Set Your Harem Mode:",
        reply_markup=reply_markup,
    )

@app.on_callback_query(filters.regex(r'^sort_'))
async def hmode_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    # Close handler
    if data == "close":
        await callback_query.message.delete()
        return

    # Fetch user details from the database
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer("You Have Not Seized Any Characters Yet.", show_alert=True)
        return

    # Sort by rarity
    if data == "sort_rarity":
        await send_rarity_preferences(callback_query)

async def send_rarity_preferences(callback_query: CallbackQuery):
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
    
    keyboard = [[InlineKeyboardButton(rarity, callback_data=f"rarity_{rarity}")] for rarity in rarity_order]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="harem_menu")])  # Back to main menu
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.edit_text("🎴 Choose Your Preferred Rarity.", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r'^rarity_'))
async def rarity_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    if data.startswith("rarity_"):
        rarity = data.split("_")[1]
        # Update user preference in the database
        await user_collection.update_one({'id': user_id}, {'$set': {'rarity_preference': rarity}})
        
        # Success message and navigating to harem mode again
        await callback_query.message.edit_text("Harem Interface Changed Successfully!")
        await harem(client, callback_query.message)

@app.on_callback_query(filters.regex(r'reset_preferences'))
async def reset_preferences(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    # Authorization check
    if not hmode_user_id or user_id != hmode_user_id["id"]:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    # Reset user preference in the database
    await user_collection.update_one({'id': user_id}, {'$unset': {'rarity_preference': ''}})
    await callback_query.message.edit_text("🌋 Your Rarity Preferences Have Been Reset Successfully!")
    
    # Return to harem mode after reset
    await harem(client, callback_query.message)

@app.on_message(filters.command("hmode"))
async def hmode_command(client, message):
    await hmode(client, message)

@app.on_message(filters.command("reset_preferences"))
async def reset_preferences_command(client, message):
    await reset_preferences(client, message)
