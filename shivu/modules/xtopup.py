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
            "💠 To exchange characters: `/exchange <old_character_name> <target_rarity>`"
        )
        return

    old_character_name = args[0]
    target_rarity = args[1].capitalize()

    # Find old character
    characters = user_data["characters"]
    old_character = next((c for c in characters if c["name"] == old_character_name), None)

    if not old_character:
        await update.message.reply_text(f"❌ Character '{old_character_name}' not found!")
        return

    if old_character["rarity"] == target_rarity:
        await update.message.reply_text("❌ You cannot exchange for the same rarity.")
        return

    if target_rarity not in rarity_costs:
        await update.message.reply_text(
            "❌ Invalid rarity! Available rarities: Legendary, Exclusive, Limited Edition, Premium, Astral, Exotic, Valentine."
        )
        return

    # Determine the lowest rarity character as the cost
    lowest_character = get_lowest_rarity_character(characters)
    if not lowest_character:
        await update.message.reply_text("❌ You don't have any characters to exchange!")
        return

    # Display warning about losing the lowest rarity character
    await update.message.reply_text(
        f"""
⚠️ **Warning!** ⚠️  

In this exchange:  
🌀 You will lose your **lowest rarity character**:  
✨ **{lowest_character['name']} (Rarity: {lowest_character['rarity']})**  

💠 Make sure you're okay with this before proceeding!  

👉 **Next Step**: You can confirm or reject the exchange in the following prompt.
""",
        parse_mode="Markdown",
    )

    # Display confirmation with buttons
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Accept", callback_data=f"accept:{user_id}:{old_character_name}:{target_rarity}"
            ),
            InlineKeyboardButton("❌ Reject", callback_data="reject"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"""
⚠️ **Confirm Exchange** ⚠️

🌀 **Old Character:** `{old_character_name}`  
🌟 **Target Rarity:** `{target_rarity}`  

📜 **Cost:** Your lowest rarity character:  
✨ **{lowest_character['name']} (Rarity: {lowest_character['rarity']})**

💠 **Note:** Once accepted, your lowest rarity character will be removed as part of the exchange.
""",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

async def handle_exchange_confirmation(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "reject":
        await query.message.edit_text("❌ Exchange rejected.")
        return

    if data.startswith("accept"):
        _, user_id, old_character_name, target_rarity = data.split(":")
        user_id = int(user_id)
        user_data = get_user_data(user_id)

        # Find and remove old character
        characters = user_data["characters"]
        old_character = next((c for c in characters if c["name"] == old_character_name), None)
        characters.remove(old_character)

        # Remove the lowest rarity character as the cost
        lowest_character = get_lowest_rarity_character(characters)
        characters.remove(lowest_character)

        # Add new character
        new_character = {
            "name": f"Hero_{target_rarity}_{random.randint(1000, 9999)}",
            "rarity": target_rarity,
        }
        characters.append(new_character)

        await query.message.edit_text(
            f"""
🎉 **Exchange Successful!** 🎉  

🔄 You exchanged **{old_character_name}** and your lowest rarity character **{lowest_character['name']}**  
🌟 **For a new character:**  
✨ **{new_character['name']} (Rarity: {target_rarity})**  

💡 Thank you for using the exchange feature!
"""
        )

# Initialize Application
application.add_handler(CommandHandler("topup", tokens))
application.add_handler(CommandHandler("exchange", exchange))
application.add_handler(CallbackQueryHandler(handle_exchange_confirmation))
