from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.enums import ChatMemberStatus
import asyncio

# Developer user IDs and group/channel IDs
DEVS = (6402009857,)
SUPPORT_CHAT_ID = -1002104939708
CHANNEL_ID = -1002122552289

# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.start()

# Support group and channel buttons
keyboard_support = InlineKeyboardMarkup([
    [InlineKeyboardButton("Official Group", url="https://t.me/dynamic_gangs")]
])
keyboard_channel = InlineKeyboardMarkup([
    [InlineKeyboardButton("Official Channel", url="https://t.me/Seizer_updates")]
])
keyboard_both = InlineKeyboardMarkup([
    [InlineKeyboardButton("Official Group", url="https://t.me/dynamic_gangs")],
    [InlineKeyboardButton("Official Channel", url="https://t.me/Seizer_updates")]
])

# Function to check if a user is a member
async def check_membership(user_id):
    is_member_group = False
    is_member_channel = False
    valid_statuses = [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ]

    try:
        member_group = await bot.get_chat_member(SUPPORT_CHAT_ID, user_id)
        is_member_group = member_group.status in valid_statuses
    except UserNotParticipant:
        pass
    except Exception as e:
        print(f"Error checking group membership: {e}")

    try:
        member_channel = await bot.get_chat_member(CHANNEL_ID, user_id)
        is_member_channel = member_channel.status in valid_statuses
    except UserNotParticipant:
        pass
    except Exception as e:
        print(f"Error checking channel membership: {e}")

    return is_member_group, is_member_channel

# Function to get unique characters
async def get_unique_characters(receiver_id, target_rarities=['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']):
    try:
        user_data = await user_collection.find_one({'id': receiver_id})
        owned_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_character_ids}}},
            {'$sample': {'size': 1}}
        ]

        characters = await collection.aggregate(pipeline).to_list(length=1)
        if not characters:
            print("No characters found")
        return characters
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

# Function to notify users when their cooldown ends
async def send_cooldown_notification(user_id, mention):
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✨ Hello {mention}, your cooldown has ended! You can now claim a new character using the `/wclaim` command."
        )
    except Exception as e:
        print(f"Error sending cooldown notification to {user_id}: {e}")

# Main command function for wclaim with cooldown notifications
@bot.on_message(filters.command(["wclaim"]))
async def wclaim(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if user is banned
    if user_id in DEVS:
        return await message.reply("🚫 Sorry, you are banned from using this command.")

    # Membership check
    is_member_group, is_member_channel = await check_membership(user_id)
    
    if not is_member_group and not is_member_channel:
        return await message.reply_text(
            "To use this command, please join our official group and channel.",
            reply_markup=keyboard_both
        )
    elif not is_member_group:
        return await message.reply_text(
            "Please join the official group to use this command.",
            reply_markup=keyboard_support
        )
    elif not is_member_channel:
        return await message.reply_text(
            "Please join the official channel to use this command.",
            reply_markup=keyboard_channel
        )

    # Fetch user data or initialize if not present
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await user_collection.insert_one({'id': user_id, 'characters': [], 'last_claim_time': None})

    now = datetime.utcnow()
    last_claim_time = user_data.get('last_claim_time')

    if last_claim_time and last_claim_time.date() == now.date():
        next_claim_time = last_claim_time + timedelta(days=1)
        next_claim_time_str = next_claim_time.strftime("%H:%M:%S")
        return await message.reply_text(
            f"✨ You’ve already claimed today. Try again tomorrow at {next_claim_time_str}!"
        )

    # Animated sequence of claim messages
    animation_messages = [
        "🔥 **Getting your claim ready...**",
        "⚡ **Preparing the rewards...**",
        "❄️ **Almost there...**",
        "🎉 **Here comes your reward!**"
    ]
    animation_message = await message.reply_text(animation_messages[0])
    for msg in animation_messages[1:]:
        await asyncio.sleep(1)
        await animation_message.edit_text(msg)

    # Update last claim time and schedule a cooldown notification
    await user_collection.update_one({'id': user_id}, {'$set': {'last_claim_time': now}})
    scheduler.add_job(
        send_cooldown_notification,
        trigger=DateTrigger(run_date=now + timedelta(days=1)),
        args=[user_id, mention]
    )

    # Retrieve a unique character
    unique_characters = await get_unique_characters(user_id)
    if unique_characters:
        try:
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': unique_characters}}})
            for character in unique_characters:
                img_url = character.get('img_url')
                caption = (
                    f"🎉 Congratulations {mention}! You claimed a new character:\n\n"
                    f"🥂 Name: {character['name']}\n"
                    f"⛩️ Anime: {character['anime']}\n"
                    f"🍁 Rarity: {character['rarity']}\n\n"
                    f"Come back tomorrow for another chance!"
                )
                await message.reply_photo(photo=img_url, caption=caption)
        except Exception as e:
            print(f"Error claiming character: {e}")
            await message.reply("An error occurred while claiming your character. Please try again later.")
    else:
        await message.reply("No new characters available to claim. Try again tomorrow.")


# Command to reset claim cooldown
@bot.on_message(filters.command(["rclaim"]) & filters.user(DEVS))
async def reset_claim(_, message: t.Message):
    keyboard_confirm = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_reset")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset")]
    ])
    await message.reply("⚠️ Are you sure you want to reset the claim cooldown for all users?", reply_markup=keyboard_confirm)


@bot.on_callback_query(filters.regex("confirm_reset"))
async def confirm_reset(_, query: t.CallbackQuery):
    try:
        result = await user_collection.update_many({}, {'$unset': {'last_claim_time': 1}})
        await query.message.edit_text(f"✨ Claim cooldown reset for all users. ({result.modified_count} users affected)")
    except Exception as e:
        print(f"Error resetting claim cooldown: {e}")
        await query.message.edit_text("⚠️ An error occurred while resetting the claim cooldown.")


@bot.on_callback_query(filters.regex("cancel_reset"))
async def cancel_reset(_, query: t.CallbackQuery):
    await query.message.edit_text("🚫 Claim cooldown reset canceled.")
