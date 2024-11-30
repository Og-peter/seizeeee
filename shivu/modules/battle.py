import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection

# Constants
COOLDOWN_DURATION = 300  # Cooldown in seconds
MAX_HEALTH = 100  # Max health for players
ARENAS = [
    "🌋 Volcano Crater",
    "🏰 Mystic Castle",
    "🌌 Galactic Void",
    "🌊 Ocean Battlefield",
    "⚡ Thunder Plains",
]

# Cooldown tracker
cooldowns = {}

# Anime characters with moves and effects
CHARACTERS = {
    "Saitama": {
        "move": "💥 **Serious Punch** explodes the battlefield!",
        "damage": 30,
        "critical": 50,
        "video_url": "https://files.catbox.moe/rw2yuz.mp4"
    },
    "Goku": {
        "move": "🌌 **Ultra Instinct Kamehameha** obliterates the enemy!",
        "damage": 35,
        "critical": 60,
        "video_url": "https://files.catbox.moe/90bga6.mp4"
    },
    "Naruto": {
        "move": "🌀 **Baryon Mode** overwhelms the opponent!",
        "damage": 40,
        "critical": 70,
        "video_url": "https://files.catbox.moe/d2iygy.mp4"
    },
    "Luffy": {
        "move": "🌊 **Gear 5 Toony Chaos** wrecks the battlefield!",
        "damage": 25,
        "critical": 55,
        "video_url": "https://files.catbox.moe/wmc671.gif"
    },
    "Ichigo": {
        "move": "⚡ **Final Getsuga Tenshou** slashes through everything!",
        "damage": 30,
        "critical": 45,
        "video_url": "https://files.catbox.moe/ky17sr.mp4"
    },
    "Madara": {
        "move": "🌪️ **Perfect Susanoo** crushes the battlefield!",
        "damage": 35,
        "critical": 65,
        "video_url": "https://files.catbox.moe/lknesv.mp4"
    },
    "Aizen": {
        "move": "💀 **Kyoka Suigetsu** confuses the opponent!",
        "damage": 25,
        "critical": 50,
        "video_url": "https://files.catbox.moe/jv25db.mp4"
    },
}

# Battle command
@bot.on_message(filters.command("battle"))
async def battle_command(_, message: t.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ **Reply to someone to challenge them to an anime battle!**")
    
    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    if opponent.is_bot:
        return await message.reply_text("🤖 **You can't battle a bot! Challenge a human!**")
    if challenger.id == opponent.id:
        return await message.reply_text("⚠️ **You can't battle yourself!**")

    # Cooldown check
    current_time = time.time()
    if cooldowns.get(challenger.id, 0) > current_time:
        remaining_time = int(cooldowns[challenger.id] - current_time)
        return await message.reply_text(f"⏳ **Wait {remaining_time}s before battling again!**")

    # Select random arena
    arena = random.choice(ARENAS)
    await message.reply_text(f"⚔️ **The battle will take place in:** {arena}")

    # Initialize health points
    challenger_health = MAX_HEALTH
    opponent_health = MAX_HEALTH

    # Battle starts
    await asyncio.sleep(2)
    while challenger_health > 0 and opponent_health > 0:
        # Challenger's move
        challenger_move = random.choice(list(CHARACTERS.items()))
        damage = random.choice([challenger_move[1]["damage"], challenger_move[1]["critical"]])
        opponent_health -= damage
        opponent_health = max(opponent_health, 0)  # Prevent negative health
        await message.reply_video(
            video=challenger_move[1]["video_url"],
            caption=(
                f"🔥 **{challenger.first_name} attacks with:** {challenger_move[1]['move']}\n"
                f"💥 **Damage:** {damage} HP\n"
                f"❤️ **{opponent.first_name}'s Health:** {opponent_health}/{MAX_HEALTH}"
            )
        )
        if opponent_health <= 0:
            break

        # Opponent's move
        await asyncio.sleep(2)
        opponent_move = random.choice(list(CHARACTERS.items()))
        damage = random.choice([opponent_move[1]["damage"], opponent_move[1]["critical"]])
        challenger_health -= damage
        challenger_health = max(challenger_health, 0)  # Prevent negative health
        await message.reply_video(
            video=opponent_move[1]["video_url"],
            caption=(
                f"⚡ **{opponent.first_name} counters with:** {opponent_move[1]['move']}\n"
                f"💥 **Damage:** {damage} HP\n"
                f"❤️ **{challenger.first_name}'s Health:** {challenger_health}/{MAX_HEALTH}"
            )
        )

    # Determine winner
    if challenger_health > opponent_health:
        winner = challenger
        loser = opponent
    else:
        winner = opponent
        loser = challenger

    # Announce winner
    await asyncio.sleep(2)
    await message.reply_text(
        f"🏆 **{winner.first_name} wins the epic battle in {arena}!**\n"
        f"💀 **{loser.first_name} is defeated! Better luck next time.**"
    )

    # Set cooldown for challenger
    cooldowns[challenger.id] = current_time + COOLDOWN_DURATION
