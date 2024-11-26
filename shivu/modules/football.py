import random
import time
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, user_collection

# Cooldown tracking and duration (in seconds)
usage_tracker = {}
FOOTBALL_TIMEOUT = 10

# Blue Lock-inspired teams and outcome videos
TEAMS = ["Team Z", "Team V", "Team X", "Team Y", "Team W"]
OUTCOME_VIDEOS = {
    "win": "https://files.catbox.moe/9fk6tq.gif",
    "lose": "https://files.catbox.moe/h8zv61.gif",
    "draw": "https://files.catbox.moe/7jxi98.gif"
}

async def is_registered(user_id, message):
    """Check if the user is registered to use the bot."""
    if not await user_collection.find_one({'id': user_id}):
        await message.reply_text(
            "🛑 <b>Access Denied!</b>\nYou must register by starting the bot.\nUse the /start command to begin!",
            parse_mode='HTML'
        )
        return False
    return True

async def enforce_cooldown(user_id, cooldown_period, message):
    """Enforce cooldown period to prevent spammy requests."""
    last_used = usage_tracker.get(user_id)
    if last_used and (time.time() - last_used) < cooldown_period:
        wait_time = int(cooldown_period - (time.time() - last_used))
        await message.reply_text(
            f"⏱️ <b>Hold on, striker!</b>\nYou can play again in {wait_time} seconds.",
            parse_mode='HTML'
        )
        return False
    return True

async def blue_lock_football_game(update: Update, context: CallbackContext):
    """Main function to simulate the Blue Lock football game."""
    message = update.effective_message
    user_id = message.from_user.id

    try:
        # Check if user is registered and cooldown is not active
        if not await is_registered(user_id, message) or not await enforce_cooldown(user_id, FOOTBALL_TIMEOUT, message):
            return

        # Show football emoji and introduce a short delay
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚽")
        await asyncio.sleep(1)

        # Randomly select teams and game outcome
        user_team = random.choice(TEAMS)
        opponent_team = random.choice([team for team in TEAMS if team != user_team])
        outcome = random.choice(["win", "lose", "draw"])

        # Set outcome-specific messages and experience changes
        if outcome == "win":
            outcome_text = (
                f"<b>GOOOAL!</b> {user_team} scored an amazing goal against {opponent_team}!\n"
                "<b>Victory is yours!</b> Keep up the winning spirit!"
            )
            xp_change = 5
        elif outcome == "lose":
            outcome_text = (
                f"<b>Missed!</b> {user_team} couldn’t break through {opponent_team}'s defense.\n"
                "<b>Fight harder next time!</b>"
            )
            xp_change = -3
        else:
            outcome_text = (
                f"<b>Draw!</b> Both {user_team} and {opponent_team} were evenly matched!\n"
                "<b>The challenge awaits again!</b>"
            )
            xp_change = 2

        # Send the outcome message along with a relevant video
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{outcome_text}\n\n[⚡]({OUTCOME_VIDEOS[outcome]})",
            parse_mode='HTML'
        )

        # Update experience points for the user
        await adjust_experience(user_id, xp_change)

        # Update usage tracker to enforce cooldown
        usage_tracker[user_id] = time.time()

    except Exception as e:
        print(f"Error in blue_lock_football_game: {e}")

async def adjust_experience(user_id, xp_points):
    """Adjust user's experience based on the game outcome."""
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_points}}, upsert=True)

# Register the command handler for the football game
application.add_handler(CommandHandler('football', blue_lock_football_game, block=False))
