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
        await update.message.reply_text('Cooldown in effect! Please wait before selling another character. ⏳')
        return
    cooldowns[user_id] = current_time

    # Check if the command includes a character ID
    if not context.args or len(context.args) != 1:
        await update.message.reply_text('❌ Please provide a valid Character ID to sell.')
        return
    
    character_id = context.args[0]
    
    # Retrieve the character from the harem based on the provided ID
    character = await collection.find_one({'id': character_id})
    if not character:
        await update.message.reply_text('❌ Character Not Found. Please try again. 🚫')
        return
    
    # Check if the user has the character in their harem
    user = await user_collection.find_one({'id': user_id})
    if not user or 'characters' not in user:
        await update.message.reply_text('❌ You do not own this Character in your harem.')
        return

    # Check if the character is present in the user's harem and get its count
    character_count = sum(1 for char in user.get('characters', []) if char['id'] == character_id)
    if character_count == 0:
        await update.message.reply_text('❌ You do not own this Character in your harem.')
        return

    # Determine the coin value based on the rarity of the character
    rarity_coin_mapping = {
        "⚪ Common": 2000,
        "🔵 Medium": 4000,
        "🟠 Rere": 5000,
        "👶 Chibi": 10000,
        "🟡 Legendary": 30000,
        "💮 Exclusive": 20000,
        "🔮 Limited Edition": 40000,
    }

    rarity = character.get('rarity', 'Unknown Rarity')
    coin_value = rarity_coin_mapping.get(rarity, 0)
    image_url = character.get('image_url', '')

    if coin_value == 0:
        await update.message.reply_text('❌ Invalid rarity. Cannot determine the coin value.')
        return

    # Add bonus for selling Legendary or Limited Edition characters
    if rarity in ["🟡 Legendary", "🔮 Limited Edition"]:
        coin_value += random.randint(5000, 10000)  # Random bonus between 5000 and 10000 tokens

    # Random animation messages
    animations = [
        "🌟 Whoooosh! 🌟 Your character is flying away into the marketplace! 🚀",
        "✨ A magical transaction is happening! ✨ Your coins are being counted... 💰",
        "💫 Selling in progress... Hang tight! 💫",
        "⚡️ Zzzzap! ⚡️ Your character is being teleported for sale! ✨",
    ]
    animation_message = random.choice(animations)

    # Ask for confirmation to sell the character
    confirmation_text = (
        f"╭─── Sell Confirmation ───\n"
        f"| Character Name: {character['name']}\n"
        f"| Rarity: {rarity}\n"
        f"| Coin Value: {coin_value} 💰\n"
        "╰───────────────────────"
    )

    buttons = [
        [InlineKeyboardButton("Confirm ✅", callback_data=f"confirm_sell_{character_id}_{coin_value}")],
        [InlineKeyboardButton("Cancel ❌", callback_data="cancel_sell")]
    ]

    await update.message.reply_text(animation_message)
    if image_url:
        await update.message.reply_photo(photo=image_url, caption=confirmation_text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text(confirmation_text, reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback_query(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("confirm_sell_"):
        _, character_id, coin_value = data.split("_")
        coin_value = int(coin_value)

        # Perform the sale
        user = await user_collection.find_one({'id': user_id})

        # Remove the sold character from the user's harem
        await user_collection.update_one(
            {'id': user_id},
            {'$pull': {'characters': {'id': character_id}}, '$inc': {'balance': coin_value}}
        )

        # Notify success in the current chat
        await query.message.reply_text(f"✅ Successfully Sold Character 🌸\nCharacter ID: {character_id}\nSold For: {coin_value} 💸 Tokens.")

        # Send a DM to the user about the sold character
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔔 You have successfully sold your character! 🌟\n\n"
                 f"Character ID: {character_id}\n"
                 f"Coin Value: {coin_value} 💰 Tokens."
        )
        
    elif data == "cancel_sell":
        await query.message.reply_text("❌ Sell canceled.")
        await query.answer()  # Close the popup

sell_handler = CommandHandler("sell", sell, block=False)
application.add_handler(sell_handler)
application.add_handler(CallbackQueryHandler(handle_callback_query))
