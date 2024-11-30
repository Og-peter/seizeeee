
import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
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

        # Instruction message
        await update.message.reply_text(
            "🔄 **VIP Spin Activated!**\n\n"
            "📜 **How it works:**\n"
            "- Two low-rarity characters from your collection will be exchanged.\n"
            "- One extra random character will also be taken.\n"
            "- In return, you will receive **one high-rarity character** as a reward.\n\n"
            "✨ Let's begin the spin!"
        )

        # Animation message
        animation_msg = await update.message.reply_text("🔄 Preparing your VIP Spin...")
        animations = ["✨ Spinning the wheel...", "🔄 Exchanging characters...", "🎁 Finding your reward..."]
        for animation in animations:
            await asyncio.sleep(1.5)
            await animation_msg.edit_text(animation)

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

            # Delete animation message
            await animation_msg.delete()

            # Prepare and send the final result
            reply_message = (
                f"🎰 **VIP Spin Results - Character Exchange** 🎰\n\n"
                f"🔄 **Exchanged Characters:**\n"
                + "\n".join(f"🔸 {char['name']} ({char['rarity']})" for char in characters_to_exchange)
                + f"\n\n❗ **Extra Character Taken:** {extra_character['name']} ({extra_character['rarity']})\n\n"
                f"🎁 **Received:** {rewarded_character['name']} ({rewarded_character['rarity']})\n\n"
                f"🎉 You have **{3 - daily_spin_limit[user_id]['count']} spins** left today."
            )
            await update.message.reply_text(reply_message, parse_mode='Markdown')
        else:
            await animation_msg.delete()
            await update.message.reply_text("❌ No high-rarity rewards available. Try again later.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ An error occurred: {str(e)}")

VIPSPIN_HANDLER = CommandHandler('vipspin', vipspin, block=False)
application.add_handler(VIPSPIN_HANDLER)
