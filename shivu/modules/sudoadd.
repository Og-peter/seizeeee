from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import shivuu as app
from shivu import sudo_users_collection, application
from shivu.modules.database.sudo import add_to_sudo_users, remove_from_sudo_users, get_user_username, fetch_sudo_users
import random

DEV_LIST = [6402009857]
authorized_users = [6402009857]

# Define a list of anime characters and superpowers to assign
characters = [
    "Naruto Uzumaki", "Sasuke Uchiha", "Goku", "Saitama", "Luffy", "Tanjiro Kamado"
]
powers = [
    "Shadow Clone Jutsu", "Sharingan", "Kamehameha", "One Punch", "Gear Fourth", "Water Breathing"
]

async def is_user_sudo(user_id: int) -> bool:
    user = await sudo_users_collection.find_one({"id": user_id})
    return bool(user)

async def add_sudo_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Check if the user is authorized
    if user_id not in authorized_users:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if update.message.reply_to_message:
        replied_user_id = update.message.reply_to_message.from_user.id
        username = await get_user_username(replied_user_id)
        sudo_title = ' '.join(context.args) if context.args else "Sudo User"
        await add_to_sudo_users(replied_user_id, username, sudo_title)

        # Notify the user in their DM
        character = random.choice(characters)
        power = random.choice(powers)
        message = (
            f"Congratulations {username}! 🎉\n\n"
            f"You are now a sudo user with the title '{sudo_title}'.\n"
            f"You've been given the character role of {character} and the power of '{power}'!\n"
            f"Use your new abilities wisely!"
        )
        try:
            await context.bot.send_message(replied_user_id, message)
        except Exception as e:
            print(f"Failed to send DM to {username}: {e}")
        
        await update.message.reply_text(f"User {username} has been added as sudo with title '{sudo_title}'.")
    else:
        await update.message.reply_text("Please reply to a message to add a user as sudo.")

async def remove_sudo_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Check if the user is authorized
    if user_id not in authorized_users:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if update.message.reply_to_message:
        replied_user_id = update.message.reply_to_message.from_user.id
        user = await sudo_users_collection.find_one({"id": replied_user_id})
        if user:
            await remove_from_sudo_users(replied_user_id)
            username = user.get('username')

            # Notify the user of removal in their DM
            try:
                await context.bot.send_message(replied_user_id, f"Hello {username}, you have been removed from the sudo users list.")
            except Exception as e:
                print(f"Failed to send DM to {username}: {e}")
            
            await update.message.reply_text(f"User {username} has been removed from sudo users.")
        else:
            await update.message.reply_text("User not found in sudo users.")
    else:
        await update.message.reply_text("Please reply to a message to remove a user from sudo.")

async def sudo_list_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Check if the user is a sudo user
    if not await is_user_sudo(user_id):
        await update.message.reply_text("You are not authorized to view the sudo list.")
        return

    sudo_users = await fetch_sudo_users()
    if not sudo_users:
        await update.message.reply_text("No sudo users found.")
        return

    message = "Sudo Users:\n"
    for user in sudo_users:
        message += f"User ID: {user['user_id']}, Username: @{user['username']}, Title: {user['sudo_title']}\n"
    
    await update.message.reply_text(message)

# Add command handlers
application.add_handler(CommandHandler("addsudo", add_sudo_command))
application.add_handler(CommandHandler("sudoremove", remove_sudo_command))
application.add_handler(CommandHandler("sudolist", sudo_list_command))
