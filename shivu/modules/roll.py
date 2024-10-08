import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection, user_totals_collection, shivuu, application
import time

DEVS = (6402009857)

async def get_unique_characters(receiver_id, target_rarities=['🟡 Legendary', '💮 Exclusive']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}  # Adjust Num
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in get_unique_characters: {e}")
        return []

# Dictionary to store last roll time for each user
cooldowns = {}

@bot.on_message(filters.command(["dice", "roll"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if the user is in cooldown
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:  # Adjust the cooldown time (in seconds)
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(
            f"🕑 Hold on {mention}, you can roll again in {cooldown_time} seconds ⏳.", 
            quote=True
        )
        return

    # Update the last roll time for the user
    cooldowns[user_id] = time.time()

    # Check for banned users
    if user_id == 7162166061:
        return await message.reply_text(f"🚫 Sorry {mention}, you are banned from using this command.", quote=True)

    # Special condition for specific user
    elif user_id == 6600178006:
        receiver_id = message.from_user.id
        unique_characters = await get_unique_characters(receiver_id)
        try:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})
            img_urls = [character['img_url'] for character in unique_characters]
            captions = [
                f"🏮 🎉 Yo {mention}, you hit the JACKPOT! 🎉 🏮\n\n"
                f"🧩 Name: `{character['name']}`\n"
                f"💠 Rarity: `{character['rarity']}`\n"
                f"🏖️ Anime: `{character['anime']}`\n\n"
                f"━─━────༺༻────━─━\n"
                for character in unique_characters
            ]
            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)
        except Exception as e:
            print(f"Error updating characters for special user: {e}")
    else:
        receiver_id = message.from_user.id
        unique_characters = await get_unique_characters(receiver_id)

        # Roll dice animation with special effects
        dice_msg = await bot.send_dice(chat_id=chat_id, emoji="🎲")
        value = int(dice_msg.dice.value)

        if value in [5, 6]:
            # High roll message for jackpot win
            for character in unique_characters:
                try:
                    await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(f"Error updating character: {e}")

            img_urls = [character['img_url'] for character in unique_characters]
            captions = [
                f"🎊✨ **JACKPOT!** ✨🎊\n"
                f"🎲 You rolled a {value}, {mention}!\n\n"
                f"🎯 **Legendary Character Unlocked!** 🎯\n"
                f"🧩 Name: `{character['name']}`\n"
                f"💠 Rarity: `{character['rarity']}`\n"
                f"🏖️ Anime: `{character['anime']}`\n\n"
                f"🚀 **Good luck on your next roll!** 🚀\n"
                f"━─━────༺༻────━─━\n"
                for character in unique_characters
            ]
            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

        elif value in [3, 4]:
            # Medium roll message
            await message.reply_animation(
                animation="https://files.catbox.moe/p62bql.mp4",  # Medium roll gif
                caption=(
                    f"🎯 **Nice roll, {mention}!** 🎯\n\n"
                    f"You rolled a {value}, not bad at all! 🍀 Keep trying for the jackpot!\n\n"
                    f"🌟 **Better luck next time!** 🌟"
                ),
                quote=True
            )

        else:
            # Low roll message
            await message.reply_animation(
                animation="https://files.catbox.moe/hn08wr.mp4",  # Low roll gif
                caption=(
                    f"💔 **Oops, {mention}.**\n\n"
                    f"You rolled a {value}... 😢\n\n"
                    f"Don't give up! Try again and aim for the stars! 🌠"
                ),
                quote=True
      )
