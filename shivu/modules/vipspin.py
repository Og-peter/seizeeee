import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from shivu import application, collection, user_collection

LOW_RARITIES = ["⚪ Common", "🔵 Medium", "🟠 Rare", "👶 Chibi"]
HIGH_RARITIES = ["🔮 Limited Edition", "🫧 Premium", "💮 Exclusive", "🟡 Legendary"]

# In-memory tracking for daily spins
daily_spin_limit = {}

async def add_characters_to_user(user_id, waifu):
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': waifu}},
        upsert=True
    )

async def remove_characters_from_user(user_id, characters_to_remove):
    await user_collection.update_one(
        {'id': user_id},
        {'$pull': {'characters': {'$in': characters_to_remove}}}
    )

async def get_user_characters(user_id):
    user = await user_collection.find_one({'id': user_id})
    return user.get('characters', []) if user else []

async def vipspin(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        current_time = datetime.now()

        # Initialize or reset daily spin limit
        if user_id not in daily_spin_limit:
            daily_spin_limit[user_id] = {'count': 0, 'last_spin': current_time}
        elif (current_time - daily_spin_limit[user_id]['last_spin']).days >= 1:
            daily_spin_limit[user_id] = {'count': 0, 'last_spin': current_time}

        if daily_spin_limit[user_id]['count'] >= 3:
            await update.message.reply_text("🚫 You've reached your daily spin limit. Try again tomorrow!")
            return

        user_characters = await get_user_characters(user_id)
        low_rarity_characters = [c for c in user_characters if c['rarity'] in LOW_RARITIES]
        
        if len(low_rarity_characters) < 2 or len(user_characters) < 3:
            await update.message.reply_text(
                "⚠️ To use VIP Spin:\n"
                "- You need at least **3 characters** in your collection.\n"
                "- At least **2 of them** must be from **low rarity** categories (e.g., 🔵 Common, 🟢 Medium).\n"
            )
            return

        # Create the Accept/Reject buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"vipspin_accept:{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"vipspin_reject:{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Instruction message with buttons
        await update.message.reply_text(
            "🔄 **VIP Spin Activated!**\n\n"
            "📜 **How it works:**\n"
            "- Two low-rarity characters from your collection will be exchanged.\n"
            "- One extra random character will also be taken.\n"
            "- In return, you will receive **one high-rarity character** as a reward.\n\n"
            "✨ Do you want to proceed?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ An error occurred: {str(e)}")

async def handle_vipspin_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    original_user_id = int(callback_data.split(":")[1])

    if user_id != original_user_id:
        await query.answer("❌ This button isn't for you!", show_alert=True)
        return

    if "vipspin_accept" in callback_data:
        await query.edit_message_text("🔄 Processing your VIP Spin...")
        
        try:
            # Retrieve the original user data again
            user_characters = await get_user_characters(user_id)
            low_rarity_characters = [c for c in user_characters if c['rarity'] in LOW_RARITIES]

            # Select 2 low-rarity characters to exchange
            characters_to_exchange = random.sample(low_rarity_characters, 2)
            
            # Select 1 extra random character from the user's collection
            extra_character = random.choice(user_characters)
            
            # Remove selected characters from the user's collection
            characters_to_remove = characters_to_exchange + [extra_character]
            await remove_characters_from_user(user_id, characters_to_remove)

            # Select one random high-rarity character as a reward
            high_rarity = random.choice(HIGH_RARITIES)
            high_rarity_characters = await collection.find({'rarity': high_rarity}).to_list(length=None)
            
            if high_rarity_characters:
                rewarded_character = random.choice(high_rarity_characters)
                await add_characters_to_user(user_id, rewarded_character)
                daily_spin_limit[user_id]['count'] += 1

                # Send the final result
                reply_message = (
                    f"🎰 **VIP Spin Results - Character Exchange** 🎰\n\n"
                    f"🔄 **Exchanged Characters:**\n"
                    + "\n".join(f"🔸 {char['name']} ({char['rarity']})" for char in characters_to_exchange)
                    + f"\n\n❗ **Extra Character Taken:** {extra_character['name']} ({extra_character['rarity']})\n\n"
                    f"🎁 **Received:** {rewarded_character['name']} ({rewarded_character['rarity']})\n\n"
                    f"🎉 You have **{3 - daily_spin_limit[user_id]['count']} spins** left today."
                )
                await query.edit_message_text(reply_message, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ No high-rarity rewards available. Try again later.")
        except Exception as e:
            await query.edit_message_text(f"⚠️ An error occurred: {str(e)}")
    elif "vipspin_reject" in callback_data:
        await query.edit_message_text("❌ You rejected the VIP Spin.")

VIPSPIN_HANDLER = CommandHandler('vipspin', vipspin, block=False)
VIPSPIN_CALLBACK_HANDLER = CallbackQueryHandler(handle_vipspin_callback, pattern="vipspin_.*")

application.add_handler(VIPSPIN_HANDLER)
application.add_handler(VIPSPIN_CALLBACK_HANDLER)
