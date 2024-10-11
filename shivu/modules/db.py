import random
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, backup_collection  # Assuming waifu_collection is where waifu data is stored

# Settings for the Guess Waifu game
ban_user_ids = {1234567890}  # List of banned user IDs

# Initialize bot.user_data if not already initialized
if not hasattr(bot, "user_data"):
    bot.user_data = {}

# Helper function to get a random waifu from the database
async def get_random_waifu():
    waifus = await backup_collection.aggregate([{"$sample": {"size": 1}}]).to_list(length=1)
    return waifus[0] if waifus else None

# Command to start the guessing game
@bot.on_message(filters.command(["guesswaifu"]))
async def guess_waifu_game(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if the user is banned
    if user_id in ban_user_ids:
        return await message.reply_text("Sorry, you are banned from this command.")

    # Select a random waifu from the database
    waifu = await get_random_waifu()
    if not waifu:
        return await message.reply_text("No waifu data found. Please try again later.")

    # Check if 'image_url' exists in waifu data
    if 'image_url' not in waifu:
        return await message.reply_text("The selected waifu does not have an image. Please try again.")

    # Send the waifu image and prompt the user to guess
    await message.reply_photo(waifu["image_url"], caption=f"🧠 Guess the Waifu, {mention}!\n\nType `/guess <name>` to submit your guess.")

    # Store the game state
    bot.user_data[user_id] = {
        'waifu': waifu
    }

# Command to submit a guess
@bot.on_message(filters.command(["guess"]))
async def submit_guess(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if the user is currently playing
    if user_id not in bot.user_data:
        return await message.reply_text("You are not currently in a game. Start one by typing /guesswaifu.")

    game_data = bot.user_data.get(user_id)
    waifu = game_data.get('waifu')

    # Parse the user's guess
    if len(message.command) < 2:
        return await message.reply_text("Please specify your guess (e.g., /guess Rem).")

    user_guess = " ".join(message.command[1:]).strip()

    # Check the user's guess
    if user_guess.lower() == waifu['name'].lower():
        await message.reply_text(f"🎉 Congratulations, {mention}! You guessed it right. The waifu is {waifu['name']}!")
        del bot.user_data[user_id]  # Clear game state
    else:
        await message.reply_text(f"❌ Wrong guess! Try again.")
