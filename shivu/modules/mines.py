import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

# Settings for the Mines game
GRID_SIZE = 5  # 5x5 grid
MINE_COUNT = 5  # Number of mines in the grid
cooldown_duration = 600  # Cooldown time in seconds
play_fee = 50000  # Fee for playing the mines game

user_cooldowns = {}  # Dictionary to track user cooldowns
ban_user_ids = {1234567890}  # List of banned users

# Helper function to generate a grid with mines
def generate_mines_grid(size, mine_count):
    grid = [['🟩' for _ in range(size)] for _ in range(size)]
    mine_positions = random.sample(range(size * size), mine_count)
    for pos in mine_positions:
        grid[pos // size][pos % size] = '💣'
    return grid

# Helper function to convert grid coordinates to a human-readable format
def format_grid(grid):
    grid_str = "   A B C D E\n"
    for i, row in enumerate(grid):
        grid_str += f"{i + 1}  " + " ".join(row) + "\n"
    return grid_str

# Mines command where the game begins
@bot.on_message(filters.command(["mines"]))
async def mines_game(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    chat_id = message.chat.id

    # Check if the user is banned
    if user_id in ban_user_ids:
        return await message.reply_text("Sorry, you are banned from this command.")

    # Cooldown check
    if user_id in user_cooldowns and time.time() - user_cooldowns[user_id] < cooldown_duration:
        remaining_time = cooldown_duration - int(time.time() - user_cooldowns[user_id])
        return await message.reply_text(f"Please wait! You can play again in {remaining_time} seconds.")

    # Deduct play fee
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    user_balance = user_data.get('balance', 0)

    if user_balance < play_fee:
        return await message.reply_text(f"You need at least {play_fee} tokens to play.")

    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -play_fee}})

    # Generate a random mines grid
    grid = generate_mines_grid(GRID_SIZE, MINE_COUNT)
    revealed_grid = [['🟦' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # All spots are hidden at first
    safe_spots_to_reveal = (GRID_SIZE * GRID_SIZE) - MINE_COUNT

    # Set cooldown for the user
    user_cooldowns[user_id] = time.time()

    # Send the initial grid to the user
    await message.reply_text(f"🔍 Welcome to the Mines game, {mention}!\n\nHere is your grid:\n\n{format_grid(revealed_grid)}\nType `/reveal A1` to reveal a spot.")

    # Store the game state
    bot.user_data[user_id] = {
        'grid': grid,
        'revealed_grid': revealed_grid,
        'safe_spots_to_reveal': safe_spots_to_reveal
    }

# Command to reveal a grid spot
@bot.on_message(filters.command(["reveal"]))
async def reveal_spot(_, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention

    # Check if the user is currently playing
    if user_id not in bot.user_data:
        return await message.reply_text("You are not currently in a game. Start one by typing /mines.")

    game_data = bot.user_data[user_id]
    grid = game_data['grid']
    revealed_grid = game_data['revealed_grid']
    safe_spots_to_reveal = game_data['safe_spots_to_reveal']

    # Parse the user's move (e.g., /reveal A1)
    if len(message.command) < 2:
        return await message.reply_text("Please specify a spot to reveal (e.g., /reveal A1).")

    spot = message.command[1].upper()
    if len(spot) < 2 or spot[0] not in "ABCDE" or not spot[1].isdigit() or int(spot[1]) < 1 or int(spot[1]) > GRID_SIZE:
        return await message.reply_text("Invalid spot. Use format like A1, B3, etc.")

    col = ord(spot[0]) - ord('A')  # Convert 'A' to 0, 'B' to 1, etc.
    row = int(spot[1]) - 1

    # Check if the spot is already revealed
    if revealed_grid[row][col] != '🟦':
        return await message.reply_text(f"{mention}, that spot is already revealed. Choose another.")

    # Reveal the spot
    if grid[row][col] == '💣':
        # User hit a mine! Game over
        revealed_grid[row][col] = '💣'
        await message.reply_text(f"{mention}, you hit a mine! 💥 Game over.\n\nHere was your final grid:\n\n{format_grid(grid)}")
        del bot.user_data[user_id]  # Clear game state
    else:
        # Safe spot revealed
        revealed_grid[row][col] = '🟩'
        safe_spots_to_reveal -= 1
        await message.reply_text(f"Good job, {mention}! No mine here. Keep going!\n\n{format_grid(revealed_grid)}")

        # Update the game state
        bot.user_data[user_id]['revealed_grid'] = revealed_grid
        bot.user_data[user_id]['safe_spots_to_reveal'] = safe_spots_to_reveal

        # Check if the user has won
        if safe_spots_to_reveal == 0:
            await message.reply_text(f"🎉 Congratulations, {mention}! You revealed all safe spots and won the game!\n\n{format_grid(revealed_grid)}")
            del bot.user_data[user_id]  # Clear game state

# Start the bot
bot.run()
