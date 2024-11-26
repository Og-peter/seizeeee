import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, collection, user_collection

# List of rarities for sorting (higher to lower for exchange)
RARITIES = [
    "🟡 Legendary",
    "💮 Exclusive",
    "🫧 Premium",
    "🔮 Limited Edition"
]

# In-memory tracking for daily spins
daily_spin_limit = {}

async def add_characters_to_user(user_id, waifus):
    user = await user_collection.find_one({'id': user_id})
    if user:
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': waifus}}})
    else:
        await user_collection.insert_one({'id': user_id, 'characters': waifus})

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

        # Initialize or update daily spin limit
        if user_id not in daily_spin_limit:
            daily_spin_limit[user_id] = {'count': 0, 'last_spin': current_time}
        last_spin = daily_spin_limit[user_id]['last_spin']

        # Reset daily limit if more than 1 day has passed
        if (current_time - last_spin).days >= 1:
            daily_spin_limit[user_id] = {'count': 0, 'last_spin': current_time}

        if daily_spin_limit[user_id]['count'] >= 3:
            await update.message.reply_text(
                "🚫 You have reached your daily limit of 3 spins. Try again tomorrow!"
            )
            return

        user_characters = await get_user_characters(user_id)
        if len(user_characters) < 5:
            await update.message.reply_text(
                "⚠️ You need at least 5 characters in your collection to perform a spin."
            )
            return

        # Randomly select 5 characters to exchange
        characters_to_exchange = random.sample(user_characters, 5)
        await remove_characters_from_user(user_id, characters_to_exchange)

        # Generate rewards
        waifus = []
        for _ in range(5):  # Reward 5 characters for exchange
            rarity = random.choice(RARITIES)
            all_waifus = await collection.find({'rarity': rarity}).to_list(length=None)
            if all_waifus:
                waifu = random.choice(all_waifus)
                waifus.append(waifu)

        if waifus:
            await add_characters_to_user(user_id, waifus)
            daily_spin_limit[user_id]['count'] += 1
            daily_spin_limit[user_id]['last_spin'] = current_time

            # Prepare reply message
            reply_message = "🎰 **Your VIP Spin Results** 🎰\n\n"
            for waifu in waifus:
                reply_message += (
                    f"✨ **Name**: {waifu['name']}\n"
                    f"🎭 **Anime**: {waifu['anime']}\n"
                    f"💎 **Rarity**: {waifu['rarity']}\n\n"
                )
            reply_message += (
                f"🎉 You successfully exchanged 5 characters! "
                f"You can spin {3 - daily_spin_limit[user_id]['count']} more time(s) today."
            )

            # Animation using text effects
            animations = [
                "🔄 Spinning the wheel...",
                "✨ Characters flying into the VIP zone...",
                "🎁 Opening your rewards..."
            ]
            for animation in animations:
                await update.message.reply_text(animation)
                await asyncio.sleep(1)

            # Send final results
            await update.message.reply_text(reply_message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No rewards found. Please try again.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

VIPSPIN_HANDLER = CommandHandler('vipspin', vipspin, block=False)
application.add_handler(VIPSPIN_HANDLER)
