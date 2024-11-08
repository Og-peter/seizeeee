import os
import logging 
import random
import html
from html import escape
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (application, PHOTO_URL, OWNER_ID,
                   user_collection, top_global_groups_collection,
                   group_user_totals_collection, db)
from shivu import sudo_users as SUDO_USERS

# Fetch from your specific collections
groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

# List of video links
video = [
    "https://files.catbox.moe/x7cjqd.mp4",
    "https://files.catbox.moe/d5uiqt.mp4",
]

# Function to display the global leaderboard of top groups
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    try:
        # Fetch the top 10 groups based on count
        cursor = top_global_groups_collection.aggregate([
            {"$project": {"group_name": 1, "count": 1}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        
        # Load leaderboard data
        leaderboard_data = await cursor.to_list(length=10)

        # Debugging: Log fetched data
        logging.info("Fetched leaderboard data: %s", leaderboard_data)

        # Check if leaderboard data is empty
        if not leaderboard_data:
            await update.message.reply_text("🚫 No data available for the top groups leaderboard.", parse_mode='HTML')
            return

        # Prepare the leaderboard message
        leaderboard_message = "<b>🌟 𝚃𝙾𝙿 10 𝙶𝚁𝙾𝚄𝙿𝚂 🌟</b>\n"
        leaderboard_message += "─────────────────────\n"
        
        for i, group in enumerate(leaderboard_data, start=1):
            group_name = escape(group.get('group_name', 'Unknown'))
            if len(group_name) > 15:
                group_name = group_name[:15] + '...'
            count = group.get('count', 0)
            leaderboard_message += f"{i}. <b>{group_name}</b> - <b>{count}</b> 🏆\n"

        leaderboard_message += "─────────────────────\n"
        leaderboard_message += "✨ 𝚃𝚘𝚙 𝙶𝚛𝚘𝚞𝚙𝚜 𝚟𝚒𝚊 @Character_seize_bot ✨"

        # Select a random video from the list and send it with the leaderboard message
        video_url = random.choice(video)
        await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')

    except Exception as e:
        logging.error("Error in global_leaderboard: %s", e)
        await update.message.reply_text(f"⚠️ 𝔸𝕟 𝕖𝕣𝕣𝕠𝕣 𝕠𝕔𝕔𝕦𝕣𝕖𝕕: {e}", parse_mode='HTML')

# Function to display the top users in the current chat
async def ctop(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        cursor = group_user_totals_collection.aggregate([
            {"$match": {"group_id": chat_id}},
            {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
            {"$sort": {"character_count": -1}},
            {"$limit": 10}
        ])
        leaderboard_data = await cursor.to_list(length=10)

        leaderboard_message = "<b>✨ 𝚃𝙾𝙿 10 𝚄𝚂𝙴𝚁𝚂 𝙸𝙽 𝚃𝙷𝙸𝚂 𝙲𝙷𝙰𝚃 ✨</b>\n"
        leaderboard_message += "─────────────────────\n"
        
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = escape(user.get('first_name', 'Unknown'))
            if len(first_name) > 15:
                first_name = first_name[:15] + '...'
            character_count = user['character_count']
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> - <b>{character_count}</b> 🌟\n'

        leaderboard_message += "─────────────────────\n"
        leaderboard_message += "✨ 𝚃𝚘𝚙 𝚄𝚜𝚎𝚛𝚜 𝚟𝚒𝚊 @Character_seize_bot ✨"

        # Select a random video from the list and send it with the leaderboard message
        video_url = random.choice(video)
        await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f"⚠️ 𝔸𝕟 𝕖𝕣𝕣𝕠𝕣 𝕠𝕔𝕔𝕦𝕣𝕖𝕕: {e}", parse_mode='HTML')

# Function to display the global user leaderboard
async def leaderboard(update: Update, context: CallbackContext) -> None:
    try:
        cursor = user_collection.aggregate([
            {"$match": {"characters": {"$exists": True, "$type": "array"}}},
            {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
            {"$sort": {"character_count": -1}},
            {"$limit": 10}
        ])
        leaderboard_data = await cursor.to_list(length=10)

        # Enhanced leaderboard message with unique styling
        leaderboard_message = "<b>🏆 𝗧𝗼𝗽 𝟭𝟬 𝗨𝘀𝗲𝗿𝘀 𝘄𝗶𝘁𝗵 𝗺𝗼𝘀𝘁 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 🏆</b>\n"
        leaderboard_message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = escape(user.get('first_name', 'Unknown'))
            if len(first_name) > 15:
                first_name = first_name[:15] + '...'
            character_count = user['character_count']
            leaderboard_message += f'<b>{i}. <a href="https://t.me/{username}">{first_name}</a></b> — <code>{character_count}</code> ✨\n'

        leaderboard_message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        leaderboard_message += "🌟 𝑻𝒐𝒑 𝑼𝒔𝒆𝒓𝒔 𝒗𝒊𝒂 @Character_seize_bot 🌟"

        # Select a random video from the list and send it with the leaderboard message
        video_url = random.choice(video)
        await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f"⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱: {e}", parse_mode='HTML')
      
# Function to send a document listing all users
async def send_users_document(update: Update, context: CallbackContext) -> None:
    try:
        if str(update.effective_user.id) not in SUDO_USERS:
            await update.message.reply_text('Only for sudo users...')
            return

        cursor = user_collection.find({})
        users = []
        async for document in cursor:
            users.append(document)
        user_list = "\n".join([user['first_name'] for user in users])

        with open('users.txt', 'w') as f:
            f.write(user_list)
        with open('users.txt', 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

        os.remove('users.txt')

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Function to send a document listing all groups
async def send_groups_document(update: Update, context: CallbackContext) -> None:
    try:
        if str(update.effective_user.id) not in SUDO_USERS:
            await update.message.reply_text('Only for sudo users...')
            return

        cursor = top_global_groups_collection.find({})
        groups = []
        async for document in cursor:
            groups.append(document)
        group_list = "\n".join([group['group_name'] for group in groups])

        with open('groups.txt', 'w') as f:
            f.write(group_list)
        with open('groups.txt', 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

        os.remove('groups.txt')

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

  
# Register the command handlers
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('topGroups', global_leaderboard, block=False))

application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('gtop', leaderboard, block=False))
