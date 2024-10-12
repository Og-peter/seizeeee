from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, Updater, CallbackQueryHandler
from datetime import datetime, timedelta
from pyrogram import filters

# Simulate user data storage with in-memory dictionaries
user_plants = {}
user_collection = {}

plant_image_urls = {
    1: "https://telegra.ph/file/8b017c909aca80620dd70.png",
    20: "https://telegra.ph/file/5c3b67113186e532effa1.jpg",
    40: "https://telegra.ph/file/5ae2de95199e349bc5a05.jpg",
    60: "https://telegra.ph/file/f9b1607ffe259b8aaac3d.png"
}

# Function to handle button click for claiming rewards
@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data == "claim"))
async def claim_reward_button(client, callback_query):
    user_id = callback_query.from_user.id

    # Retrieve user's plant data
    user_data = user_plants.get(user_id)

    if user_data:
        last_claim_time = user_data.get('last_claim_time')
        if last_claim_time and datetime.now() - last_claim_time < timedelta(days=1):
            await callback_query.answer("You have already claimed your coins for today.")
        else:
            coins = calculate_coins(user_data['level'])
            
            # Update user's balance
            user_balance_data = user_collection.get(user_id, {'balance': 0})
            user_balance_data['balance'] += coins
            user_balance_data['last_claim_time'] = datetime.now()
            user_collection[user_id] = user_balance_data

            user_data['last_claim_time'] = datetime.now()  # Update last claim time
            await callback_query.edit_message_text(text=f"🎉 You have claimed {coins} coins!")
    else:
        await callback_query.edit_message_text(text="You don't have a plant.")


# Function to handle /myplant command
async def my_plant(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Retrieve user's plant data
    user_data = user_plants.get(user_id)

    if user_data:
        plant_level = user_data['level']
        plant_image_url = get_plant_image_url(plant_level)
        message = f"🌱 Your plant, {user_name}, is currently at level {plant_level}. Keep growing it!\n\nYour unique code: {user_id}"

        # Create inline keyboard with a "Claim Reward" button
        keyboard = [[InlineKeyboardButton("Claim Reward", callback_data='claim')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with plant image, user's plant level, and the inline keyboard
        await update.message.reply_photo(photo=plant_image_url, caption=message, reply_markup=reply_markup)
    else:
        # If user doesn't have a plant, create one with initial level 1
        new_plant = {"user_id": user_id, "level": 1}
        user_plants[user_id] = new_plant
        plant_image_url = plant_image_urls[1]
        message = f"🌱 Welcome, {user_name}! Your new plant has been planted. Keep nurturing it to help it grow!\nYour code: {user_id}"

        # Send message with plant image
        await update.message.reply_photo(photo=plant_image_url, caption=message)


# Function to handle /code command
async def code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Please provide a target user's ID.")
        return

    target_user_id = int(context.args[0])

    if target_user_id == user_id:
        await update.message.reply_text("You cannot use the /code command with your own user ID.")
        return

    # Check if the user has already used the code
    user_data = user_plants.get(user_id)

    if user_data and user_data.get('code_used', False):
        await update.message.reply_text("You have already used your code.")
        return

    # Retrieve target user's plant data
    target_user_data = user_plants.get(target_user_id)

    if not target_user_data:
        await update.message.reply_text("The specified user does not exist or does not have a plant yet.")
        return

    # Increase target user's plant level by 1
    target_user_data['level'] += 1
    updated_level = target_user_data['level']

    # Mark the user's code as used
    user_data['code_used'] = True
    await update.message.reply_text(f"🌿 Congratulations! The plant belonging to user ID {target_user_id} has leveled up to level {updated_level}!")


# Function to handle /mycode command
async def my_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your user ID is: {user_id}")


# Function to calculate coins earned based on plant level
def calculate_coins(level):
    return level * 100


# Function to get plant image URL based on level
def get_plant_image_url(level):
    for threshold in sorted(plant_image_urls.keys(), reverse=True):
        if level >= threshold:
            return plant_image_urls[threshold]
    return plant_image_urls[1]


# Function to display top plant levels
async def top_plant_levels(update: Update, context: CallbackContext):
    # Sort users by plant level in descending order
    top_users = sorted(user_plants.items(), key=lambda x: x[1]['level'], reverse=True)[:10]

    top_users_info = []
    for idx, (user_id, data) in enumerate(top_users, start=1):
        user = await context.bot.get_chat(user_id)
        full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        user_link = f'<a href="tg://user?id={user.id}">{full_name}</a>'
        top_users_info.append(f"{user_link} - Level: {data['level']}")

    if top_users_info:
        message = "\n".join(top_users_info)
        pic = "https://telegra.ph/file/f466f1fdab10ab5a0fc11.jpg"
        await update.message.reply_photo(photo=pic, caption=f"Top 10 Users by Plant Level:\n\n{message}", parse_mode="HTML")
    else:
        await update.message.reply_text("No users found.")


# Set up the application with command handlers
application.add_handler(CommandHandler("myplant", my_plant))
application.add_handler(CommandHandler("mycode", my_code))
application.add_handler(CommandHandler("code", code))
application.add_handler(CommandHandler("ptop", top_plant_levels))

# Add the callback query handler for the claim reward button
application.add_handler(CallbackQueryHandler(claim_reward_button, pattern='claim'))
