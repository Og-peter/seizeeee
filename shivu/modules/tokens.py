from telegram.ext import CommandHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from shivu import collection, user_collection, application
from shivu import shivuu as app
import random
from html import escape
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from pymongo import ReturnDocument
from shivu import sudo_users_collection
from shivu.modules.database.sudo import is_user_sudo

async def tokens(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_balance = await user_collection.find_one({'id': user_id}, projection={'tokens': 1})

    # Mention the user
    user_mention = f"[{update.effective_user.first_name}](tg://user?id={user_id})"

    if user_balance:
        balance_amount = user_balance.get('tokens', 0)
        formatted_balance = "{:,.0f}".format(balance_amount)
        balance_message = f"""
┌─━═━─━═━─━═━─━═━─━═━─━═━─┐
💼 **{user_mention}'s Token Balance** 💼
🪙 **Current Balance:** Ŧ `{formatted_balance}`
└─━═━─━═━─━═━─━═━─━═━─━═━─┘
"""
    else:
        balance_message = (
            "⚠️ Attention:\n"
            f"{user_mention}, you need to register first by starting the bot in DMs."
        )

    await update.message.reply_text(balance_message, parse_mode="Markdown", disable_web_page_preview=True)

application.add_handler(CommandHandler("tokens", tokens, block=False))

MAX_DAILY_TOKENS = 20000
COST_PER_TOKEN = 1000000
COOLDOWN_SECONDS = 300 

user_last_command_times = {}

LOG_GROUP_ID = -1001992198513

async def pay_tokens(update, context):
    sender_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🆘 Contact Support", url='https://t.me/dynamic_gangs')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if the user is still in cooldown
    if sender_id in cooldowns and (time.time() - cooldowns[sender_id]) < 1200:
        remaining_time = int(1200 - (time.time() - cooldowns[sender_id]))
        await update.message.reply_text(
            f"⏱️ Hold on! You can use /tpay again in {remaining_time // 60} minutes and {remaining_time % 60} seconds."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("🚫 Please reply to a user to send tokens using /tpay.")
        return

    recipient_id = update.message.reply_to_message.from_user.id

    try:
        amount = int(context.args[0])
        if amount < 0:
            raise ValueError("Negative amounts are not allowed.")
    except (IndexError, ValueError):
        await update.message.reply_text("❗ Invalid amount. Usage: /tpay <amount>")
        return

    # Check if the amount is greater than the maximum allowed
    if amount > MAX_DAILY_TOKENS:
        await update.message.reply_text(f"💸 You can’t transfer more than Ŧ{MAX_DAILY_TOKENS}.")
        return

    sender_balance = await user_collection.find_one({'id': sender_id}, projection={'tokens': 1})
    if not sender_balance or sender_balance.get('tokens', 0) < amount:
        await update.message.reply_text("⚠️ Not enough tokens for this transaction.")
        return

    disallowed_words = ['negative', 'badword']  # Add disallowed words here
    payment_message = update.message.text.lower()
    if any(word in payment_message for word in disallowed_words):
        await update.message.reply_text("🚫 Transaction message contains restricted words.")
        return

    # Process the payment
    await user_collection.update_one({'id': sender_id}, {'$inc': {'tokens': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'tokens': amount}})

    # Send a success message with enhanced formatting
    success_message = (
        f"🎉 <b>Success!</b> Ŧ Token Transfer Completed 🥂\n\n"
        f"👤 You sent <b>Ŧ{amount}</b> to <b>{update.message.reply_to_message.from_user.first_name}</b>.\n"
        f"💼 Updated Balance: <code>Ŧ{sender_balance['tokens'] - amount}</code>"
    )
    await update.message.reply_text(success_message, parse_mode='HTML')

    # Set the cooldown time for the user
    cooldowns[sender_id] = time.time()

    # Log payment information
    logs_message = (
        f"📜 <b>Transaction Log</b>\n"
        f"🔸 Sender: @{update.effective_user.username} (ID: {sender_id})\n"
        f"🔸 Amount: <b>Ŧ{amount}</b>\n"
        f"🔸 Recipient: @{update.message.reply_to_message.from_user.username} (ID: {recipient_id})"
    )

    for log_group_id in logs:
        try:
            await context.bot.send_message(log_group_id, logs_message, parse_mode='HTML')
        except Exception as e:
            print(f"Error sending transaction log to group {log_group_id}: {str(e)}")
            
@app.on_message(filters.command(["convert"]))
async def convert_tokens(client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("🔄 Please specify the amount: /convert <amount>")
            return

        user_id = message.from_user.id
        user_name = message.from_user.username
        amount = int(args[1])

        if amount <= 0:
            await message.reply_text("❌ Invalid amount. Please enter a positive number.")
            return

        if amount > MAX_DAILY_TOKENS:
            await message.reply_text(f"❌ Cannot buy more than {MAX_DAILY_TOKENS} tokens in one transaction.")
            return

        user = await user_collection.find_one({'id': user_id})

        if not user:
            await message.reply_text("⚠️ User not found.")
            return

        user_balance = user.get('balance', 0)
        total_cost = amount * COST_PER_TOKEN

        if user_balance < total_cost:
            await message.reply_text("❌ Insufficient balance. You need more coins to make this purchase.")
            return

        current_time = datetime.utcnow()

        # Cooldown check
        if user_id in user_last_command_times:
            last_command_time = user_last_command_times[user_id]
            if (current_time - last_command_time).total_seconds() < COOLDOWN_SECONDS:
                await message.reply_text("⏳ You are sending commands too quickly. Please wait a moment.")
                return

        # Check the last purchase time and the total tokens bought today
        last_purchase = user.get('last_purchase', None)
        tokens_bought_today = user.get('tokens_bought_today', 0)

        current_date = current_time.date()
        if last_purchase:
            last_purchase_date = datetime.strptime(last_purchase, "%Y-%m-%d").date()

            if last_purchase_date == current_date:
                if tokens_bought_today + amount > MAX_DAILY_TOKENS:
                    await message.reply_text(f"❌ Cannot buy more than {MAX_DAILY_TOKENS} tokens per day. You have already bought {tokens_bought_today} tokens today.")
                    return
            else:
                # Reset the daily count if the date has changed
                tokens_bought_today = 0

        new_balance = user_balance - total_cost
        new_token_count = user.get('tokens', 0) + amount
        tokens_bought_today += amount

        # Update the user document with the new balances and purchase details
        await user_collection.update_one(
            {'id': user_id},
            {
                '$set': {
                    'balance': new_balance,
                    'tokens': new_token_count,
                    'last_purchase': current_date.strftime("%Y-%m-%d"),
                    'tokens_bought_today': tokens_bought_today
                }
            }
        )

        await message.reply_text(
            f"✅ Purchase successful! You bought {amount} tokens for Ŧ{total_cost} cash. \n"
            f"💳 New Token balance: Ŧ{new_token_count}"
        )

        # Log the command use
        user_last_command_times[user_id] = current_time

        # Send log message to the specified group
        log_message = f'🔄 User {user_name} [{user_id}] converted {amount} tokens for {total_cost} cash. New Token balance: Ŧ{new_token_count}.'
        await send_log_message(client, log_message)

    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred: {str(e)}")

async def send_log_message(client, log_message):
    try:
        await client.send_message(chat_id=LOG_GROUP_ID, text=log_message)
    except Exception as e:
        print(f"⚠️ Error sending log message: {str(e)}")

async def addtokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("❌ You don't have permission to add tokens.")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("🔄 Invalid usage. Usage: /at <user_id> <amount>")
        return

    target_user_id = int(context.args[0])
    amount = int(context.args[1])

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("⚠️ User not found.")
        return

    # Update the balance by adding tokens
    await user_collection.update_one({'id': target_user_id}, {'$inc': {'tokens': amount}})
    await update.message.reply_text(f"✅ Added {amount} tokens to user {target_user_id}.")

async def deletetokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("❌ You don't have permission to delete tokens.")
        return

    # Check if the command includes the required arguments
    if len(context.args) != 2:
        await update.message.reply_text("🔄 Invalid usage. Usage: /dt <user_id> <amount>")
        return

    target_user_id = int(context.args[0])
    amount = int(context.args[1])

    # Find the target user
    target_user = await user_collection.find_one({'id': target_user_id})
    if not target_user:
        await update.message.reply_text("⚠️ User not found.")
        return

    if target_user['tokens'] < amount:
        await update.message.reply_text("❌ Insufficient tokens to delete.")
        return

    await user_collection.update_one({'id': target_user_id}, {'$inc': {'tokens': -amount}})
    await update.message.reply_text(f"✅ Deleted {amount} tokens from user {target_user_id}.")

application.add_handler(CommandHandler("at", addtokens, block=False))
application.add_handler(CommandHandler("dt", deletetokens, block=False))
