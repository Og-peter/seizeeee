import asyncio
from shivu import application
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, CallbackContext
import random

# In-Memory Database
users_data = {}

# Rarity costs and rewards
rarity_costs = {
    "Legendary": 5,
    "Exclusive": 10,
    "Limited Edition": 50,
    "Premium": 200,
    "Astral": 500,
    "Exotic": 1000,
    "Valentine": 1500,
}

# Helper Function: Get or Initialize User Data
def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "tokens": 0,
            "characters": [{"name": "Starter_Common", "rarity": "Common"}],
        }
    return users_data[user_id]

# Helper Function: Get the Lowest Rarity Character
def get_lowest_rarity_character(user_characters):
    rarities = ["Common", "Rare", "Medium"]
    for rarity in rarities:
        low_rarity = next((c for c in user_characters if c["rarity"] == rarity), None)
        if low_rarity:
            return low_rarity
    return None

async def tokens(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args

    user_data = get_user_data(user_id)

    if not args or len(args) < 1:
        await update.message.reply_text("💳 To top up tokens: `/topup <amount>`")
        return

    try:
        amount = int(args[0])
        if amount < 10:
            await update.message.reply_text("❌ Minimum top-up is 10 tokens.")
            return

        # Simulate top-up
        user_data["tokens"] += amount
        formatted_balance = "{:,.0f}".format(user_data["tokens"])

        # Send success message without an image
        balance_message = f"""
┌─━═━─━═━─━═━─━═━─━═━─━═━─┐
🪙 **Your Token Balance Updated!** 🎮  
✨ **Tokens Added:** Ŧ `{amount}`  
💰 **New Balance:** Ŧ `{formatted_balance}`
└─━═━─━═━─━═━─━═━─━═━─━═━─┘
"""
        await update.message.reply_text(balance_message, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")

async def exchange(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args

    user_data = get_user_data(user_id)

    if not args or len(args) < 2:
        await update.message.reply_text(
            "💠 **Usage:** `/exchange <old_character_id> <target_rarity>`\n\n"
            "🌟 **Example:** `/exchange 12345 Legendary`"
        )
        return

    old_character_id = args[0]
    target_rarity = args[1].capitalize()

    # Find old character by ID
    characters = user_data["characters"]
    old_character = next((c for c in characters if str(c["id"]) == old_character_id), None)

    if not old_character:
        await update.message.reply_text(f"❌ **Character with ID `{old_character_id}` not found!**")
        return

    if old_character["rarity"] == target_rarity:
        await update.message.reply_text("❌ **You cannot exchange for the same rarity.**")
        return

    if target_rarity not in rarity_costs:
        await update.message.reply_text(
            "❌ **Invalid rarity!**\n\n"
            "🎨 **Available rarities:**\n`Legendary, Exclusive, Limited Edition, Premium, Astral, Exotic, Valentine`"
        )
        return

    # Determine the lowest rarity character as the tax
    lowest_character = get_lowest_rarity_character(characters)
    if not lowest_character:
        await update.message.reply_text("❌ **You don't have any characters available for tax!**")
        return

    await update.message.reply_text(
        f"""
⚠️ **Exchange Details** ⚠️

🔄 **Character to Exchange:**  
🆔 `{old_character['id']}` - ✨ `{old_character['name']}` (Rarity: `{old_character['rarity']}`)

🌟 **Target Rarity:** `{target_rarity}`

💰 **Tax Character:**  
🆔 `{lowest_character['id']}` - ✨ `{lowest_character['name']}` (Rarity: `{lowest_character['rarity']}`)

💠 **Proceed only if you're willing to lose this character in tax!**
""",
        parse_mode="Markdown",
    )

    # Display confirmation with buttons
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm Exchange",
                callback_data=f"accept:{user_id}:{old_character['id']}:{target_rarity}:{lowest_character['id']}",
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="reject"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💬 **Do you want to proceed?**",
        reply_markup=reply_markup,
    )


async def handle_exchange_confirmation(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "reject":
        await query.message.edit_text("❌ **Exchange cancelled.**")
        return

    if data.startswith("accept"):
        _, user_id, old_character_id, target_rarity, tax_character_id = data.split(":")
        user_id = int(user_id)
        user_data = get_user_data(user_id)

        # Remove old character and tax character
        characters = user_data["characters"]
        old_character = next((c for c in characters if str(c["id"]) == old_character_id), None)
        tax_character = next((c for c in characters if str(c["id"]) == tax_character_id), None)

        if old_character:
            characters.remove(old_character)
        if tax_character:
            characters.remove(tax_character)

        # Add new character
        new_character = {
            "id": random.randint(1000, 9999),
            "name": f"Hero_{target_rarity}_{random.randint(1000, 9999)}",
            "rarity": target_rarity,
        }
        characters.append(new_character)

        await query.message.edit_text(
            f"""
🎉 **Exchange Completed!** 🎉  

🆔 **Old Character Removed:** `{old_character['id']}` - ✨ `{old_character['name']}`  
💰 **Tax Character Removed:** `{tax_character['id']}` - ✨ `{tax_character['name']}`  

🌟 **New Character Added:**  
🆔 `{new_character['id']}` - ✨ `{new_character['name']}` (Rarity: `{target_rarity}`)

💡 **Thank you for using the exchange service!**
"""
        )

# Initialize Application
application.add_handler(CommandHandler("topup", tokens))
application.add_handler(CommandHandler("exchange", exchange))
application.add_handler(CallbackQueryHandler(handle_exchange_confirmation))
