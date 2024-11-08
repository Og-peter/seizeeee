#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
# For Waifu/Husbando telegram bots.
# Updated and Added new commands, features and style by https://github.com/lovetheticx
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
# <======================================= IMPORTS ==================================================>
import os
import random
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

from shivu import (application, OWNER_ID,
                   user_collection, top_global_groups_collection, 
                   group_user_totals_collection, sudo_users as SUDO_USERS)

# Replace PHOTO_URL with a list of video URLs
VIDEO_URL = [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/video3.mp4"
]

# <======================================= GLOBAL TOP GROUPS ==================================================>
async def global_leaderboard(update: Update, context: CallbackContext, query=None) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>🥂 𝗧𝗢𝗣 𝟭𝟬 𝗚𝗟𝗢𝗕𝗔𝗟 𝗚𝗥𝗢𝗨𝗣𝗦:</b>\n\n"
    leaderboard_message += "┏━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┓\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'┣ {i:02d}.  <b>{group_name}</b> ➾ <b>{count}</b>\n'
    leaderboard_message += "┗━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┛\n"

    video_url = random.choice(VIDEO_URL)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❂ ɢʟᴏʙᴀʟ ᴛᴏᴘ ❂", callback_data="global_users")],
        [InlineKeyboardButton("❖ ᴄʜᴀᴛ ᴛᴏᴘ ❖", callback_data="ctop")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ⊗", callback_data="close")]
    ])

    if query:
        await query.edit_message_caption(caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
    else:
        message = await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
        context.chat_data['leaderboard_message_id'] = message.message_id

# <======================================= TOP USERS IN THIS GROUP ==================================================>
async def ctop(update: Update, context: CallbackContext, query=None) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>🍁 𝗧𝗢𝗣 𝟭𝟬 𝗨𝗦𝗘𝗥𝗦 𝗜𝗡 𝗧𝗛𝗜𝗦 𝗖𝗛𝗔𝗧:</b>\n\n"
    leaderboard_message += "┏━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┓\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f"┣ {i:02d}. <a href='https://t.me/{username}'>{first_name}</a> ⇒ {character_count}\n"
    leaderboard_message += "┗━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┛\n"

    video_url = random.choice(VIDEO_URL)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❂ ɢʟᴏʙᴀʟ ᴛᴏᴘ ❂", callback_data="global_users")],
        [InlineKeyboardButton("▣ ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ▣", callback_data="global")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ⊗", callback_data="close")]
    ])

    if query:
        await query.edit_message_caption(caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
    else:
        message = await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
        context.chat_data['leaderboard_message_id'] = message.message_id

# <======================================= GLOBAL TOP USERS ==================================================>
async def global_users_leaderboard(update: Update, context: CallbackContext, query=None) -> None:
    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>❄️ 𝗚𝗟𝗢𝗕𝗔𝗟 𝗧𝗢𝗣 𝟭𝟬 𝗨𝗦𝗘𝗥𝗦:</b>\n\n"
    leaderboard_message += "┏━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┓\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f"┣ {i:02d}. <a href='https://t.me/{username}'>{first_name}</a> ⇒ {character_count}\n"

    leaderboard_message += "┗━┅┅┄┄⟞⟦🌐⟧⟝┄┄┉┉━┛\n"

    video_url = random.choice(VIDEO_URL)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❖ ᴄʜᴀᴛ ᴛᴏᴘ ❖", callback_data="ctop")],
        [InlineKeyboardButton("▣ ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ▣", callback_data="global")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ⊗", callback_data="close")]
    ])

    if query:
        await query.edit_message_caption(caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
    else:
        message = await update.message.reply_video(video=video_url, caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
        context.chat_data['leaderboard_message_id'] = message.message_id

# <======================================= CALLBACK ==================================================>
async def callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data == "close":
        message_id = context.chat_data.get('leaderboard_message_id')
        if message_id:
            await query.message.delete()
            del context.chat_data['leaderboard_message_id']
    elif data == "ctop":
        await ctop(update, context, query)
    elif data == "global":
        await global_leaderboard(update, context, query)
    elif data == "global_users":
        await global_users_leaderboard(update, context, query)


application.add_handler(CallbackQueryHandler(callback_query))

# <======================================= FOR CHANNEL STATS ==================================================>
async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != 6558846590:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')
    await update.message.reply_text(f'💮 Total Users: {user_count}\n💮 Total groups: {len(group_count)}')

# <======================================= TO GET USERS ==================================================>
async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('Only For Sudo users...')
        return
    cursor = user_collection.find({})
    users = []
    async for document in cursor:
        users.append(document)
    user_list = "\n".join([user['first_name'] for user in users])
    with open('users.txt', 'w', encoding='utf-8') as f:
        f.write(user_list)
    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('users.txt')

# <======================================= TO GET GROUPS ==================================================>
async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('Only For Sudo users...')
        return
    cursor = top_global_groups_collection.find({})
    groups = []
    async for document in cursor:
        groups.append(document)
    group_list = "\n".join([group['group_name'] for group in groups])
    with open('groups.txt', 'w', encoding='utf-8') as f:
        f.write(group_list)
    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
    os.remove('groups.txt')


application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('topgroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('gtop', global_users_leaderboard, block=False))

# by https://github.com/lovetheticx
