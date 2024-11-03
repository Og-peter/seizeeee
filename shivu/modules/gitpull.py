import os
import subprocess
import sys
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu as app, SPECIALGRADE

# Add SUDO list to manage sudo users
SUDO = set(SPECIALGRADE)  # Initialize SUDO list with initial SPECIALGRADE

@app.on_message(filters.command("gitpull"))
async def git_pull_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    await message.reply("Pulling from the repo... please wait.")

    try:
        result = subprocess.run(
            ["git", "pull", "https://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@github.com/Itachiuchiha786786/seizeeee", "main"],
            capture_output=True, text=True, check=True, timeout=60
        )

        if "Already up to date" in result.stdout:
            return await message.reply("✅ Repo is already up to date.")
        elif result.returncode == 0:
            await message.reply(f"✅ Git pull successful! Updating the bot now...\n\n`{result.stdout}`")
            await restart_bot(message)
        else:
            await message.reply("❌ Git pull failed. Please check the logs.")

    except subprocess.CalledProcessError as e:
        await message.reply(f"❌ Git pull failed with error:\n`{e.stderr}`")
    except subprocess.TimeoutExpired:
        await message.reply("❌ Git pull timed out. Please check your connection and try again.")
    except Exception as e:
        await message.reply(f"❌ Unexpected error occurred: {str(e)}")

# Function to handle restarting the bot
async def restart_bot(message):
    await message.reply("`Restarting the bot...`")

    try:
        args = [sys.executable, "-m", "shivu"]  # Adjust this line to your bot's main file/module
        subprocess.Popen(args)
        sys.exit()  # Ensure the bot exits cleanly before restarting
    except Exception as e:
        await message.reply(f"❌ Failed to restart the bot. Error: {str(e)}")

# Command to restart the bot directly
@app.on_message(filters.command("restart"))
async def restart_command(client, message):
    if str(message.from_user.id) not in SUDO:
        await message.reply("You are not authorized to use this command.")
        return
    await restart_bot(message)

# Command to check bot status
@app.on_message(filters.command("bot"))
async def status_check_command(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    await message.reply("✅ Bot is up and running!")

# Command to add a user to the SUDO list
@app.on_message(filters.command("addog"))
async def add_sudo_user(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Please reply to a user's message to add them as Sudo.")

    user_id = str(message.reply_to_message.from_user.id)
    SUDO.add(user_id)

    # Display a confirmation message with a Restart button
    restart_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔄 Restart Bot", callback_data="restart_bot")]]
    )
    await message.reply(f"✅ Added {message.reply_to_message.from_user.mention} to Sudo users!", reply_markup=restart_button)

# Command to remove a user from the SUDO list
@app.on_message(filters.command("rmog"))
async def remove_sudo_user(client, message):
    if str(message.from_user.id) not in SPECIALGRADE:
        await message.reply("You are not authorized to use this command.")
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Please reply to a user's message to remove them from Sudo.")

    user_id = str(message.reply_to_message.from_user.id)
    if user_id in SUDO:
        SUDO.remove(user_id)
        await message.reply(f"✅ Removed {message.reply_to_message.from_user.mention} from Sudo users!")
    else:
        await message.reply("User is not a Sudo user.")

# Callback for restart button
@app.on_callback_query(filters.regex("restart_bot"))
async def on_restart_callback(client, callback_query):
    if str(callback_query.from_user.id) not in SUDO:
        await callback_query.answer("You are not authorized to use this button.", show_alert=True)
        return

    await callback_query.message.edit_text("`Restarting the bot...`")
    await restart_bot(callback_query.message)
