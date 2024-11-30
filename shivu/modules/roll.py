import asyncio
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import collection, user_collection

# Cooldown dictionary to track user command usage
cooldowns = {}

# Bonus rewards based on dice value
BONUS_REWARDS = {
    6: "⭐ 100 Bonus Coins! ⭐",
    5: "💎 50 Bonus Coins! 💎",
    4: "🌟 20 Bonus Coins! 🌟",
}

async def fetch_unique_characters(receiver_id, target_rarities=['🟡 Legendary', '💮 Exclusive']):
    try:
        existing_character_ids = await user_collection.find_one(
            {'id': receiver_id}, {'characters.id': 1}
        ) or {'characters': []}
        
        pipeline = [
            {'$match': {
                'rarity': {'$in': target_rarities},
                'id': {'$nin': [char['id'] for char in existing_character_ids['characters']]}
            }},
            {'$sample': {'size': 1}}
        ]
        
        characters = await collection.aggregate(pipeline).to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error in fetch_unique_characters: {e}")
        return []

async def handle_dice_result(user_id, mention, value, message, unique_characters):
    # Bonus reward message
    bonus_message = BONUS_REWARDS.get(value, "")

    if value in [5, 6]:
        img_urls = [char['img_url'] for char in unique_characters]
        captions = [
            f"🎉 **Jackpot!**\n\n🍃 **Name:** {char['name']}\n⚜️ **Rarity:** {char['rarity']}\n⛩️ **Anime:** {char['anime']}\n\n**Congratulations {mention}! 🎊**\n{bonus_message}"
            for char in unique_characters
        ]
        
        for img, caption in zip(img_urls, captions):
            await message.reply_photo(photo=img, caption=caption)
            
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': {'$each': unique_characters}}})
        
    elif value in [3, 4]:
        await message.reply_animation(
            animation="https://files.catbox.moe/p62bql.mp4",  # Medium roll animation
            caption=f"❄️ **Nice roll, {mention}!** Rolled {value}. Keep going for the jackpot! 🩷\n{bonus_message}"
        )
        
    else:
        await message.reply_animation(
            animation="https://files.catbox.moe/hn08wr.mp4",  # Low roll animation
            caption=f"💔 **Oops, {mention}.** Rolled {value}. Better luck next time! 🎲"
        )

@bot.on_message(filters.command(["dice", "roll"]))
async def roll_command(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Cooldown management
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:
        await message.reply_text(f"⏳ Please wait {int(60 - (time.time() - cooldowns[user_id]))} seconds before rolling again.")
        return

    cooldowns[user_id] = time.time()

    # Fetch unique characters
    unique_characters = await fetch_unique_characters(user_id)
    
    # Dice roll with custom emoji and suspense
    suspense_msg = await message.reply_text("🎲 Rolling the dice... 🔄")
    await asyncio.sleep(2)
    dice_msg = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
    value = dice_msg.dice.value
    
    # Edit suspense message with result
    await suspense_msg.edit_text(f"🎲 **You rolled a {value}, {mention}!**")
    await handle_dice_result(user_id, mention, value, message, unique_characters)

    # Additional surprise chance
    if value == 6:
        await message.reply_text("🎉 **Surprise Bonus!** 🎉 You earned an extra roll!")
