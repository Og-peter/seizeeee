import asyncio
import random
import time
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot

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

# Cooldown checker
def is_on_cooldown(user_id):
    current_time = time.time()
    return cooldowns.get(user_id, 0) > current_time

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
    if is_on_cooldown(challenger.id):
        remaining_time = int(cooldowns[challenger.id] - time.time())
        return await message.reply_text(f"⏳ **Wait {remaining_time}s before challenging again!**")

    # Notify opponent
    notification = await message.reply_text(
        f"⚔️ **{challenger.first_name} has challenged you to an anime battle!**\n\n"
        "🏟 **Arena:** A random battlefield awaits!\n"
        "💥 **Do you accept the challenge?**",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{challenger.id}_{opponent.id}"),
                InlineKeyboardButton("❌ Decline", callback_data="decline")
            ]
        ])
    )

# Handle accept/decline callbacks
@bot.on_callback_query(filters.regex(r"accept_(\d+)_(\d+)"))
async def accept_battle(_, callback_query: t.CallbackQuery):
    challenger_id, opponent_id = map(int, callback_query.data.split("_")[1:])
    if callback_query.from_user.id != opponent_id:
        return await callback_query.answer("You can't accept this challenge!", show_alert=True)

    challenger = await bot.get_users(challenger_id)
    opponent = await bot.get_users(opponent_id)

    # Start battle
    arena = random.choice(ARENAS)
    battle_message = await callback_query.message.edit_text(
        f"🏟 **Battle begins in:** {arena}\n\n"
        f"❤️ {challenger.first_name}: {MAX_HEALTH}/{MAX_HEALTH}\n"
        f"❤️ {opponent.first_name}: {MAX_HEALTH}/{MAX_HEALTH}"
    )

    challenger_health = MAX_HEALTH
    opponent_health = MAX_HEALTH

    while challenger_health > 0 and opponent_health > 0:
        # Challenger's move
        challenger_move = random.choice(list(CHARACTERS.items()))
        damage = random.choice([challenger_move[1]["damage"], challenger_move[1]["critical"]])
        opponent_health -= damage
        opponent_health = max(opponent_health, 0)  # Prevent negative health

        # Update health bar
        await asyncio.sleep(1)
        await battle_message.edit_text(
            f"🏟 **Battle in:** {arena}\n\n"
            f"🔥 **{challenger.first_name} uses {challenger_move[1]['move']}**\n"
            f"💥 **Damage:** {damage}\n"
            f"❤️ {challenger.first_name}: {challenger_health}/{MAX_HEALTH}\n"
            f"❤️ {opponent.first_name}: {opponent_health}/{MAX_HEALTH}"
        )

        if opponent_health <= 0:
            break

        # Opponent's move
        await asyncio.sleep(2)
        opponent_move = random.choice(list(CHARACTERS.items()))
        damage = random.choice([opponent_move[1]["damage"], opponent_move[1]["critical"]])
        challenger_health -= damage
        challenger_health = max(challenger_health, 0)  # Prevent negative health

        # Update health bar
        await battle_message.edit_text(
            f"🏟 **Battle in:** {arena}\n\n"
            f"⚡ **{opponent.first_name} counters with {opponent_move[1]['move']}**\n"
            f"💥 **Damage:** {damage}\n"
            f"❤️ {challenger.first_name}: {challenger_health}/{MAX_HEALTH}\n"
            f"❤️ {opponent.first_name}: {opponent_health}/{MAX_HEALTH}"
        )

    # Determine winner
    winner = challenger if challenger_health > opponent_health else opponent
    loser = opponent if winner == challenger else challenger
    await battle_message.edit_text(
        f"🏆 **{winner.first_name} wins the battle in {arena}!**\n"
        f"💀 **{loser.first_name} is defeated! Better luck next time.**"
    )

    # Set cooldown
    cooldowns[challenger.id] = time.time() + COOLDOWN_DURATION

@bot.on_callback_query(filters.regex("decline"))
async def decline_battle(_, callback_query: t.CallbackQuery):
    await callback_query.message.edit_text("⚔️ **The battle challenge was declined!**")
