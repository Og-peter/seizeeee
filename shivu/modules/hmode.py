from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivu import collection, user_collection, shivuu as app
import math
from html import escape 
import random
from itertools import groupby

# Global dictionary to store user data
user_data = {}

async def hmode(client, message):
    user_id = message.from_user.id
    user_data[user_id] = user_id  # Store the user ID in the global user_data

    keyboard = [
        [
            InlineKeyboardButton("🧩sᴏʀᴛ ʙʏ ʀᴀʀɪᴛʏ", callback_data="sort_rarity"),
        ],
        [InlineKeyboardButton("🎏ʀᴇsᴇᴛ ᴘʀᴇғᴇʀᴇɴᴄᴇs", callback_data="reset_preferences")],
        [InlineKeyboardButton("🧧ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("ʏᴏᴜ ᴄᴀɴ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ʜᴀʀᴇᴍ ɪɴᴛᴇʀғᴀᴄᴇ ᴜsɪɴɢ ᴛʜᴇsᴇ ʙᴜᴛᴛᴏɴs:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r'^sort_'))
async def hmode_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    if user_id != hmode_user_id:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    if data == "close":
        await callback_query.message.delete()
        return

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer("ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ʟᴏᴏᴛᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀs ʏᴇᴛ.", show_alert=True)
        return

    if data == "sort_rarity":
        await send_rarity_preferences(callback_query)

async def send_rarity_preferences(callback_query: CallbackQuery):
    rarity_order = [
        "⚪️ Common",
        "🔮 Limited Edition",
        "🫧 Premium",
        "🥵 Cosplay",
        "💮 Exclusive",
        "👶 Chibi",
        "🟡 Legendary",
        "🟠 Rare",
        "🔵 Medium",
        "💠 Cosmic",
        "🧿 Supreme"
        
    ]
    keyboard = [[InlineKeyboardButton(rarity, callback_data=f"rarity_{rarity}")] for rarity in rarity_order]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.edit_text("🎴ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʀᴀʀɪᴛʏ", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r'^rarity_'))
async def rarity_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    if user_id != hmode_user_id:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    if data.startswith("rarity_"):
        rarity = data.split("_")[1]
        await user_collection.update_one({'id': user_id}, {'$set': {'rarity_preference': rarity}})
        await callback_query.message.edit_text("ʜᴀʀᴇᴍ ɪɴᴛᴇʀғᴀᴄᴇ ᴄʜᴀɴɢᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ")
        await harem(client, callback_query.message)

@app.on_callback_query(filters.regex(r'reset_preferences'))
async def reset_preferences(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    hmode_user_id = user_data.get(user_id)

    if user_id != hmode_user_id:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'rarity_preference': ''}})
    await callback_query.message.edit_text("ʏᴏᴜʀ ʀᴀʀɪᴛʏ ᴘʀᴇғᴇʀᴇɴᴄᴇs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇsᴇᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!")
    await harem(client, callback_query.message)

@app.on_message(filters.command("hmode"))
async def hmode_command(client, message):
    await hmode(client, message)

@app.on_message(filters.command("reset_preferences"))
async def reset_preferences_command(client, message):
    await reset_preferences(client, message)
    
