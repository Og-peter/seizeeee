import asyncio
from shivu import application
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, CallbackContext
import random
import datetime

# In-Memory Database
users_data = {}

# Rewards for each top-up type
topup_rewards = {
    "Free": {"tokens": 500, "characters": [], "wealth": 0, "cooldown": 24},  # Cooldown in hours
    "Weekly": {
        "tokens": 1200,
        "characters": [{"name": "Rare_Orange", "rarity": "Rare"}],
        "wealth": 500,
        "discount": 0.1,  # 10% Discount
        "last_day_bonus": {"tokens": 2000, "characters": [{"name": "Legendary_Yellow", "rarity": "Legendary"}], "wealth": 1000},
    },
    "Monthly": {
        "tokens": 1000,
        "characters": [{"name": "Legendary_Yellow", "rarity": "Legendary"}],
        "wealth": 1000,
        "discount": 0.2,  # 20% Discount
        "last_week_bonus": {"tokens": 3000, "characters": [{"name": "Limited_Edition", "rarity": "Limited Edition"}], "wealth": 2000},
    },
}

# Helper Function: Get or Initialize User Data
def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "tokens": 0,
            "wealth": 0,
            "characters": [{"id": 1, "name": "Starter_Common", "rarity": "Common"}],
            "last_topup": None,
            "reward_history": [],
        }
    return users_data[user_id]

# Helper Function: Generate New Character
def generate_character(rarity, name_prefix):
    return {
        "id": random.randint(1000, 9999),
        "name": f"{name_prefix}_{random.randint(1000, 9999)}",
        "rarity": rarity,
    }

# Helper Function: Calculate Discounted Tokens
def calculate_discount(tokens, discount):
    return int(tokens * (1 - discount))

# Command: Show Top-Up Options
async def topup(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    keyboard = [
        [InlineKeyboardButton("💎 Free Top-Up", callback_data="topup:Free")],
        [InlineKeyboardButton("📅 Weekly Top-Up", callback_data="topup:Weekly")],
        [InlineKeyboardButton("🗓️ Monthly Top-Up", callback_data="topup:Monthly")],
        [InlineKeyboardButton("📜 View Reward History", callback_data="topup:History")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💳 **Choose a Top-Up Plan:**\n\n"
        "1️⃣ **Free Top-Up:** Get 500 Tokens (once every 24 hours).\n"
        "2️⃣ **Weekly Top-Up:** 1200 Tokens + 🟠 Rare Character + 500 Wealth. Bonus on the last weekly day: 2000 Tokens + 🟡 Legendary + 1000 Wealth.\n"
        "3️⃣ **Monthly Top-Up:** Weekly 1000 Tokens + 🟡 Legendary + 1000 Wealth. Last Week: 🔮 Limited Edition Character + 3000 Tokens + 2000 Wealth.\n",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

# Handle Top-Up Confirmation
async def handle_topup(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    _, topup_type = query.data.split(":")
    if topup_type == "History":
        history = user_data["reward_history"]
        if not history:
            await query.message.edit_text("📜 **Reward History is empty!**")
        else:
            formatted_history = "\n".join(
                [f"📅 `{entry['date']}` - 🪙 `{entry['tokens']} Tokens`, 🛡 `{entry['wealth']} Wealth`, Characters: {', '.join([c['name'] for c in entry['characters']])}" for entry in history]
            )
            await query.message.edit_text(f"📜 **Reward History:**\n\n{formatted_history}", parse_mode="Markdown")
        return

    rewards = topup_rewards.get(topup_type)
    if not rewards:
        await query.message.edit_text("❌ Invalid top-up type.")
        return

    now = datetime.datetime.now()

    # Cooldown Check for Free Top-Up
    if topup_type == "Free":
        last_topup = user_data.get("last_topup")
        if last_topup and (now - last_topup).total_seconds() < rewards["cooldown"] * 3600:
            remaining = rewards["cooldown"] - (now - last_topup).total_seconds() // 3600
            await query.message.edit_text(f"⏳ **Free Top-Up available in {int(remaining)} hours.**")
            return

    # Apply Discounts
    discount = rewards.get("discount", 0)
    if discount:
        discounted_tokens = calculate_discount(rewards["tokens"], discount)
        rewards["tokens"] = discounted_tokens

    # Time-Based Bonuses
    is_last_day_of_week = now.weekday() == 6
    is_last_week_of_month = now.isocalendar()[1] == now.replace(day=28).isocalendar()[1]

    if topup_type == "Weekly" and is_last_day_of_week:
        rewards["tokens"] += rewards["last_day_bonus"]["tokens"]
        rewards["characters"].extend(rewards["last_day_bonus"]["characters"])
        rewards["wealth"] += rewards["last_day_bonus"]["wealth"]

    if topup_type == "Monthly" and is_last_week_of_month:
        rewards["tokens"] += rewards["last_week_bonus"]["tokens"]
        rewards["characters"].extend(rewards["last_week_bonus"]["characters"])
        rewards["wealth"] += rewards["last_week_bonus"]["wealth"]

    # Update User Data
    user_data["tokens"] += rewards["tokens"]
    user_data["wealth"] += rewards["wealth"]
    for char in rewards["characters"]:
        user_data["characters"].append(generate_character(char["rarity"], char["name"]))
    user_data["last_topup"] = now if topup_type == "Free" else user_data["last_topup"]

    # Log Reward History
    user_data["reward_history"].append(
        {
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "tokens": rewards["tokens"],
            "wealth": rewards["wealth"],
            "characters": rewards["characters"],
        }
    )

    # Send Confirmation
    character_rewards = "\n".join(
        [f"✨ `{char['name']}` ({char['rarity']})" for char in rewards["characters"]]
    )
    await query.message.edit_text(
        f"""
🎉 **Top-Up Successful!** 🎉

💰 **Tokens Added:** `{rewards['tokens']}`  
🪙 **Wealth Added:** `{rewards['wealth']}`  
📜 **Characters Rewarded:**  
{character_rewards}

💡 **Thank you for using the top-up service!**
""",
        parse_mode="Markdown",
    )

# Initialize Application
application.add_handler(CommandHandler("topup", topup))
application.add_handler(CallbackQueryHandler(handle_topup, pattern="^topup:"))
