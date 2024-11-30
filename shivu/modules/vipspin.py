import asyncio
import random
from datetime import datetime
from telegram import Update
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
        {'$pull': {'characters': {'name': {'$in': [c['name'] for c in characters_to_remove]}}}}
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
            message = await update.message.reply_text(
                "🚫 You've reached your daily spin limit. Try again tomorrow!"
            )
            await asyncio.sleep(3)
            await message.delete()
            return

        user_characters = await get_user_characters(user_id)
        low_rarity_characters = [c for c in user_characters if c['rarity'] in LOW_RARITIES]

        if len(low_rarity_characters) < 2 or len(user_characters) < 3:
            message = await update.message.reply_text(
                "⚠️ To use VIP Spin:\n"
                "- You need at least **3 characters** in your collection.\n"
                "- At least **2 of them** must be from **low rarity** categories (e.g., ⚪ Common, 🔵 Medium).",
                parse_mode='Markdown'
            )
            await asyncio.sleep(3)
            await message.delete()
            return

        # Process the spin
        processing_message = await update.message.reply_text(
            "🔄 **VIP Spin Activated!**\n\n"
            "📜 **How it works:**\n"
            "- Two low-rarity characters from your collection will be exchanged.\n"
            "- One extra random character will also be taken.\n"
            "- In return, you will receive **one high-rarity character** as a reward.\n\n"
            "✨ Processing your request...",
            parse_mode='Markdown'
        )

        await asyncio.sleep(3)
        await processing_message.delete()

        # Handle spin logic
        user_characters = await get_user_characters(user_id)
        low_rarity_characters = [c for c in user_characters if c['rarity'] in LOW_RARITIES]

        characters_to_exchange = random.sample(low_rarity_characters, 2)
        extra_character = random.choice(user_characters)
        characters_to_remove = characters_to_exchange + [extra_character]
        await remove_characters_from_user(user_id, characters_to_remove)

        high_rarity = random.choice(HIGH_RARITIES)
        high_rarity_characters = await collection.find({'rarity': high_rarity}).to_list(length=None)

        if high_rarity_characters:
            rewarded_character = random.choice(high_rarity_characters)
            await add_characters_to_user(user_id, rewarded_character)
            daily_spin_limit[user_id]['count'] += 1

            result_message = await update.message.reply_text(
                f"🎰 **VIP Spin Results - Character Exchange** 🎰\n\n"
                f"🔄 **Exchanged Characters:**\n"
                + "\n".join(f"🔸 {char['name']} ({char['rarity']})" for char in characters_to_exchange)
                + f"\n\n❗ **Extra Character Taken:** {extra_character['name']} ({extra_character['rarity']})\n\n"
                f"🎁 **Received:** {rewarded_character['name']} ({rewarded_character['rarity']})\n\n"
                f"🎉 You have **{3 - daily_spin_limit[user_id]['count']} spins** left today.",
                parse_mode='Markdown'
            )
            await asyncio.sleep(3)
            await result_message.delete()
        else:
            error_message = await update.message.reply_text("❌ No high-rarity rewards available. Try again later.")
            await asyncio.sleep(3)
            await error_message.delete()

    except Exception as e:
        error_message = await update.message.reply_text(f"⚠️ An error occurred: {str(e)}")
        await asyncio.sleep(3)
        await error_message.delete()

VIPSPIN_HANDLER = CommandHandler('vipspin', vipspin, block=False)

application.add_handler(VIPSPIN_HANDLER)
