from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram.types import CallbackQuery
import asyncio
import random
from telegram import Update
from datetime import datetime, timedelta
from telegram.ext import CallbackContext
from pyrogram import Client, filters
from shivu import user_collection, collection, application

# User ID of the authorized user who can reset passes
AUTHORIZED_USER_ID = 6402009857

async def get_random_character():
    target_rarities = ['🔮 limited edition', '🟡 Legendary']  # Example rarities
    selected_rarity = random.choice(target_rarities)
    try:
        pipeline = [
            {'$match': {'rarity': selected_rarity}},
            {'$sample': {'size': 1}}  # Adjust Num
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(e)
        return []

async def get_user_data(user_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        user = {
            'id': user_id,
            'balance': 0,
            'tokens': 0,
            'pass': False,
            'pass_expiry': None,
            'daily_claims': 0,
            'weekly_claims': 0,
            'bonus_claimed': False,
            'last_claim_date': None,
            'last_weekly_claim_date': None,
            'pass_details': {
                'total_claims': 0,
                'daily_claimed': False,
                'weekly_claimed': False,
                'last_weekly_claim_date': None
            }
        }
        await user_collection.insert_one(user)
    return user

async def pass_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        # Button for purchasing a pass
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 ʙᴜʏ ᴘᴀss (30,000 ᴛᴏᴋᴇɴs)", callback_data=f'buy_pass:{user_id}')]
        ])
        await update.message.reply_html("<b>🚫 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss. ʙᴜʏ ᴏɴᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴇxᴛʀᴀ ʀᴇᴡᴀʀᴅs.</b>", reply_markup=keyboard)
        return
    
    pass_details = user_data.get('pass_details', {})
    pass_expiry_date = datetime.now() + timedelta(days=7)
    pass_details['pass_expiry'] = pass_expiry_date
    user_data['pass_details'] = pass_details
    
    total_claims = pass_details.get('total_claims', 0)
    pass_details['total_claims'] = total_claims
    
    await user_collection.update_one({'id': user_id}, {'$set': user_data})
    
    pass_expiry = pass_expiry_date.strftime("%m-%d")
    daily_claimed = "✅" if pass_details.get('daily_claimed', False) else "❌"
    weekly_claimed = "✅" if pass_details.get('weekly_claimed', False) else "❌"
    
    pass_info_text = (
        f"❰ 𝗦 𝗘 𝗜 𝗭 𝗘  𝗣 𝗔 𝗦 𝗦 🎟️ ❱\n"
        f"▰▱▰▱▰▱▰▱▰▱\n\n"
        f"✤ **ᴏᴡɴᴇʀ ᴏғ ᴘᴀss:** {update.effective_user.first_name}\n"
        f"───────────────\n"
        f"✤ **ᴅᴀɪʟʏ ᴄʟᴀɪᴍᴇᴅ:** {daily_claimed}\n"
        f"✤ **ᴡᴇᴇᴋʟʏ ᴄʟᴀɪᴍᴇᴅ:** {weekly_claimed}\n"
        f"✤ **ᴛᴏᴛᴀʟ ᴄʟᴀɪᴍs:** {total_claims}\n"
        f"───────────────\n"
        f"✤ **ᴘᴀss ᴇxᴘɪʀʏ:** {pass_expiry}\n"
        f"✤ **ᴄʟᴀɪᴍ ʀᴇsᴇᴛ:** sᴜɴᴅᴀʏ ᴀᴛ 00:00 ᴜᴛᴄ"
    )
    
    await update.message.reply_text(pass_info_text, parse_mode="Markdown")

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query_data = query.data.split(':')
    action = query_data[0]
    user_id = int(query_data[1])
    
    # Verify user authorization
    if query.from_user.id != user_id:
        await query.answer("🚫 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴜᴛᴛᴏɴ.", show_alert=True)
        return
    
    if action == 'buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("✅ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss.", show_alert=True)
            return
        
        if user_data['tokens'] < 30000:
            await query.answer("💔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ᴛᴏᴋᴇɴs ᴛᴏ ʙᴜʏ ᴀ ᴘᴀss.", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✔️ ᴄᴏɴғɪʀᴍ ᴘᴜʀᴄʜᴀsᴇ", callback_data=f'confirm_buy_pass:{user_id}')],
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴜʀᴄʜᴀsᴇ", callback_data=f'cancel_buy_pass:{user_id}')],
        ])
        await query.message.edit_text(
            "💳 **ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙᴜʏ ᴀ ᴘᴀss ғᴏʀ 30,000 ᴛᴏᴋᴇɴs?**\n\n"
            "🛡️ ᴛʜɪs ᴘᴀss ᴜɴʟᴏᴄᴋs sᴘᴇᴄɪᴀʟ ғᴇᴀᴛᴜʀᴇs ᴀɴᴅ ʀᴇᴡᴀʀᴅs!",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif action == 'claim_free_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("✅ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss.", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✔️ ᴄᴏɴғɪʀᴍ ᴄʟᴀɪᴍ", callback_data=f'confirm_claim_free_pass:{user_id}')],
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴄʟᴀɪᴍ", callback_data=f'cancel_claim_free_pass:{user_id}')],
        ])
        await query.message.edit_text(
            "🎁 **Are you sure you want to claim a free pass?**\n\n"
            "✨ This pass grants you access to exclusive content!",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
async def confirm_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query_data = query.data.split(':')
    action = query_data[0]
    user_id = int(query_data[1])
    
    # Verify user authorization
    if query.from_user.id != user_id:
        await query.answer("🚫 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴜᴛᴛᴏɴ.", show_alert=True)
        return
    
    if action == 'confirm_buy_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("✅ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss.", show_alert=True)
            return
        
        user_data['tokens'] -= 30000
        user_data['pass'] = True
        await user_collection.update_one({'id': user_id}, {'$set': {'tokens': user_data['tokens'], 'pass': True}})
        
        await query.message.edit_text(
            "🎉 **ᴘᴀss sᴜᴄᴄᴇssғᴜʟʟʏ ᴘᴜʀᴄʜᴀsᴇᴅ!**\n"
            "✨ ᴇɴᴊᴏʏ ʏᴏᴜʀ ɴᴇᴡ ʙᴇɴᴇғɪᴛs ᴀɴᴅ ᴇxᴄʟᴜsɪᴠᴇ ғᴇᴀᴛᴜʀᴇs! 🌟",
            parse_mode='Markdown'
        )
    
    elif action == 'cancel_buy_pass':
        await query.message.edit_text("❌ **ᴘᴜʀᴄʜᴀsᴇ ᴄᴀɴᴄᴇʟᴇᴅ.**\n\n"
                                       "ɪғ ʏᴏᴜ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ᴍɪɴᴅ, ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ ᴛʀʏ ᴀɢᴀɪɴ!")

    elif action == 'confirm_claim_free_pass':
        user_data = await get_user_data(user_id)
        if user_data.get('pass'):
            await query.answer("✅ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss.", show_alert=True)
            return
        
        user_data['pass'] = True
        pass_details = {
            'pass_expiry': datetime.now() + timedelta(days=7),
            'total_claims': 0,
            'daily_claimed': False,
            'weekly_claimed': False
        }
        user_data['pass_details'] = pass_details
        
        await user_collection.update_one({'id': user_id}, {'$set': user_data})
        
        await query.message.edit_text(
            "🎁 **Free pass successfully claimed!**\n"
            "🌈 Welcome to a world of exclusive benefits! Enjoy! 🎊",
            parse_mode='Markdown'
        )
    
    elif action == 'cancel_claim_free_pass':
        await query.message.edit_text("❌ **Claim canceled.**\n"
                                       "If you wish to claim your free pass later, just let me know!")

async def claim_daily_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html(
            f"<b>🚫 {user_name}, ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss. "
            "ʙᴜʏ ᴏɴᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴇxᴛʀᴀ ʀᴇᴡᴀʀᴅs!\n\n"
            "🛒 ᴜsᴇ /pass ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴀ ᴘᴀss.</b>"
        )
        return
    
    pass_details = user_data.get('pass_details', {})
    last_claim_date = pass_details.get('last_claim_date')
    
    if last_claim_date:
        time_since_last_claim = datetime.now() - last_claim_date
        if time_since_last_claim < timedelta(hours=24):
            remaining_time = timedelta(hours=24) - time_since_last_claim
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            await update.message.reply_html(
                f"<b>⏳ {user_name}, ʏᴏᴜ ᴄᴀɴ ᴏɴʟʏ ᴄʟᴀɪᴍ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅs ᴏɴᴄᴇ ᴇᴠᴇʀʏ 24 ʜᴏᴜʀs. "
                f"ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {int(hours)}ʜ {int(minutes)}ᴍ {int(seconds)}s ʙᴇғᴏʀᴇ ʏᴏᴜʀ ɴᴇxᴛ ᴄʟᴀɪᴍ.</b>"
            )
            return

    # Get the current day of the week
    today = datetime.now().weekday()

    # Set rewards for each day
    daily_rewards = {
        0: 1000,  # Monday
        1: 500,   # Tuesday
        2: 1500,  # Wednesday
        3: 5000,  # Thursday
        4: 1500,  # Friday
        5: 3000,  # Saturday
        6: 5000   # Sunday
    }

    daily_reward = daily_rewards.get(today, 500)  # Default to 500 if day not found

    characters = await get_random_character()
    if not characters:
        await update.message.reply_html(
            f"<b>❌ {user_name}, ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴀ ʀᴀɴᴅᴏᴍ ᴄʜᴀʀᴀᴄᴛᴇʀ ғᴏʀ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ.</b>"
        )
        return

    character = characters[0]
    character_info_text = (
        f"<b>❄️ ᴄʜᴀʀᴀᴄᴛᴇʀ: {character['name']}</b> ғʀᴏᴍ <i>{character['anime']}</i>:\n"
        f"⚜️ ʀᴀʀɪᴛʏ: {character['rarity']}\n"
    )
    
    pass_details['last_claim_date'] = datetime.now()
    pass_details['daily_claimed'] = True
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1
    
    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'tokens': daily_reward},
            '$set': {'pass_details': pass_details},
            '$push': {'characters': character}
        }
    )
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=character['img_url'],
        caption=(
            f"🎁 ❰ <b>𝗗 𝗔 𝗜 𝗟 𝗬 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 🎉</b> ❱\n\n"
            f"{character_info_text}\n"
            f"💰 ʀᴇᴡᴀʀᴅ: <b>{daily_reward} ᴛᴏᴋᴇɴs</b> 🎊"
        ),
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )
    
async def claim_weekly_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html(
            "<b>🚫 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss. "
            "ʙᴜʏ ᴏɴᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴇxᴛʀᴀ ʀᴇᴡᴀʀᴅs!\n\n"
            "🛒 ᴜsᴇ /pass ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴀ ᴘᴀss.</b>"
        )
        return
    
    pass_details = user_data.get('pass_details', {})
    if pass_details.get('total_claims', 0) < 6:
        await update.message.reply_html(
            "<b>⚠️ ʏᴏᴜ ᴍᴜsᴛ ᴄʟᴀɪᴍ ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅs ᴀᴛ ʟᴇᴀsᴛ 6 ᴛɪᴍᴇs ᴛᴏ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴡᴇᴇᴋʟʏ ʀᴇᴡᴀʀᴅ.</b>"
        )
        return

    today = datetime.utcnow()
    last_weekly_claim_date = pass_details.get('last_weekly_claim_date')
    if last_weekly_claim_date and (today - last_weekly_claim_date).days <= 7:
        await update.message.reply_html(
            "<b>❌ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴡᴇᴇᴋʟʏ ʀᴇᴡᴀʀᴅ ᴛʜɪs ᴡᴇᴇᴋ.</b>"
        )
        return

    weekly_reward = 5000
    pass_details['weekly_claimed'] = True
    pass_details['last_weekly_claim_date'] = today
    pass_details['total_claims'] = pass_details.get('total_claims', 0) + 1
    
    await user_collection.update_one(
        {'id': user_id},
        {
            '$inc': {'tokens': weekly_reward},
            '$set': {'pass_details': pass_details}
        }
    )
    
    await update.message.reply_html(
        "<b>🎉 ❰ 𝗪 𝗘 𝗘 𝗸 𝗟 𝗬 𝗥 𝗘 𝗪 𝗔 𝗥 𝗗 🎁 ❱\n\n"
        f"🏆 <b>{weekly_reward} ᴛᴏᴋᴇɴs</b> sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴀɪᴍᴇᴅ!</b>"
    )

async def claim_pass_bonus_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    
    if not user_data.get('pass'):
        await update.message.reply_html(
            "<b>🚫 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴘᴀss. "
            "ʙᴜʏ ᴏɴᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴇxᴛʀᴀ ʀᴇᴡᴀʀᴅs!\n\n"
            "🛒 ᴜsᴇ /pass ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴀ ᴘᴀss.</b>"
        )
        return
    
    current_streak = user_data.get('streak', 0)
    if current_streak < 10:
        await update.message.reply_html(
            f"<b>⚡️ ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴍᴀɪɴᴛᴀɪɴ ᴀ sᴛʀᴇᴀᴋ ᴏғ 10 ɪɴ /guess ᴛᴏ ᴄʟᴀɪᴍ ᴛʜᴇ ᴘᴀss ʙᴏɴᴜs.\n"
            f"ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ: {current_streak}⚡️.</b>"
        )
        return

    PASS_BONUS_TOKENS = 500  
    await user_collection.update_one({'id': user_id}, {
        '$inc': {'tokens': PASS_BONUS_TOKENS},
        '$set': {'streak': 0}
    })

    await update.message.reply_html(
        "<b>🎊 ❰ 𝗣 𝗔 𝗦 𝗦 𝗕 𝗢 𝗡 𝗨 𝗦 🎁 ❱\n"
        f"💰 <b>{PASS_BONUS_TOKENS} ᴛᴏᴋᴇsɴ</b> ᴀᴡᴀʀᴅᴇᴅ! ʏᴏᴜʀ sᴛʀᴇᴀᴋ ʜᴀs ʙᴇᴇɴ ʀᴇsᴇᴛ.</b>"
    )

async def reset_passes_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if the user issuing the command is the authorized user
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_html(
            "<b>🔒 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ʀᴇsᴇᴛ ᴘᴀssᴇs.</b>"
        )
        return

    # Reset the pass status for all users
    await user_collection.update_many(
        {},
        {
            '$set': {
                'pass': False,
                'pass_details': {
                    'total_claims': 0,
                    'daily_claimed': False,
                    'weekly_claimed': False,
                    'last_weekly_claim_date': None,
                    'pass_expiry': None
                }
            }
        }
    )
    
    await update.message.reply_html(
        "<b>🔄 ᴀʟʟ ᴘᴀssᴇs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇsᴇᴛ. ᴜsᴇʀs ᴡɪʟʟ ɴᴇᴇᴅ ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴀɢᴀɪɴ.</b>"
        )

# Register the command handler
application.add_handler(CommandHandler("wbonus", claim_pass_bonus_cmd))
application.add_handler(CommandHandler("pass", pass_cmd, block=False))
application.add_handler(CommandHandler("claim", claim_daily_cmd, block=False))
application.add_handler(CommandHandler("weekly", claim_weekly_cmd, block=False))
application.add_handler(CommandHandler("rpass", reset_passes_cmd, block=False))
application.add_handler(CallbackQueryHandler(button_callback, pattern='buy_pass:.*|claim_free_pass:.*', block=False))
application.add_handler(CallbackQueryHandler(confirm_callback, pattern='confirm_buy_pass:.*|cancel_buy_pass:.*|confirm_claim_free_pass:.*|cancel_claim_free_pass:.*', block=False))
    
