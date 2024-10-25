import random
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection  # Make sure to import the user_collection
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from pyrogram.types import Message  
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from shivu import application
from html import escape

beast_list = {
    1: {'name': '𝐋𝐮𝐜𝐲', 'price': 5000000, 'rarity': '🐱 𝐂𝐚𝐭', 'power': 500, 'img_url': 'https://telegra.ph/file/2d16aafc2a1d20279576b.jpg'},
    2: {'name': '𝐌𝐨𝐥𝐥𝐲', 'price': 1000000, 'rarity': '🐮 𝐂𝐨𝐰', 'power': 1000, 'img_url': 'https://telegra.ph/file/8438048c906fb6fb0842a.jpg'},
    3: {'name': '𝐂𝐡𝐥𝐨𝐞', 'price': 7500000, 'rarity': '🦊 𝐅𝐨𝐱', 'power': 2000, 'img_url': 'https://telegra.ph/file/037828e8ccef4452f5c50.jpg'},
    4: {'name': '𝐊𝐢𝐫𝐛𝐲', 'price': 10000000, 'rarity': '🐰 𝐁𝐮𝐧𝐧𝐲', 'power': 1000, 'img_url': 'https://telegra.ph/file/6ae41e632f458dbbb86c3.jpg'},
    5: {'name': '𝐒𝐢𝐨𝐧𝐢𝐚', 'price': 50000000, 'rarity': '🌱 𝐄𝐥𝐟', 'power': 50000, 'img_url': 'https://telegra.ph/file/bf28ceee27952160b7d84.jpg'},
    6: {'name': '𝐅𝐫𝐞𝐝𝐚', 'price': 75000000, 'rarity': '🍑 𝐒𝐮𝐜𝐂𝐮𝐜𝐮𝐬', 'power': 100000, 'img_url': 'https://telegra.ph/file/0b716a53aac17149e103e.jpg'},
    7: {'name': '𝐂𝐚𝐥𝐚𝐭𝐡𝐢𝐞𝐥', 'price': 100000000, 'rarity': '🐉 𝐃𝐫𝐚𝐠𝐨𝐧', 'power': 200000, 'img_url': 'https://telegra.ph/file/02599485060905307df60.jpg'},
    8: {'name': '𝐆𝐞𝐧𝐞𝐯𝐚', 'price': 250000, 'rarity': '🍃 𝐆𝐨𝐛𝐥𝐢𝐧', 'power': 1000, 'img_url': 'https://telegra.ph/file/db9cd322bf613f147b582.jpg'},
    9: {'name': '𝐇𝐚𝐳𝐞𝐥', 'price': 60000000, 'rarity': '🍁 𝐎𝐧𝐢', 'power': 15000, 'img_url': 'https://telegra.ph/file/7a8a5150e1a529e3b6129.jpg'},
    10: {'name': '𝐂𝐨𝐫𝐚𝐥', 'price': 40000000, 'rarity': '🌳 𝐖𝐨𝐫𝐥𝐝 𝐓𝐫𝐞𝐞', 'power': 30000, 'img_url': 'https://telegra.ph/file/363b22dade9c40a455b2f.jpg'},
    11: {'name': '𝐁𝐫𝐢𝐚𝐫', 'price': 20000000, 'rarity': '🍂 𝐃𝐚𝐫𝐤 𝐄𝐥𝐟', 'power': 75000, 'img_url': 'https://telegra.ph/file/149af3b400acdfbbbc285.jpg'},
    12: {'name': '𝐀𝐮𝐫𝐞𝐥𝐢𝐚', 'price': 80000000, 'rarity': '👹 𝐃𝐞𝐦𝐨𝐧', 'power': 100000, 'img_url': 'https://telegra.ph/file/c8bb74fcab42f1526a1a8.jpg'},
    13: {'name': '𝐀𝐭𝐥𝐚𝐧𝐭𝐚', 'price': 150000000, 'rarity': '🍑 𝐒𝐮𝐜𝐂𝐮𝐜𝐮𝐬', 'power': 150000, 'img_url': 'https://telegra.ph/file/408ee266bcecdb439ad16.jpg'},
    14: {'name': '𝐍𝐞𝐥𝐥𝐢𝐞', 'price': 200000000, 'rarity': '🪽 𝐀𝐧𝐠𝐞𝐥', 'power': 200000, 'img_url': 'https://telegra.ph/file/30dcc5f1eaa1df4ed50a5.jpg'}
}
async def get_user_data(user_id):
    return await user_collection.find_one({'id': user_id})

cooldowns = {}

@bot.on_message(filters.command(["beastshop"]))
async def beastshop_cmd(_: bot, update: Update):
    # Display a list of available beasts and their prices
    beast_list_text = "\n".join([
        f"🦁 **{beast_id}. {beast['name']}**\n"
        f"   𝐑𝐚𝐜𝐞 : {beast['rarity']}\n"
        f"   💰 **Price** : Ŧ`{beast['price']}`"
        for beast_id, beast in beast_list.items()
    ])
    
    # Sending the formatted message
    message_text = (
        "⛩️ **Welcome To Beast Shop!**\n\n"
        "🦄 **Available Beasts:**\n"
        "───────────────────────────\n"
        f"{beast_list_text}\n\n"
        "🛒 Use `/buybeast <beast_id>` to purchase a beast."
    )
    
    return await update.reply_text(message_text, parse_mode='Markdown')
@bot.on_message(filters.command(["buybeast"]))
async def buybeast_cmd(_: bot, update: Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

    if beast_id is not None:
        beast_type = beast_list[beast_id]['name'].lower()
        if 'beasts' in user_data and any(beast['name'].lower() == beast_type for beast in user_data.get('beasts', [])):
            return await update.reply_text(
                f"❌ You already own a **{beast_type.capitalize()}** beast.\n"
                f"Choose a different type from /beastshop."
            )

    if beast_id not in beast_list:
        return await update.reply_text(
            "🚫 Invalid Beast ID.\n"
            "Usage: `/buybeast <beast_id>`.\n"
            "Check the available beasts at /beastshop."
        )

    beast_price = beast_list[beast_id]['price']
    if user_data.get('balance', 0) < beast_price:
        return await update.reply_text(
            f"💔 You don't have enough tokens to buy this beast.\n"
            f"You need **Ŧ{beast_price}** tokens."
        )

    # Inline buttons for confirmation
    confirm_button = InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_buybeast_{beast_id}")
    reject_button = InlineKeyboardButton("❌ Reject", callback_data="reject")
    keyboard = InlineKeyboardMarkup([[confirm_button, reject_button]])

    await update.reply_photo(
        photo=beast_list[beast_id]['img_url'],
        caption=(
            f"🐉 **Do you want to buy this beast?**\n\n"
            f"**Name:** {beast_list[beast_id]['name']}\n"
            f"**Price:** Ŧ{beast_price}\n"
            f"**Type:** {beast_list[beast_id]['rarity']}\n\n"
            f"Click below to confirm your purchase!"
        ),
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.on_callback_query(filters.regex(r"confirm_buybeast_(\d+)"))
async def confirm_buybeast_callback(_, callback_query: t.CallbackQuery):
    beast_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    user_data = await get_user_data(user_id)

    beast_price = beast_list[beast_id]['price']
    if user_data.get('balance', 0) < beast_price:
        return await callback_query.message.edit_text(
            "❌ **Insufficient Tokens**\n"
            f"You don't have enough tokens to buy this beast.\n"
            f"You need **Ŧ{beast_price}** tokens."
        )

    # Deduct the price from the user's balance
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -beast_price}})
    
    # Create new beast object
    new_beast = {
        'id': beast_id,
        'name': beast_list[beast_id]['name'],
        'rarity': beast_list[beast_id]['rarity'],
        'img_url': beast_list[beast_id]['img_url'],
        'power': beast_list[beast_id]['power']
    }
    
    # Add the new beast to the user's collection
    await user_collection.update_one({'id': user_id}, {'$push': {'beasts': new_beast}})

    # Edit the message to confirm the purchase
    await callback_query.message.edit_text(
        f"🎉 **Purchase Successful!**\n"
        f"You have successfully purchased a **{beast_list[beast_id]['name']}**!\n\n"
        f"🦄 **Type:** {beast_list[beast_id]['rarity']}\n"
        f"💰 **Price:** Ŧ{beast_price}\n\n"
        f"Your new beast is ready!"
    )

    # Send the new beast's image with a congratulatory message
    await callback_query.message.reply_photo(
        photo=beast_list[beast_id]['img_url'],
        caption="✨ **Meet Your New Beast!** ✨\n"
                f"**Name:** {beast_list[beast_id]['name']}\n"
                f"**Rarity:** {beast_list[beast_id]['rarity']}\n"
                f"**Power:** {beast_list[beast_id]['power']}\n"
                "Unleash its power in your adventures!"
    )
    
@bot.on_message(filters.command(["beast"]))
async def showbeast_cmd(_, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    # Check if the user has any beasts
    if 'beasts' in user_data and user_data['beasts']:
        # Check if the user has a main beast set
        main_beast_id = user_data.get('main_beast')

        # Generate text for other beasts
        other_beasts_text = "\n".join([
            f"🦄 **ID:** {beast.get('id', 'N/A')} ⌠ **Rarity:** {beast.get('rarity', 'N/A')} ⌡ **Name:** {beast.get('name', 'N/A')} (💪 **Power:** `{beast.get('power', 'N/A')}`)" 
            for beast in user_data['beasts']
        ])

        if main_beast_id:
            main_beast = next((beast for beast in user_data['beasts'] if beast['id'] == main_beast_id), None)
            if main_beast:
                await update.reply_photo(
                    photo=main_beast['img_url'],
                    caption="⛩️ **Your Main Beast Waifu** ⛩️\n\n" + other_beasts_text + "\n\n🔍 Use /binfo <ID> to see details about your beasts."
                )
                return

        # If there's no main beast, just show other beasts
        return await update.reply_text(
            "🐾 **Your Beasts**:\n\n" + other_beasts_text + "\n\n✨ Explore more by using /binfo <ID> to learn about each beast!"
        )
    
    return await update.reply_text("🚫 You don't have any beasts. Buy a beast using `/beastshop`.")
    
# Add a new command to show beast details along with an image
from pyrogram import filters
from pyrogram.types import Update
from html import escape

@bot.on_message(filters.command(["binfo"]))
async def showbeastdetails_cmd(_, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    if 'beasts' in user_data and user_data['beasts']:
        beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

        if beast_id is not None:
            selected_beast = next((beast for beast in user_data.get('beasts', []) if beast.get('id') == beast_id), None)

            if selected_beast and all(key in selected_beast for key in ('img_url', 'name', 'rarity', 'power')):
                user_first_name = update.from_user.first_name
                user_link = f'<a href="tg://user?id={user_id}">{escape(user_first_name)}</a>'
                caption = (
                    f"OWO! Check Out This {user_link}'s Beast!\n\n"
                    f"🌸 Name: {selected_beast['name']}\n"
                    f"🧬 Beast Race: {selected_beast['rarity']}\n"
                    f"🔮 Power: `{selected_beast['power']}`\n"
                    f"🆔 Beast ID: `{beast_id}`\n\n"
                    "Use `/setbeast <id>` to set this as your main beast."
                )
                await update.reply_photo(photo=selected_beast['img_url'], caption=caption)
                return
    
    await update.reply_text("You don't own that beast. Use `/binfo` to see your available beasts.")

@bot.on_message(filters.command(["givebeast"]) & filters.user(6402009857))
async def givebeast_cmd(_: bot, update: t.Update):
    try:
        # Extract user_id and beast_id from the command
        _, user_id, beast_id = update.text.split()
        user_id = int(user_id)
        beast_id = int(beast_id)

        # Check if the beast_id is valid
        if beast_id not in beast_list:
            return await update.reply_text("Invalid beast ID. Choose a valid beast ID.")

        # Check if the user exists
        user_data = await get_user_data(user_id)
        if not user_data:
            return await update.reply_text("User not found.")

        # Add the new beast to the user's list of beasts with rarity information
        new_beast = {'id': beast_id, 'name': beast_list[beast_id]['name'], 'rarity': beast_list[beast_id]['rarity'], 'img_url': beast_list[beast_id]['img_url'], 'power': beast_list[beast_id]['power']}
        await user_collection.update_one({'id': user_id}, {'$push': {'beasts': new_beast}})

        return await update.reply_text(f"Beast {beast_list[beast_id]['name']} has been successfully given to user {user_id}.")

    except ValueError:
        return await update.reply_text("Invalid command format. Use /givebeast <user_id> <beast_id>.")

# Command for the bot owner to delete all beasts of a user
@bot.on_message(filters.command(["delbeast"]) & filters.user(6402009857))
async def deletebeasts_cmd(_: bot, update: t.Update):
    try:
        # Extract user_id from the command
        _, user_id = update.text.split()
        user_id = int(user_id)

        # Check if the user exists
        user_data = await get_user_data(user_id)
        if not user_data:
            return await update.reply_text("User not found.")

        # Remove all beasts of the user
        await user_collection.update_one({'id': user_id}, {'$unset': {'beasts': 1}})

        return await update.reply_text(f"All beasts of user {user_id} have been deleted.")

    except ValueError:
        return await update.reply_text("Invalid command format. Use /delbeast <user_id>.")

@bot.on_message(filters.command(["setbeast"]))
async def setbeast_cmd(_: bot, update: t.Update):
    user_id = update.from_user.id
    user_data = await get_user_data(user_id)

    if 'beasts' in user_data and user_data['beasts']:
        beast_id = int(update.text.split()[1]) if len(update.text.split()) > 1 else None

        if beast_id is not None:
            if any(beast['id'] == beast_id for beast in user_data['beasts']):
                # Inline buttons for confirmation
                confirm_button = InlineKeyboardButton("Confirm", callback_data=f"confirm_setbeast_{beast_id}")
                reject_button = InlineKeyboardButton("Reject", callback_data="reject")
                keyboard = InlineKeyboardMarkup([[confirm_button, reject_button]])

                return await update.reply_text(f"Are you sure you want to set beast {beast_id} as your main beast?", reply_markup=keyboard)
            else:
                return await update.reply_text("You don't own a beast with that ID.")
        else:
            return await update.reply_text("Invalid command format. Use `/setbeast <beast_id>`.")
    else:
        return await update.reply_text("You don't have any beasts. Buy a beast using `/beastshop`.")

@bot.on_callback_query(filters.regex(r"confirm_setbeast_(\d+)"))
async def confirm_setbeast_callback(_, callback_query: t.CallbackQuery):
    beast_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    await user_collection.update_one({'id': user_id}, {'$set': {'main_beast': beast_id}})
    await callback_query.message.edit_text(f"Your main beast has been set successfully!")

@bot.on_message(filters.command(["btop"]))
async def top_beasts(_, message: Message):
    top_users = await user_collection.aggregate([
        {"$project": {"id": 1, "first_name": 1, "num_beasts": {"$size": {"$ifNull": ["$beasts", []]}}}},
        {"$sort": {"num_beasts": -1}},
        {"$limit": 10}
    ]).to_list(10)

    if top_users:
        response = "Top 10 Users With Most Beast's :\n\n"
        for index, user_data in enumerate(top_users, start=1):
            first_name = user_data.get('first_name', 'N/A')
            num_beasts = user_data.get('num_beasts', 0)
            user_id = user_data.get('id')
            user_link = f'<a href="tg://user?id={user_id}">{escape(first_name)}</a>'
            response += f"({index}) {user_link} ➾ `{num_beasts}` beast's\n"

        # Button to check your rank
        my_rank_button = InlineKeyboardButton("Check Your Rank", callback_data="check_rank")
        keyboard = InlineKeyboardMarkup([[my_rank_button]])

        random_photo_url = "https://telegra.ph/file/049a2fb78ed521c8e1ff6.jpg"

        await message.reply_photo(photo=random_photo_url, caption=response, reply_markup=keyboard)
    else:
        await message.reply_text("No users found.")

@bot.on_callback_query(filters.regex("check_rank"))
async def check_rank_callback(_, callback_query: t.CallbackQuery):
    user_id = callback_query.from_user.id

    user_rank = await user_collection.aggregate([
        {"$project": {"id": 1, "num_beasts": {"$size": {"$ifNull": ["$beasts", []]}}}},
        {"$sort": {"num_beasts": -1}}
    ]).to_list(None)

    rank = next((index + 1 for index, user in enumerate(user_rank) if user['id'] == user_id), None)

    if rank:
        await callback_query.message.edit_text(f"Your current rank is #{rank}.")
    else:
        await callback_query.message.edit_text("You are not ranked yet.")
