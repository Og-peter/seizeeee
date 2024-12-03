from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivu import collection, user_collection, shivuu as app

# Global dictionary to store user session data
user_data = {}

# Harem command handler
@app.on_message(filters.command("hmode"))
async def hmode_command(client, message):
    user_id = message.from_user.id
    user_data[user_id] = user_id  # Store the user ID for validation

    img_url = "https://example.com/harem_interface.jpg"  # Replace with your actual image URL
    keyboard = [
        [InlineKeyboardButton("🧩 Sort by Rarity", callback_data="sort_rarity")],
        [InlineKeyboardButton("🎏 Reset Preferences", callback_data="reset_preferences")],
        [InlineKeyboardButton("🧧 Close", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_photo(
        img_url,
        caption="🌸 **Harem Interface Settings** 🌸\n\nCustomize your harem interface using the buttons below.",
        reply_markup=reply_markup
    )

# Callback query handler for harem settings
@app.on_callback_query(filters.regex(r'^sort_|^reset_preferences|^close'))
async def harem_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id != user_data.get(user_id):
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    if data == "close":
        await callback_query.message.delete()
        return

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await callback_query.answer("You don't have any characters yet. Loot some to customize your harem!", show_alert=True)
        return

    if data == "sort_rarity":
        await send_rarity_preferences(callback_query)
    elif data == "reset_preferences":
        await reset_user_preferences(callback_query)

# Send rarity preferences
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
    keyboard = [
        [InlineKeyboardButton(rarity, callback_data=f"rarity_{rarity.split()[1]}")] for rarity in rarity_order
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await callback_query.message.edit_text(
        "🎴 **Choose Your Preferred Rarity** 🎴\n\nClick a button to set your rarity preference.",
        reply_markup=reply_markup
    )

# Callback for rarity selection
@app.on_callback_query(filters.regex(r'^rarity_'))
async def rarity_selection_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id != user_data.get(user_id):
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    rarity = data.split("_")[1]
    await user_collection.update_one({'id': user_id}, {'$set': {'rarity_preference': rarity}})
    await callback_query.message.edit_text(
        f"🎉 **Your harem interface has been successfully updated to {rarity}!** 🎉\n\nExplore more customization options!"
    )

# Reset user preferences
async def reset_user_preferences(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await user_collection.update_one({'id': user_id}, {'$unset': {'rarity_preference': ''}})
    await callback_query.message.edit_text(
        "🔄 **Your rarity preferences have been reset successfully!** 🔄\n\nFeel free to set new preferences anytime!"
    )
