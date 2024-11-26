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
    "https://files.catbox.moe/sab0z3.mp4",
    "https://files.catbox.moe/erfe6v.mp4",
    "https://files.catbox.moe/sab0z3.mp4"
]

# <======================================= GLOBAL TOP GROUPS ==================================================>
async def global_leaderboard(update: Update, context: CallbackContext, query=None) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    # Anime-themed message with kawaii words and unique fonts
    leaderboard_message = (
        "ʜᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴍᴏꜱᴛ ᴛᴏᴘ 𝟷𝟶 ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘꜱ ᴀʀᴀ ᴀʀᴀ~\n\n"
        "┏━⊱ 🌸 ᴛᴏᴘ 𝟷𝟶 ɢʀᴏᴜᴘꜱ 🌸 ⊰━┓\n"
    )

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))
        if len(group_name) > 10:
            group_name = group_name[:15] + '...'  # Truncate long names
        count = group['count']

        leaderboard_message += f"┣ {i:02d}.  <b>{group_name}</b> ➾ <b>{count}</b>\n"

    # Choose a random anime-themed video
    video_url = random.choice(VIDEO_URL)

    # Inline keyboard with anime-themed buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❂ ᴛᴏᴘ ᴏɴɪɪ-ᴄʜᴀɴꜱ ᴜsᴇʀs ❂", callback_data="global_users")],
        [InlineKeyboardButton("❖ ᴛᴏᴘ ᴄʜᴀᴛꜱ ❖", callback_data="ctop")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ᴀʀᴀ ᴀʀᴀ ⊗", callback_data="close")]
    ])

    if query:
        # Update existing message if query is passed
        await query.edit_message_caption(
            caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard
        )
    else:
        # Send a new message with the video and caption
        message = await update.message.reply_video(
            video=video_url, caption=leaderboard_message, parse_mode='HTML', reply_markup=keyboard
        )
        # Store the message ID in chat data
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

    leaderboard_message = (
        "<b>🌸 ᴋᴀᴡᴀɪɪ ᴛᴏᴘ 10 ᴜꜱᴇʀꜱ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ 🌸</b>\n\n"
        "┏━⊱ 💖 ᴏɴɪɪ-ᴄʜᴀɴ ꜰᴀᴠᴏʀɪᴛᴇꜱ 💖 ⊰━┓\n"
    )

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'  # Truncate long names
        character_count = user['character_count']
        leaderboard_message += f"┣ {i:02d}. <a href='https://t.me/{username}'>{first_name}</a> ⇒ <b>{character_count}</b>\n"

    video_url = random.choice(VIDEO_URL)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❂ ᴛᴏᴘ ɢʟᴏʙᴀʟ ᴜꜱᴇʀꜱ ❂", callback_data="global_users")],
        [InlineKeyboardButton("▣ ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ▣", callback_data="global")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ꜱᴇɴᴘᴀɪ ⊗", callback_data="close")]
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

    leaderboard_message = (
        "<b>🌟 ᴛᴏᴘ 10 ɢʟᴏʙᴀʟ ᴜꜱᴇʀꜱ 🌟</b>\n\n"
        "┏━⊱ ✨ ᴀᴍᴀᴢɪɴɢ ꜱᴏᴜʟꜱ ✨ ⊰━┓\n"
    )

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'  # Truncate long names
        character_count = user['character_count']
        leaderboard_message += f"┣ {i:02d}. <a href='https://t.me/{username}'>{first_name}</a> ⇒ <b>{character_count}</b>\n"

    video_url = random.choice(VIDEO_URL)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❖ ᴛᴏᴘ ᴄʜᴀᴛꜱ ❖", callback_data="ctop")],
        [InlineKeyboardButton("▣ ᴛᴏᴘ ɢʀᴏᴜᴘꜱ ▣", callback_data="global")],
        [InlineKeyboardButton("⊗ ᴄʟᴏꜱᴇ ꜱᴇɴᴘᴀɪ ⊗", callback_data="close")]
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


# <======================================= KEEPING ALL FEATURES ================================================>
application.add_handler(CallbackQueryHandler(callback_query))
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('topgroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('gtop', global_users_leaderboard, block=False))
