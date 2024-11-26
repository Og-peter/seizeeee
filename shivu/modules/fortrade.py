import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UsernameInvalid
from shivu import shivuu as app, user_collection, collection


# Global storage for trade data and pagination states
trade_data = {}
pagination_state = {}

@app.on_message(filters.command("fortrade"))
async def fortrade_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Validate input
    if len(message.command) != 3:
        await message.reply_text("Usage: /fortrade <find_character_id> <own_character_id>")
        return

    # Extract character IDs
    find_id = message.command[1]
    own_id = message.command[2]

    # Fetch character details
    find_character = await collection.find_one({"id": find_id})
    own_character = await collection.find_one({"id": own_id})

    if not find_character or not own_character:
        await message.reply_text("Invalid character IDs provided. Please check and try again.")
        return

    # Store trade data
    trade_data[user_id] = {
        "find_id": find_id,
        "own_id": own_id,
        "find_img": find_character["img_url"],
        "own_img": own_character["img_url"],
        "find_name": find_character["name"],
        "own_name": own_character["name"]
    }

    # Display confirmation prompt with both images
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes", callback_data="trade_confirm_yes"),
         InlineKeyboardButton("No", callback_data="trade_confirm_no")]
    ])
    await message.reply_photo(
        photo=find_character["img_url"],
        caption=f"Are you sure you want to trade your character `{own_character['name']}` "
                f"for `{find_character['name']}`?",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r'^trade_confirm_'))
async def trade_confirmation(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    action = callback_query.data.split("_")[-1]

    if action == "yes":
        # Validate trade data
        trade_info = trade_data.get(user_id)
        if not trade_info:
            await callback_query.message.edit_text("Trade data not found. Please try again.")
            return

        find_id = trade_info["find_id"]

        # Fetch owners of the character
        owners = await user_collection.aggregate([
            {"$match": {"characters.id": find_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": find_id}},
            {"$group": {
                "_id": "$_id",
                "username": {"$first": "$username"},
                "first_name": {"$first": "$first_name"}
            }}
        ]).to_list(length=10)  # Limit to 10 owners

        # Save pagination state
        pagination_state[user_id] = {"owners": owners, "page": 0}

        await show_trade_page(client, callback_query.message, user_id)
    else:
        await callback_query.message.edit_text("Trade canceled.")

async def show_trade_page(client: Client, message: Message, user_id: int):
    state = pagination_state.get(user_id)
    if not state or not state["owners"]:
        await message.edit_text("No owners found for the requested character.")
        return

    page = state["page"]
    owners = state["owners"]
    owner = owners[page]

    # Fetch trade data
    trade_info = trade_data[user_id]
    find_img = trade_info["find_img"]
    own_img = trade_info["own_img"]
    find_name = trade_info["find_name"]
    own_name = trade_info["own_name"]

    # Display owner details with character images
    keyboard = [
        [InlineKeyboardButton("Send Request", callback_data=f"trade_request_{owner['_id']}")],
        [
            InlineKeyboardButton("◀", callback_data="trade_prev"),
            InlineKeyboardButton("▶", callback_data="trade_next")
        ]
    ]
    await message.reply_photo(
        photo=find_img,
        caption=f"Owner: {owner['first_name']} (@{owner.get('username', 'No username')})\n\n"
                f"Character you want: {find_name}\n"
                f"Character you are offering: {own_name}\n\n"
                f"(Page {page + 1}/{len(owners)})",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex(r'^trade_(prev|next|request)_'))
async def handle_trade_pagination(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    state = pagination_state.get(user_id)

    if not state:
        await callback_query.answer("Pagination state not found.", show_alert=True)
        return

    action = callback_query.data.split("_")[1]
    if action == "prev" and state["page"] > 0:
        state["page"] -= 1
    elif action == "next" and state["page"] < len(state["owners"]) - 1:
        state["page"] += 1
    elif action == "request":
        target_user_id = callback_query.data.split("_")[-1]
        await send_trade_request(client, callback_query, user_id, target_user_id)
        return

    await show_trade_page(client, callback_query.message, user_id)

async def send_trade_request(client: Client, callback_query: CallbackQuery, user_id: int, target_user_id: str):
    trade_info = trade_data.get(user_id)
    if not trade_info:
        await callback_query.answer("Trade data not found.", show_alert=True)
        return

    find_id = trade_info["find_id"]
    own_id = trade_info["own_id"]
    find_img = trade_info["find_img"]
    own_img = trade_info["own_img"]

    # Notify target user of the trade request
    await client.send_photo(
        chat_id=target_user_id,
        photo=own_img,
        caption=f"Trade request received!\n\n"
                f"From: {callback_query.from_user.first_name} (@{callback_query.from_user.username})\n"
                f"Requesting: {trade_info['find_name']}\nOffering: {trade_info['own_name']}\n\n"
                f"Use /accept or /reject to respond."
    )
    await callback_query.message.edit_text("Trade request sent successfully.")
