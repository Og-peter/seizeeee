import time
import asyncio
import random
import os  # Import os for environment variables
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import shivuu as app
from shivu import user_collection
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

MUST_JOIN = "dynamic_gangs"

gem_prices = {
    "Wood": {"price": 2, "emoji": "🪵", "aliases": ["wood", "w"]},
    "Iron": {"price": 5, "emoji": "🔩", "aliases": ["iron", "i"]},
    "Silver": {"price": 7, "emoji": "🥈", "aliases": ["silver", "s"]},
    "Gold": {"price": 10, "emoji": "🥇", "aliases": ["gold", "g"]},
    "Diamond": {"price": 20, "emoji": "💎", "aliases": ["diamond", "d", "gem"]},
    "Platinum": {"price": 25, "emoji": "🏆", "aliases": ["platinum", "p"]},  # New
    "Emerald": {"price": 30, "emoji": "🟢", "aliases": ["emerald", "e"]},    # New
    "Ruby": {"price": 35, "emoji": "🔴", "aliases": ["ruby", "r"]},      # New
    "Sapphire": {"price": 40, "emoji": "🔵", "aliases": ["sapphire", "s"]}, # New
    "Amethyst": {"price": 45, "emoji": "🟣", "aliases": ["amethyst", "a"]}, # New
    "Obsidian": {"price": 50, "emoji": "⚫", "aliases": ["obsidian", "o"]}  # New
}

@bot.on_message(filters.command(["sbag"]))
async def gems_command(_, message: Message):
    user_id = message.from_user.id

    # Get user's gem inventory from the database
    user_data = await user_collection.find_one({'id': user_id}, projection={'gems': 1})

    if user_data and 'gems' in user_data and user_data['gems']:
        gem_inventory = user_data['gems']
        inventory_text = "<b>💎 𝗬𝗢𝗨𝗥 𝗜𝗧𝗘𝗠 𝗟𝗜𝗦𝗧 💎</b>\n\n"
        
        # Iterate through the gem inventory
        for gem, quantity in gem_inventory.items():
            # Check if gem price is available to avoid KeyError
            gem_emoji = gem_prices.get(gem, {}).get('emoji', '❓')  # Default to a question mark if not found
            inventory_text += f"{gem_emoji} <b>{gem}</b>: <b>{quantity}</b>\n"
        
        # Add a footer for clarity and encouragement
        inventory_text += "\n<b>✨ Keep collecting more gems and unlock amazing rewards!</b>"

        # Use reply method without parse_mode
        await message.reply(inventory_text)
    else:
        await message.reply("<b>🚫 You haven't collected any items yet! Start gathering some gems to fill your inventory.</b>")
        
# Command to sell gems
@bot.on_message(filters.command(["sellitem"]))
async def sell_command(_, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) != 3:
        return await message.reply_html("<b>❌ Invalid command. Usage: /sellitem <item name> <quantity></b>")

    item_name = command_parts[1]
    try:
        quantity = int(command_parts[2])
    except ValueError:
        return await message.reply_html("<b>⚠️ Please enter a valid quantity.</b>")

    # Check if the item exists and the user has it in their inventory
    found_item = None
    for gem, item_info in gem_prices.items():
        if item_name.lower() in [gem.lower()] + item_info.get("aliases", []):
            found_item = gem
            break

    if not found_item:
        return await message.reply_html("<b>🚫 Invalid item name. Please check your input.</b>")

    user_data = await user_collection.find_one({'id': user_id}, projection={'gems': 1})

    if user_data and user_data.get('gems') and found_item in user_data['gems']:
        # Check if the user has enough quantity of the item to sell
        if user_data['gems'][found_item] < quantity:
            return await message.reply_html("<b>⚠️ You don't have enough quantity of this item to sell.</b>")

        # Calculate the total price for the items
        total_price = gem_prices[found_item]["price"] * quantity
        
        # Remove the sold items from the user's inventory
        await user_collection.update_one({'id': user_id}, {'$inc': {f'gems.{found_item}': -quantity}})
        
        # Add the sold tokens to the user's balance
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': total_price}})
        
        await message.reply_html(
            f"<b>✅ You have successfully sold {quantity} {gem_prices[found_item]['emoji']} {found_item} for a total of <u>{total_price} tokens</u>.</b>"
        )
    else:
        await message.reply_html("<b>🚫 You don't have this item to sell. Please check your inventory.</b>")

        
# Dictionary of gem sets with their images, captions, win chances, and text messages
gem_sets = {
    "1": {
        "image_url": "https://files.catbox.moe/cwpmbf.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐅` ] 𝐑𝐚𝐧𝐤 𝐆𝐨𝐛𝐥𝐢𝐧 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 80,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Goblin... *fouled your Beast* 💀."
    },
    "2": {
        "image_url": "https://te.legra.ph/file/400b73f9a6e48a227c7e5.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐄` ] 𝐑𝐚𝐧𝐤 𝐆𝐨𝐛𝐥𝐢𝐧 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 75,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Goblin... *fouled your Beast* 💀."
    },
    "3": {
        "image_url": "https://te.legra.ph/file/cc4b24dc0f54bc79ea998.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐃` ] 𝐑𝐚𝐧𝐤 𝐖𝐨𝐥𝐟 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 65,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Wolf... *fouled your Beast* 💀."
    },
    "4": {
        "image_url": "https://te.legra.ph/file/59bdd9842b4c98b75e5d2.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐂` ] 𝐑𝐚𝐧𝐤 𝐒𝐧𝐨𝐰 𝐖𝐨𝐥𝐟 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 45,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Snow Wolf... *fouled your Beast* 💀."
    },
    "5": {
        "image_url": "https://te.legra.ph/file/31ca2402a9309c3810a6b.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐀` ] 𝐑𝐚𝐧𝐤 𝐑𝐞𝐝 𝐎𝐫𝐜 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 5,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Orc... *fouled your Beast* 💀."
    },
    "6": {
        "image_url": "https://te.legra.ph/file/44df7f9ae15f9d543fec4.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐀` ] 𝐑𝐚𝐧𝐤 𝐋𝐢𝐜𝐡 𝐤𝐢𝐧𝐠 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 5,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Undead... *fouled your Beast* 💀."
    },
    "7": {
        "image_url": "https://files.catbox.moe/5k4qge.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐒` ] 𝐑𝐚𝐧𝐤 𝐄𝐦𝐞𝐫𝐚𝐥𝐝 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 40,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Emerald Monster... *fouled your Beast* 💀."
    },
    "8": {
        "image_url": "https://files.catbox.moe/4wnk20.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐒+` ] 𝐑𝐚𝐧𝐤 𝐏𝐥𝐚𝐭𝐢𝐧𝐮𝐦 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 25,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Platinum Monster... *fouled your Beast* 💀."
    },
    "9": {
        "image_url": "https://files.catbox.moe/ghc26e.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐊` ] 𝐑𝐚𝐧𝐤 𝐑𝐮𝐛𝐲 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 35,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Ruby Monster... *fouled your Beast* 💀."
    },
    "10": {
        "image_url": "https://files.catbox.moe/490776.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐊+` ] 𝐑𝐚𝐧𝐤 𝐒𝐚𝐩𝐩𝐡𝐢𝐫𝐞 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 20,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Sapphire Monster... *fouled your Beast* 💀."
    },
    "11": {
        "image_url": "https://files.catbox.moe/2sazgc.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐊++` ] 𝐑𝐚𝐧𝐤 𝐀𝐦𝐞𝐭𝐡𝐲𝐬𝐭 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 15,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Amethyst Monster... *fouled your Beast* 💀."
    },
    "12": {
        "image_url": "https://files.catbox.moe/1akk7p.jpg",
        "caption": "𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐟𝐨𝐮𝐧𝐝 𝐚𝐧 [ `𝐊+++` ] 𝐑𝐚𝐧𝐤 𝐎𝐛𝐬𝐢𝐝𝐢𝐚𝐧 𝐃𝐮𝐧𝐠𝐞𝐨𝐧.",
        "win_chance": 10,
        "loss_message": "<b>❌ You lost!</b> 💀\nAnd the Obsidian Monster... *fouled your Beast* 💀."
    }
}
async def send_log(log_message):
    await app.send_message(LOG_GROUP_CHAT_ID, log_message)

LOG_GROUP_CHAT_ID = -1001992198513
        
# Define a dictionary to store the last time each user executed the shunt command
last_usage_time_shunt = {}

user_last_command_times = {}

@app.on_message(filters.command(["hunt"]))
async def get_gem_command(client, message):
    user_id = message.from_user.id
    current_time = time.time()

    # Spam prevention
    if user_id in user_last_command_times and current_time - user_last_command_times[user_id] < 5:  # Adjust spam threshold
        return await message.reply_text("⚠️ You are sending commands too quickly. Please wait a moment.")

    user_last_command_times[user_id] = current_time

    # Log the usage of the command
    await send_log(f"Command /hunt used by user `{user_id}`")

    try:
        # Check if the user is on cooldown
        if user_id in last_usage_time_shunt:
            time_elapsed = current_time - last_usage_time_shunt[user_id]
            remaining_time = max(0, cooldown_duration_shunt - time_elapsed)
            if remaining_time > 0:
                return await message.reply_text(f"⏳ You're on cooldown. Please wait {int(remaining_time)} seconds before using this command again.")

        # Check if the user has joined the MUST_JOIN group/channel
        try:
            await app.get_chat_member(MUST_JOIN, user_id)
        except UserNotParticipant:
            # If not, prompt the user to join
            link = f"https://t.me/{MUST_JOIN}" if MUST_JOIN.isalpha() else (await app.get_chat(MUST_JOIN)).invite_link
            try:
                await message.reply_text(
                    f"🔒 You must join the support group/channel to use this command. Please join [here]({link}).",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔗 Join", url=link)]]
                    ),
                    disable_web_page_preview=True
                )
                return
            except ChatWriteForbidden:
                pass

        # Retrieve user data
        user_data = await user_collection.find_one({'id': user_id}, projection={'beasts': 1})
        if not user_data.get('beasts'):
            return await message.reply_text("🐾 You need a beast to hunt. Acquire a beast first using /beastshop.")

        # Proceed with gem shunt logic
        gem_set = random.choice(list(gem_sets.values()))
        image_url = gem_set["image_url"]
        caption = gem_set["caption"]
        win_chance = gem_set["win_chance"]
        loss_message = gem_set["loss_message"]

        # Send the image with the corresponding caption
        await message.reply_photo(photo=image_url, caption=caption)

        # Wait for 1 second before sending the message
        await asyncio.sleep(1)

        # Determine the gem won based on win rate percentage
        gem_won = None
        for gem, win_rate in gem_win_rates.items():
            if random.randint(1, 100) <= win_rate:
                gem_won = gem
                break

        # Check if the user wins
        if gem_won:
            # User wins, award gems
            await award_gems(user_id, message, gem_won)
            await message.reply_text(f"🎉 Congratulations! You won a **{gem_won}** gem! 🏆\n\nYour new treasure has been added to your collection.")
        else:
            # User loses
            await message.reply_text(f"💔 Unfortunately, you lost this round. {loss_message}")

        # Update the last usage time for the user
        last_usage_time_shunt[user_id] = current_time

    except Exception as e:
        # Log any exceptions that occur
        await send_log(f"Error occurred in get_gem_command: {e}")
        print(e)  # Print the exception for debugging purposes
        await message.reply_text("❌ An error occurred while processing your request. Please try again later.")

# Set the cooldown duration for the shunt command (in seconds)
cooldown_duration_shunt = 60  # 1 minute

gem_win_rates = {
    "Wood": 50,
    "Iron": 50,
    "Silver": 20,
    "Gold": 5,
    "Diamond": 1,
    "Platinum": 0.5,  # New
    "Emerald": 2,      # New
    "Ruby": 3,
    "Sapphire": 2,
    "Amethyst": 1,
    "Obsidian": 0.5
        }

async def award_gems(user_id, message, gem_won):
    user_data = await user_collection.find_one({'id': user_id})
    if user_data and user_data.get('gems'):
        gem_inventory = user_data['gems']
    else:
        gem_inventory = {}

    # Randomly select gems to award based on the gem won
    gems_to_award = {gem_won: random.randint(5, 10)}  # Adjust the quantity range as needed

    # Update user's gem inventory in the database
    for gem, quantity in gems_to_award.items():
        if gem in gem_inventory:
            gem_inventory[gem] += quantity
        else:
            gem_inventory[gem] = quantity
    await user_collection.update_one({'id': user_id}, {'$set': {'gems': gem_inventory}})
    
    # Send a message listing the awarded gems
    message_text = "🎉 𝐂𝐨𝐧𝐠𝐫𝐚𝐭𝐮𝐥𝐚𝐭𝐢𝐨𝐧𝐬! 𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐜𝐨𝐧𝐪𝐮𝐞𝐫𝐞𝐝 𝐭𝐡𝐞 𝐟𝐢𝐠𝐡𝐭! 🏆\n\n"
    message_text += "🌟 𝐘𝐨𝐮 𝐠𝐨𝐭 𝐭𝐡𝐞𝐬𝐞 𝐠𝐞𝐦𝐬:\n\n"
    
    for gem, quantity in gems_to_award.items():
        message_text += f"<b>✨ {gem}</b>: <b>{quantity}</b>\n"
    
    message_text += "\n💎 𝐄𝐧𝐣𝐨𝐲 𝐲𝐨𝐮𝐫 𝐛𝐨𝐨𝐬𝐭 𝐨𝐟 𝐠𝐞𝐦𝐬! 💎"
    
    await message.reply_text(message_text)
   
owner_id = 6402009857

@bot.on_message(filters.user(owner_id) & filters.command(["hreset"]))
async def reset_gems_command(_: bot, message: t.Message):
    # Check if the command is a reply to a user's message
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        # Reset gems for the specified user
        await user_collection.update_one({'id': user_id}, {'$unset': {'gems': 1}})
        await message.reply_text(f"loot reset for user {user_id}.")
    else:
        await message.reply_text("Please reply to the user's message to reset their loot.")

AUTHORIZED_USER_ID = 6402009857

@bot.on_message(filters.command(["itemreset"]))
async def item_reset_command(client, message):
    user_id = message.from_user.id
    if user_id != AUTHORIZED_USER_ID:
        await message.reply_text("You are not authorized to use this command.")
        return

    await user_collection.update_many({}, {'$set': {'gems': {}}})
    await message.reply_text("All users' items have been reset to zero.")
