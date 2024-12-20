import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import collection, user_collection

# Cooldown and temporary storage
user_sessions = {}  # Tracks active user sessions
cooldowns = {}

async def fetch_character(query=None):
    """Fetch a character randomly or by specific query (ID)."""
    try:
        if query:
            character = await collection.find_one({'id': query})
        else:
            pipeline = [{'$sample': {'size': 1}}]
            cursor = collection.aggregate(pipeline)
            character = await cursor.to_list(length=1)
            character = character[0] if character else None
        return character
    except Exception as e:
        print(e)
        return None

async def calculate_stats():
    """Generate random stats for a fight."""
    return {
        'strength': random.randint(50, 100),
        'agility': random.randint(40, 90),
        'defense': random.randint(30, 80),
        'luck': random.randint(1, 20),
    }

@bot.on_message(filters.command(["find"]))
async def find_character(_, message: t.Message):
    """Discover a random character."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Cooldown check
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 30:
        cooldown_time = int(30 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(f"⏳ Wait {cooldown_time} seconds before searching again.", quote=True)

    # Update cooldown
    cooldowns[user_id] = time.time()

    # Fetch a random character
    character = await fetch_character()
    if not character:
        return await message.reply_text("No character found. Please try again later.", quote=True)

    # Generate random stats for the character
    character['stats'] = await calculate_stats()

    # Save session
    user_sessions[user_id] = character

    # Display character with options
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚔️ Fight", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{user_id}")]
        ]
    )
    await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🔍 {mention}, you found a random character!\n\n"
            f"⛱️ Name: {character['name']}\n"
            f"🏮 Rarity: {character['rarity']}\n"
            f"⛩️ Anime: {character['anime']}\n\n"
            f"✨ **Stats**:\n"
            f"🔹 Strength: {character['stats']['strength']}\n"
            f"🔹 Agility: {character['stats']['agility']}\n"
            f"🔹 Defense: {character['stats']['defense']}\n"
            f"🔹 Luck: {character['stats']['luck']}\n\n"
            f"⚔️ Choose to fight or ignore!"
        ),
        reply_markup=keyboard,
    )

@bot.on_message(filters.command(["hfind"]))
async def hfind_character(_, message: t.Message):
    """Search and fight a specific character by ID."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    if len(message.command) < 2:
        return await message.reply_text("Please specify the character ID, e.g., `/hfind 1234`.", quote=True)

    character_id = message.command[1]

    # Fetch the character by ID
    character = await fetch_character(query=character_id)
    if not character:
        return await message.reply_text(f"No character found with ID `{character_id}`. Please try another.", quote=True)

    # Generate random stats for the character
    character['stats'] = await calculate_stats()

    # Save session
    user_sessions[user_id] = character

    # Display character with options
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚔️ Fight", callback_data=f"fight_{user_id}")],
            [InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{user_id}")]
        ]
    )
    await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🔍 {mention}, you found **{character['name']}** by ID!\n\n"
            f"⛱️ Name: {character['name']}\n"
            f"🏮 Rarity: {character['rarity']}\n"
            f"⛩️ Anime: {character['anime']}\n\n"
            f"✨ **Stats**:\n"
            f"🔹 Strength: {character['stats']['strength']}\n"
            f"🔹 Agility: {character['stats']['agility']}\n"
            f"🔹 Defense: {character['stats']['defense']}\n"
            f"🔹 Luck: {character['stats']['luck']}\n\n"
            f"⚔️ Ready to fight or ignore?"
        ),
        reply_markup=keyboard,
    )

@bot.on_callback_query(filters.regex(r"^(fight|ignore)_(\d+)$"))
async def fight_or_ignore_callback(_, callback_query: t.CallbackQuery):
    """Handle fight or ignore options."""
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)
    mention = callback_query.from_user.mention

    # Ensure the callback is for the correct user
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This is not your interaction!", show_alert=True)

    # Fetch character data from session
    character = user_sessions.get(user_id)
    if not character:
        return await callback_query.answer("Character data not found. Please use /find or /hfind again.", show_alert=True)

    if action == "ignore":
        await callback_query.message.edit_text(f"❌ {mention}, you ignored {character['name']}.\nTry searching again with `/find` or `/hfind`!")
        user_sessions.pop(user_id, None)
    elif action == "fight":
        await callback_query.answer("⚔️ Fight initiated!", show_alert=True)
        await initiate_bed_fight(callback_query, user_id, character)

async def initiate_bed_fight(callback_query, user_id, character):
    """Simulate a fight."""
    mention = callback_query.from_user.mention

    # User stats
    user_stats = await calculate_stats()
    user_score = sum(user_stats.values())

    # Character stats
    char_stats = character['stats']
    char_score = sum(char_stats.values())

    # Simulate fight
    fight_text = (
        f"🛏️ **Bed Fight Begins!**\n\n"
        f"🔹 Your Stats:\n"
        f"Strength: {user_stats['strength']}, Agility: {user_stats['agility']}, Defense: {user_stats['defense']}, Luck: {user_stats['luck']}\n\n"
        f"🔸 {character['name']}'s Stats:\n"
        f"Strength: {char_stats['strength']}, Agility: {char_stats['agility']}, Defense: {char_stats['defense']}, Luck: {char_stats['luck']}\n\n"
        f"⚔️ Calculating the winner...\n"
    )
    await callback_query.message.edit_text(fight_text)

    await asyncio.sleep(2)  # Add suspense

    if user_score > char_score:
        result_text = f"🎉 {mention}, you won the bed fight against {character['name']}!\nThe character is now yours!"
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        result_text = f"💔 {mention}, you lost the fight against {character['name']}.\nBetter luck next time!"

    await callback_query.message.edit_text(result_text)

    # Clear session
    user_sessions.pop(user_id, None)
