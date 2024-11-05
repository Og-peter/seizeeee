from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import collection, user_collection, application
import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Cooldown dictionary to track user cooldowns
cooldowns = {}

async def sell(update, context):
    user_id = update.effective_user.id

    # Cooldown check (5 seconds cooldown)
    current_time = time.time()
    if user_id in cooldowns and current_time - cooldowns[user_id] < 5:
        await update.message.reply_text('Cooldown in effect! Please wait before selling another waifu. ⏳')
        return
    cooldowns[user_id] = current_time

    # Check if the command includes a waifu ID
    if not context.args or len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a valid Waifu ID to sell.\n**Usage:** /sell <waifu_id>')
        return
    
    waifu_id = context.args[0]
    
    # Retrieve the waifu from the harem based on the provided ID
    waifu = await collection.find_one({'id': waifu_id})
    if not waifu:
        await update.message.reply_text('❌ Waifu Not Found. Please try again. 🚫')
        return
    
    # Check if the user has the waifu in their harem
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await update.message.reply_text('❌ You do not own this waifu in your harem.')
        return

    # Check if the waifu is present in the user's harem
    character = next((char for char in user['characters'] if char['id'] == waifu_id), None)
    if not character:
        await update.message.reply_text('❌ You do not own this waifu in your harem.')
        return

    # Determine the coin value based on the rarity of the waifu
    rarity_coin_mapping = {
        "⚪ Common": 2000,
        "🔵 Medium": 4000,
        "🟠 Rare": 5000,
        "👶 Chibi": 10000,
        "🟡 Legendary": 30000,
        "💮 Exclusive": 20000,
        "🔮 Limited Edition": 40000,
    }

    rarity = waifu.get('rarity', 'Unknown Rarity')
    coin_value = rarity_coin_mapping.get(rarity, 0)
    image_url = waifu.get('image_url', '')

    if coin_value == 0:
        await update.message.reply_text('❌ Invalid rarity. Cannot determine the coin value.')
        return

    # Add bonus for selling Legendary or Limited Edition waifus
    if rarity in ["🟡 Legendary", "🔮 Limited Edition"]:
        coin_value += random.randint(5000, 10000)  # Random bonus between 5000 and 10000 tokens

    # Ask for confirmation to sell the waifu
    confirmation_text = (
        f"❄️ **Are you sure you want to sell this waifu?** ❄️\n\n"
        f"🫧 **Name:** `{waifu['name']}`\n"
        f"⛩️ **Rarity:** {rarity}\n"
        f"💰 **Coin Value:** `{coin_value}`\n\n"
        "⚜️ **Choose an option:**"
    )

    # Send character photo with confirmation message and inline buttons
    confirmation_message = await update.message.reply_photo(
        photo=image_url,
        caption=confirmation_text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Confirm", callback_data=f"sell_confirm_{waifu_id}_{coin_value}"),
                InlineKeyboardButton("🔴 Cancel", callback_data="sell_cancel")
            ]
        ])
    )

async def handle_callback_query(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("sell_confirm_"):
        _, waifu_id, coin_value = data.split("_")
        coin_value = int(coin_value)

        # Perform the sale
        user = await user_collection.find_one({'id': user_id})

        # Ensure character exists in user's harem
        if not any(char['id'] == waifu_id for char in user.get('characters', [])):
            await query.answer("You don't own this waifu!", show_alert=True)
            return

        # Remove the sold waifu from the user's harem and update balance
        await user_collection.update_one(
            {'id': user_id},
            {
                '$pull': {'characters': {'id': waifu_id}},
                '$inc': {'balance': coin_value}
            }
        )

        # Notify success in the current chat
        await query.message.reply_text(f"✅ Successfully Sold Waifu 🌸\nWaifu ID: {waifu_id}\nSold For: {coin_value} 💸 Tokens.")
        await query.answer()  # Acknowledge callback to close popup

    elif data == "sell_cancel":
        await query.message.reply_text("❌ Sell canceled.")
        await query.answer("Sell canceled.", show_alert=True)

# Define handlers
sell_handler = CommandHandler("sell", sell)
callback_query_handler = CallbackQueryHandler(handle_callback_query)

# Add handlers to the application
application.add_handler(sell_handler)
application.add_handler(callback_query_handler)
