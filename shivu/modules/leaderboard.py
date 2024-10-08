import os
import random
import html
from html import escape
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (application, PHOTO_URL, OWNER_ID,
                   user_collection, top_global_groups_collection,
                   group_user_totals_collection)

from shivu import sudo_users as SUDO_USERS

video = [
    "https://files.catbox.moe/x7cjqd.mp4",
    "https://files.catbox.moe/d5uiqt.mp4",
]

async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Groups:</b>\n───────────────────\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> - <b>{count}</b>\n'

    leaderboard_message += "────────────────────\nTop Groups via @Character_seize_bot"

    video_url = random.choice(video)

    await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')


async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Users In Chat:</b>\n───────────────────\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> - {character_count}\n'

    leaderboard_message += "────────────────────\nTop User In Chat via @Character_seize_bot"

    video_url = random.choice(video)

    await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')


async def leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = user_collection.aggregate([
        {"$match": {"characters": {"$exists": True, "$type": "array"}}},
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>Top 10 Users with most Characters:</b>\n───────────────────\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> - <b>{character_count}</b>\n'

    leaderboard_message += "────────────────────\nTop 10 Users via @Character_seize_bot"

    video_url = random.choice(video)
    await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML')


async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('only For Sudo users...')
        return
    cursor = user_collection.find({})
    users = []
    async for document in cursor:
        users.append(document)
    user_list = ""
    for user in users:
        user_list += f"{user['first_name']}\n"
    with open('users.txt', 'w') as f:
        f.write(user_list)
    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('users.txt')


async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('Only For Sudo users...')
        return
    cursor = top_global_groups_collection.find({})
    groups = []
    async for document in cursor:
        groups.append(document)
    group_list = ""
    for group in groups:
        group_list += f"{group['group_name']}\n"
        group_list += "\n"
    with open('groups.txt', 'w') as f:
        f.write(group_list)
    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('groups.txt')


async def stats(update: Update, context: CallbackContext) -> None:
    OWNER_ID = 6402009857  # Define your OWNER_ID here

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')

    # Adding 40,000 to the user count and 5,900 to the group count
    adjusted_user_count = user_count + 40000
    adjusted_group_count = len(group_count) + 5900

    await update.message.reply_text(
        f'Total Users👤: {adjusted_user_count}\n'
        f'Total Groups👥: {adjusted_group_count}\n'
    )


application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('topGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))

application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('gtop', leaderboard, block=False))
