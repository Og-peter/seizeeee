from pyrogram import filters
from shivu import db, user_collection, SPECIALGRADE, GRADE1
from shivu import shivuu as app
import random
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
import asyncio  # To handle delays for animated messages

# Define collections and constants
backup_collection = db["backup_collection"]
logs_collection = db["logs_collection"]
COOLDOWN_TIME = timedelta(minutes=5)
reward_for_restoring = 1000  # Reward for reversing an erase operation
destroy_cost = 200  # Cost to erase a character

# Helper function to log actions
async def log_action(destroyer_id, target_id, action, details=""):
    await logs_collection.insert_one({
        'destroyer_id': eraser_id,
        'target_id': target_id,
        'action': action,
        'details': details,
        'timestamp': datetime.utcnow()
    })

# Backup characters before erasure
async def backup_characters(user_id, characters):
    await backup_collection.insert_one({'user_id': user_id, 'characters': characters})

# Function to erase characters from a user's collection
async def erase_characters_for_user(user_id, num_characters):
    user = await user_collection.find_one({'id': user_id})

    if user:
        total_characters = len(user.get('characters', []))
        
        if total_characters == 0:
            return f"⚠️ <a href='tg://user?id={user_id}'>{user.get('first_name', 'User')}</a> has no characters to destroy."

        num_characters_to_remove = min(num_characters, total_characters)
        
        characters_to_remove = random.sample(user['characters'], num_characters_to_remove)
        user_characters = [character for character in user['characters'] if character not in characters_to_remove]
        
        await backup_characters(user_id, user['characters'])  # Backup characters
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': user_characters}}
        )

        # Deduct balance for the destroy operation
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -destroy_cost * num_characters_to_remove}})

        return num_characters_to_remove, user.get('first_name', 'User')

    return 0, "not found"

# Send notifications to SpecialGrade users
async def send_notification_to_specialgrade(destroyer_id, destroyer_name, target_id, target_name, num_characters):
    message = (
        f"⚔️ **Destroy Characters Action** ⚔️\n"
        f"👤 **Destroer:** <a href='tg://user?id={destroyer_id}'>{destroyer_name}</a>\n"
        f"🎯 **Target:** <a href='tg://user?id={target_id}'>{target_name}</a>\n"
        f"🧹 **Characters destroyed:** {num_characters}\n"
        f"💥 Cost: {destroy_cost * num_characters} coins"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Reverse", callback_data=f"reverse_{target_id}")]
    ])
    for user_id in SPECIALGRADE:
        await app.send_message(user_id, message, reply_markup=keyboard)

# Restore erased characters
async def restore_characters(user_id):
    backup = await backup_collection.find_one({'user_id': user_id})
    if backup:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': backup['characters']}}
        )
        await backup_collection.delete_one({'user_id': user_id})
        return True
    return False

# Add cooldown system to prevent frequent erases
destroy_timestamps = {}

# Animation function after erasure
async def send_destroy_animation(message, user_id, num_characters):
    animation_steps = [
        "💥 Destroying in progress... 💥",
        "🧹 Cleaning up the characters... 🧹",
        "🌀 Wiping traces from the universe... 🌀",
        f"❌ {num_characters} characters from <a href='tg://user?id={user_id}'>the user</a> have been completely destroyed! 💀"
    ]
    
    for step in animation_steps:
        await message.edit_text(step)
        await asyncio.sleep(1.5)  # Delay for the animation effect

@app.on_message(filters.command(["destroy"]))
async def destroy_characters_command(client, message):
    destroyer_id = message.from_user.id
    if str(destroyer_id) not in SPECIALGRADE and str(destroyer_id) not in GRADE1:
        await message.reply_text("⚠️ This command is restricted to Special Grade and Grade 1 users.")
        return

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id

        if target_id == destroyer_id:
            await message.reply_text("❌ You cannot erase your own characters! 💀")
            return
        
        if len(message.command) != 2 or not message.command[1].isdigit():
            await message.reply_text("Usage: /destroy {num_characters}")
            return

        num_characters_to_destroy = int(message.command[1])

        # Check for cooldown
        last_destroy_time = destroy_timestamps.get(destroyer_id)
        if last_destroy_time and datetime.utcnow() - last_destroy_time < COOLDOWN_TIME:
            cooldown_remaining = COOLDOWN_TIME - (datetime.utcnow() - last_destroy_time)
            await message.reply_text(f"⏳ You need to wait {cooldown_remaining.seconds // 60} minutes before using this command again.")
            return

        # Send confirmation before destroying 
        confirm_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Confirm Destroy", callback_data=f"confirm_erase_{target_id}_{num_characters_to_destroy}")]
        ])
        await message.reply_text(
            f"⚠️ Are you sure you want to destroy {num_characters_to_destroy} characters from <a href='tg://user?id={target_id}'>{message.reply_to_message.from_user.first_name}</a>? This will cost {erase_cost * num_characters_to_erase} coins.",
            reply_markup=confirm_keyboard
        )

    else:
        await message.reply_text("Please reply to a user's message to erase their characters.")


@app.on_callback_query(filters.regex(r"^confirm_destroy_\d+_\d+$"))
async def confirm_destroy(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    target_id = int(data[2])
    num_characters_to_erase = int(data[3])
    destroyer_id = callback_query.from_user.id

    # Perform the destroy action
    num_destroyed, user_name = await destroy_characters_for_user(target_id, num_characters_to_destroy)
    if num_destroyed > 0:
        # Send animated message
        await send_destroy_animation(callback_query.message, target_id, num_characters_to_destroy)
        
        destroyer_name = callback_query.from_user.first_name
        target_name = (await app.get_users(target_id)).first_name
        await send_notification_to_specialgrade(destroyer_id, destroyer_name, target_id, target_name, num_characters_to_destroy)
        await log_action(destroyer_id, target_id, "destroy", f"Destroyed {num_characters_to_destroy} characters.")
        destroy_timestamps[destroyer_id] = datetime.utcnow()

    else:
        await callback_query.message.edit_text("❌ Unable to destroy characters.")

@app.on_callback_query(filters.regex(r"^reverse_\d+$"))
async def reverse_erase(client, callback_query: CallbackQuery):
    target_id = int(callback_query.data.split("_")[1])
    destroyer_id = callback_query.from_user.id

    if str(destroyer_id) in SPECIALGRADE:
        restored = await restore_characters(target_id)
        if restored:
            await callback_query.answer("✅ The destroy operation has been reversed. Characters restored! 💫")
            await callback_query.edit_message_text("🔄 The destroy operation has been successfully reversed.")
            
            # Reward for restoring characters
            await user_collection.update_one({'id': target_id}, {'$inc': {'balance': reward_for_restoring}})
            await callback_query.message.reply_text(f"🎁 {reward_for_restoring} coins have been rewarded to <a href='tg://user?id={target_id}'>the user</a> for reversing the destroy operation.")
            
            await log_action(destroyer_id, target_id, "restore", "Characters restored after erasure.")
        else:
            await callback_query.answer("⚠️ No backup found to restore.", show_alert=True)
    else:
        await callback_query.answer("❌ You do not have permission to reverse this operation.", show_alert=True)
