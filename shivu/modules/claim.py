from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta
import asyncio
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.enums import ChatMemberStatus

OWNER_ID = 123456789  # Replace with the owner user ID
DEVS = (6995317382,)
SUPPORT_CHAT_ID = -1002104939708
CHANNEL_ID = -1002122552289
COMMUNITY_GROUP_ID = -1002104939708

# Keyboards
keyboard_support = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap group", url="https://t.me/dynamic_gangs")]
])
keyboard_channel = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap W/H", url="https://t.me/Seizer_updates")]
])
keyboard_community = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Community Groups", url="https://t.me/dynamic_gangs")]
])
keyboard_all = t.InlineKeyboardMarkup([
    [t.InlineKeyboardButton("Official Grap W/H Groups", url="https://t.me/dynamic_gangs")],
    [t.InlineKeyboardButton("Official Grap W/H", url="https://t.me/Seizer_updates")],
    [t.InlineKeyboardButton("Community Groups", url="https://t.me/dynamic_gangs")]
])


async def check_membership(user_id):
    is_member_group, is_member_channel, is_member_community = False, False, False
    valid_statuses = [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ]

    try:
        member_group = await bot.get_chat_member(SUPPORT_CHAT_ID, user_id)
        is_member_group = member_group.status in valid_statuses
    except Exception:
        pass

    try:
        member_channel = await bot.get_chat_member(CHANNEL_ID, user_id)
        is_member_channel = member_channel.status in valid_statuses
    except Exception:
        pass

    try:
        member_community = await bot.get_chat_member(COMMUNITY_GROUP_ID, user_id)
        is_member_community = member_community.status in valid_statuses
    except Exception:
        pass

    return is_member_group, is_member_channel, is_member_community


async def get_unique_character(receiver_id, target_rarities=None):
    try:
        user_data = await user_collection.find_one({'id': receiver_id}, {'characters': 1})
        owned_character_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        target_rarities = target_rarities or ['⚪️ Common', '🔵 Medium', '🟠 Rare', '🟡 Legendary', '👶 Chibi', '💮 Exclusive']
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': owned_character_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)

        if not characters:
            random_character_pipeline = [{'$sample': {'size': 1}}]
            random_cursor = collection.aggregate(random_character_pipeline)
            characters = await random_cursor.to_list(length=1)

        return characters[0] if characters else None
    except Exception as e:
        print(f"Error fetching character: {e}")
        return None


@bot.on_message(filters.command(["wclaim"]))
async def claim_command(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Initial animation message
    anim_msg = await message.reply_text("🔄 Processing your claim...")

    # Check user's group/channel membership
    is_member_group, is_member_channel, is_member_community = await check_membership(user_id)
    if not is_member_group and not is_member_channel and not is_member_community:
        await anim_msg.delete()
        return await message.reply_text(
            "You must join the official groups, channels, and community group to use this command.",
            reply_markup=keyboard_all
        )
    elif not is_member_group:
        await anim_msg.delete()
        return await message.reply_text(
            "You must join the official group to use this command.",
            reply_markup=keyboard_support
        )
    elif not is_member_channel:
        await anim_msg.delete()
        return await message.reply_text(
            "You must join the official channel to use this command.",
            reply_markup=keyboard_channel
        )
    elif not is_member_community:
        await anim_msg.delete()
        return await message.reply_text(
            "You must join the community group to use this command.",
            reply_markup=keyboard_community
        )

    # Ensure user exists in the database
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await user_collection.insert_one({'id': user_id, 'characters': [], 'last_claim_time': None})

    # Check cooldown
    now = datetime.utcnow()
    last_claim_time = user_data.get('last_claim_time')
    if last_claim_time and last_claim_time.date() == now.date():
        cooldown_end = last_claim_time + timedelta(hours=24)
        await anim_msg.delete()
        return await message.reply_text(
            f"You've already claimed your character today! Cooldown ends at {cooldown_end.time()} UTC."
        )

    # Simulate claim process
    await anim_msg.edit_text("🔎 Searching for a unique character...")
    await asyncio.sleep(2)

    # Update last claim time
    await user_collection.update_one({'id': user_id}, {'$set': {'last_claim_time': now}})

    # Fetch a character
    character = await get_unique_character(user_id)

    # Ensure the character is added to the user's collection
    if character:
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        img_url = character['img_url']
        caption = (
            f"╭── ˹ ᴛᴏᴅᴀʏ'ꜱ ʀᴇᴡᴀʀᴅ ˼ ──•\n"
            f"┆\n"
            f"┊◍ 𝖮𝗐𝖮 {mention} won this character today! 💘\n"
            f"┆◍ ❄️ Name: {character['name']}\n"
            f"┊● ⚜️ Rarity: {character['rarity']}\n"
            f"┆● ⛩️ Anime: {character['anime']}\n"
            f"├──˹ ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ˼──•\n"
            f"╰───────────────•\n"
        )
        cooldown_end = now + timedelta(hours=24)

        await anim_msg.edit_text("✨ Found your reward! Preparing it...")
        await asyncio.sleep(2)

        async def notify_user():
            await asyncio.sleep(24 * 60 * 60)  # Wait for cooldown (24 hours)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Hey {mention}! Your cooldown has ended. You can now claim another character!"
                )
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")

        asyncio.create_task(notify_user())
        await anim_msg.delete()
        return await message.reply_photo(photo=img_url, caption=caption)
    else:
        await anim_msg.delete()
        return await message.reply_text("An unexpected error occurred. Please try again later.")
@bot.on_message(filters.command(["reset_claims"]) & filters.user(OWNER_ID))
async def reset_claims_command(_, message: t.Message):
    """
    Resets the claim cooldown for all users except developers.
    Only the owner can use this command.
    """
    try:
        # Fetch all users except DEVS and reset their claim cooldown
        result = await user_collection.update_many(
            {'id': {'$nin': DEVS}},  # Exclude DEVS from reset
            {'$set': {'last_claim_time': None}}
        )
        reset_count = result.modified_count
        await message.reply_text(f"✅ Successfully reset claim cooldown for {reset_count} users (excluding developers).")
    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred while resetting claims: {e}")
