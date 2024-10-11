import asyncio
from shivu import shivuu as bot
from pyrogram import filters, Client, types as t
from random import randint, choice
import time

DEVS = (6402009857,)
BANNED_USERS = [7162166061]

# Dictionary to store last open time for each user
cooldowns = {}
user_inventory = {}

# Mystery Box Types
BOX_TYPES = [
    {"type": "Common Box", "chance": 70, "rarity": "🟠 Rare", "items": [
        {"name": "Health Potion", "effect": "Restores 50% health", "rarity": "🟠 Rare"},
        {"name": "Gold Coins", "effect": "50 gold coins", "rarity": "🟠 Rare"}
    ]},
    {"type": "Rare Box", "chance": 25, "rarity": "🟡 Legendary", "items": [
        {"name": "Speed Boost", "effect": "Run 50% faster for 10 minutes", "rarity": "🟡 Legendary"},
        {"name": "Double XP", "effect": "Earn double XP for 1 hour", "rarity": "🟡 Legendary"}
    ]},
    {"type": "Legendary Box", "chance": 5, "rarity": "💮 Exclusive", "items": [
        {"name": "Mystery Key", "effect": "Opens another mystery box for free", "rarity": "💮 Exclusive"},
        {"name": "Golden Armor", "effect": "Reduces damage by 80% for 15 minutes", "rarity": "💮 Exclusive"}
    ]}
]

def get_box_type():
    """Determine the box type based on random chances."""
    roll = randint(1, 100)
    if roll <= 5:
        return BOX_TYPES[2]  # Legendary Box
    elif roll <= 30:
        return BOX_TYPES[1]  # Rare Box
    else:
        return BOX_TYPES[0]  # Common Box

async def get_random_item(box_type):
    """Get a random item from the selected box."""
    return choice(box_type['items'])

@bot.on_message(filters.command(["box", "openbox"]))
async def open_box(_, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention

    # Check if user is in cooldown
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:  # 60 seconds cooldown
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        await message.reply_text(
            f"🕑 Hold on {mention}, you can open another box in {cooldown_time} seconds ⏳.", 
            quote=True
        )
        return

    # Update the last open time for the user
    cooldowns[user_id] = time.time()

    # Check if user is banned
    if user_id in BANNED_USERS:
        return await message.reply_text(f"🚫 Sorry {mention}, you are banned from opening boxes.", quote=True)

    # Determine box type based on random chance
    box_type = get_box_type()

    # Open a mystery box and get a random item from the selected box type
    item = await get_random_item(box_type)

    # Add item to user's inventory
    if user_id not in user_inventory:
        user_inventory[user_id] = []
    user_inventory[user_id].append(item)

    # Box opening animation
    await message.reply_animation(
        animation="https://files.catbox.moe/jxgdk9.mp4",  # Box opening animation
        caption=(
            f"🎁 **{box_type['type']} Unlocked!** 🎁\n\n"
            f"📦 You found a hidden item, {mention}!\n\n"
            f"🧩 Name: `{item['name']}`\n"
            f"💥 Effect: `{item['effect']}`\n"
            f"💠 Rarity: `{item['rarity']}`\n\n"
            f"🚀 Keep opening boxes for more rewards!"
        ),
        quote=True
    )

@bot.on_message(filters.command(["inventory"]))
async def show_inventory(client: Client, message: t.Message):
    """Show the user's inventory."""
    user_id = message.from_user.id
    mention = message.from_user.mention

    # Check if user has any items in inventory
    if user_id not in user_inventory or len(user_inventory[user_id]) == 0:
        await message.reply_text(f"🎒 {mention}, your inventory is empty! Open some boxes to collect items.", quote=True)
        return

    # Build inventory message
    inventory_text = f"🎒 **{mention}'s Inventory** 🎒\n\n"
    for idx, item in enumerate(user_inventory[user_id], 1):
        inventory_text += f"{idx}. **{item['name']}** - {item['effect']} (Rarity: {item['rarity']})\n"
    
    await message.reply_text(inventory_text, quote=True)

@bot.on_message(filters.command(["bonus"]))
async def bonus_streak(client: Client, message: t.Message):
    """Daily bonus feature."""
    user_id = message.from_user.id
    mention = message.from_user.mention
    
    # Example bonus rewards
    bonus_rewards = [
        {"name": "Bonus Gold", "effect": "Earn 500 gold coins", "rarity": "🟡 Legendary"},
        {"name": "XP Boost", "effect": "Earn double XP for the next 12 hours", "rarity": "💮 Exclusive"}
    ]
    
    # Add bonus item to user's inventory
    bonus_item = choice(bonus_rewards)
    if user_id not in user_inventory:
        user_inventory[user_id] = []
    user_inventory[user_id].append(bonus_item)

    await message.reply_text(
        f"🎉 **Daily Bonus Collected!** 🎉\n\n"
        f"🧩 Name: `{bonus_item['name']}`\n"
        f"💥 Effect: `{bonus_item['effect']}`\n"
        f"💠 Rarity: `{bonus_item['rarity']}`\n\n"
        f"🚀 Don't forget to collect your bonus tomorrow!",
        quote=True
    )

# Start the bot
bot.run()
