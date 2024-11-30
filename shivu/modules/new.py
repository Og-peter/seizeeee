from pyrogram import Client, filters
from telegram.ext import CommandHandler, CallbackContext
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from shivu import application
import random
import time
from collections import defaultdict

# **Database placeholders**
user_data = defaultdict(lambda: {
    "tokens": 1000,
    "energy": 100,
    "inventory": [],
    "guild": None,
    "kills": 0,
    "bgmi_score": 0,
    "last_energy_refill": 0,
})
mystery_box_rewards = [
    {"item": "Rare Waifu", "chance": 10},
    {"item": "Epic Waifu", "chance": 5},
    {"item": "Tokens x1000", "chance": 30},
    {"item": "Tokens x500", "chance": 55}
]
zones = [
    {"name": "Enchanted Forest", "rarity_bonus": 5},
    {"name": "Desert of Secrets", "rarity_bonus": 10},
    {"name": "Frozen Wastelands", "rarity_bonus": 15}
]
guilds = {}
cooldowns = defaultdict(lambda: {"last_zone_catch": 0, "last_bgmi_play": 0})

# **Command: Mystery Box**
async def mystery_box(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    cost = 500
    user_info = user_data[user_id]

    if user_info["tokens"] < cost:
        await update.message.reply_text("❌ You don’t have enough tokens to open a mystery box.")
        return

    # Deduct cost and determine reward
    user_info["tokens"] -= cost
    reward_pool = [r["item"] for r in mystery_box_rewards for _ in range(r["chance"])]
    reward = random.choice(reward_pool)

    if reward in ["Rare Waifu", "Epic Waifu"]:
        user_info["inventory"].append(reward)

    await update.message.reply_text(
        f"🎁 **Mystery Box Opened!**\nYou’ve received: {reward}\nYour remaining tokens: {user_info['tokens']}."
    )

# **Command: Energy System**
async def energy(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_info = user_data[user_id]
    current_time = time.time()

    # Recharge energy every 10 minutes
    recharge_rate = 10
    recharge_interval = 600  # 10 minutes
    elapsed_time = current_time - user_info["last_energy_refill"]
    energy_recharged = int(elapsed_time // recharge_interval) * recharge_rate

    if energy_recharged > 0:
        user_info["energy"] = min(100, user_info["energy"] + energy_recharged)
        user_info["last_energy_refill"] = current_time

    await update.message.reply_text(
        f"⚡ **Energy Status:**\nCurrent Energy: {user_info['energy']}/100"
    )

# **Command: Zones**
async def explore_zone(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args
    user_info = user_data[user_id]

    if not args:
        zones_list = "\n".join([f"- {zone['name']}" for zone in zones])
        await update.message.reply_text(
            f"🌍 **Available Zones:**\n{zones_list}\n\nUse `/zone <zone_name>` to explore."
        )
        return

    zone_name = " ".join(args).strip()
    zone = next((z for z in zones if z["name"].lower() == zone_name.lower()), None)

    if not zone:
        await update.message.reply_text("❌ Invalid zone name. Please choose a valid zone.")
        return

    # Check energy
    if user_info["energy"] < 20:
        await update.message.reply_text("❌ Not enough energy to explore this zone. Use `/energy` to check your energy.")
        return

    # Deduct energy and simulate waifu catch
    user_info["energy"] -= 20
    rarity_bonus = zone["rarity_bonus"]
    is_catch_successful = random.randint(1, 100) <= 20 + rarity_bonus

    if is_catch_successful:
        rarity = random.choices(["Common", "Rare", "Epic"], [70, 25, 5])[0]
        waifu_name = f"{rarity} Waifu {random.randint(1000, 9999)}"
        user_info["inventory"].append(waifu_name)
        await update.message.reply_text(
            f"🎉 **Waifu Caught!**\nYou’ve caught a {rarity} Waifu: {waifu_name}!"
        )
    else:
        await update.message.reply_text("❌ No waifu found. Better luck next time!")

# **Command: Guild System**
async def create_guild(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /createguild <name>")
        return

    guild_name = " ".join(args)
    if user_id in guilds:
        await update.message.reply_text("❌ You already lead a guild. Disband it first to create a new one.")
        return

    guilds[user_id] = {"name": guild_name, "members": [user_id]}
    user_data[user_id]["guild"] = guild_name
    await update.message.reply_text(f"🎉 Guild '{guild_name}' created successfully!")

async def join_guild(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /joinguild <guild_name>")
        return

    guild_name = " ".join(args)
    for guild_leader, guild_data in guilds.items():
        if guild_data["name"] == guild_name:
            guild_data["members"].append(user_id)
            user_data[user_id]["guild"] = guild_name
            await update.message.reply_text(f"🎉 You’ve joined the guild '{guild_name}'!")
            return

    await update.message.reply_text("❌ Guild not found!")

# **Command: BGMI Game Simulation**
async def bgmi_game(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_info = user_data[user_id]
    current_time = time.time()

    # Cooldown of 10 minutes for BGMI matches
    if current_time - cooldowns[user_id]["last_bgmi_play"] < 600:
        await update.message.reply_text("❌ You can only play BGMI matches every 10 minutes.")
        return

    cooldowns[user_id]["last_bgmi_play"] = current_time

    # Simulate a match
    kills = random.randint(0, 10)
    score = kills * 10 + random.randint(0, 50)
    user_info["kills"] += kills
    user_info["bgmi_score"] += score

    await update.message.reply_text(
        f"🎮 **BGMI Match Results:**\nKills: {kills}\nScore Earned: {score}\n"
        f"Total Kills: {user_info['kills']}\nTotal Score: {user_info['bgmi_score']}"
    )

# **Command: Waifu Evolution**
async def evolve(update: Update, context: CallbackContext):
    args = context.args
    user_id = update.message.from_user.id
    user_info = user_data[user_id]

    if not args or not user_info["inventory"]:
        await update.message.reply_text("Usage: /evolve <waifu_name>")
        return

    waifu_name = " ".join(args)
    if waifu_name not in user_info["inventory"]:
        await update.message.reply_text(f"❌ You don’t own a waifu named {waifu_name}.")
        return

    rarity_upgrade = {"Common": "Rare", "Rare": "Epic", "Epic": "Legendary"}
    for rarity in rarity_upgrade:
        if rarity in waifu_name:
            new_rarity = rarity_upgrade[rarity]
            user_info["inventory"].remove(waifu_name)
            evolved_waifu = waifu_name.replace(rarity, new_rarity)
            user_info["inventory"].append(evolved_waifu)
            await update.message.reply_text(
                f"✨ Your waifu has evolved into a {new_rarity} version: {evolved_waifu}!"
            )
            return

    await update.message.reply_text("❌ This waifu cannot be evolved further.")

# Add Handlers
application.add_handler(CommandHandler("mysterybox", mystery_box))
application.add_handler(CommandHandler("energy", energy))
application.add_handler(CommandHandler("zone", explore_zone))
application.add_handler(CommandHandler("createguild", create_guild))
application.add_handler(CommandHandler("joinguild", join_guild))
application.add_handler(CommandHandler("bgmi", bgmi_game))
application.add_handler(CommandHandler("evolve", evolve))
