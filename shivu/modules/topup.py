from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import application, user_collection
from datetime import datetime, timedelta
import random

# Constants for rewards
FREE_TOPUP_REWARD = 500
WEEKLY_TOPUP_COST = 1200
WEEKLY_REWARDS = {
    'daily': {'wealth': 500, 'tokens': 0, 'character_rarity': '🟠 Rare'},
    'weekly_end': {'wealth': 1000, 'tokens': 2000, 'character_rarity': '🟡 Legendary'}
}
MONTHLY_TOPUP_COST = 3000
MONTHLY_REWARDS = {
    'weekly': {'wealth': 1000, 'tokens': 1000, 'character_rarity': '🟡 Legendary'},
    'month_end': {'wealth': 2000, 'tokens': 3000, 'character_rarity': '🔮 Limited Edition'}
}

# Track user data (mock database)
users = {}

def get_user_data(user_id):
    if user_id not in users:
        users[user_id] = {
            'balance': 0,
            'wealth': 0,
            'free_topup_claimed': False,
            'weekly_topup': {
                'active': False,
                'start_date': None,
                'last_claim_date': None
            },
            'monthly_topup': {
                'active': False,
                'start_date': None,
                'last_claim_date': None
            }
        }
    return users[user_id]

def get_random_character(rarity):
    characters = {
        '🟠 Rare': {'name': 'Rare Hero', 'img_url': 'https://example.com/rare.jpg'},
        '🟡 Legendary': {'name': 'Legendary Hero', 'img_url': 'https://example.com/legendary.jpg'},
        '🔮 Limited Edition': {'name': 'Limited Hero', 'img_url': 'https://example.com/limited.jpg'}
    }
    return characters[rarity]

async def topup_cmd(update, context):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    keyboard = [
        [InlineKeyboardButton("Free Top-Up 🎁", callback_data=f"free_topup:{user_id}")],
        [InlineKeyboardButton("Weekly Top-Up 🗓️", callback_data=f"weekly_topup:{user_id}")],
        [InlineKeyboardButton("Monthly Top-Up 🗓️", callback_data=f"monthly_topup:{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "<b>❰ 𝗧 𝗢 𝗣 𝗨 𝗣 𝗠 𝗘 𝗡 𝗨 ❱</b>\n\n"
        "1️⃣ Free Top-Up: 500 tokens.\n"
        "2️⃣ Weekly Top-Up: 1200 tokens. Rewards daily + end of week bonus.\n"
        "3️⃣ Monthly Top-Up: 3000 tokens. Rewards weekly + month-end bonus.\n\n"
        "Choose your option below!",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def button_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    action, target_user_id = query.data.split(":")
    target_user_id = int(target_user_id)

    if user_id != target_user_id:
        await query.answer("This button is not for you!", show_alert=True)
        return

    user = get_user_data(user_id)

    if action == "free_topup":
        if user['free_topup_claimed']:
            await query.answer("You have already claimed the Free Top-Up.", show_alert=True)
            return

        user['balance'] += FREE_TOPUP_REWARD
        user['free_topup_claimed'] = True

        await query.message.edit_text(
            f"🎉 Free Top-Up claimed! You received {FREE_TOPUP_REWARD} tokens."
        )

    elif action == "weekly_topup":
        if user['balance'] < WEEKLY_TOPUP_COST:
            await query.answer("Not enough tokens for Weekly Top-Up!", show_alert=True)
            return

        if user['weekly_topup']['active']:
            await query.answer("Weekly Top-Up is already active.", show_alert=True)
            return

        user['balance'] -= WEEKLY_TOPUP_COST
        user['weekly_topup']['active'] = True
        user['weekly_topup']['start_date'] = datetime.now()

        await query.message.edit_text(
            "🗓️ Weekly Top-Up activated! Claim daily rewards and a bonus at the end of the week."
        )

    elif action == "monthly_topup":
        if user['balance'] < MONTHLY_TOPUP_COST:
            await query.answer("Not enough tokens for Monthly Top-Up!", show_alert=True)
            return

        if user['monthly_topup']['active']:
            await query.answer("Monthly Top-Up is already active.", show_alert=True)
            return

        user['balance'] -= MONTHLY_TOPUP_COST
        user['monthly_topup']['active'] = True
        user['monthly_topup']['start_date'] = datetime.now()

        await query.message.edit_text(
            "🗓️ Monthly Top-Up activated! Claim weekly rewards and a bonus at the end of the month."
        )

application.add_handler(CommandHandler("topup", topup_cmd))
application.add_handler(CallbackQueryHandler(button_callback, pattern="free_topup:.*|weekly_topup:.*|monthly_topup:.*"))
