from pyrogram import Client, filters
import random
import string
from datetime import datetime
from shivu import user_collection, collection 
from shivu import shivuu as app
from telegram.constants import ParseMode

# Dictionary to store generated codes and their amounts, and user claims
generated_codes = {}
generated_waifus = {}
pending_trades = {}
pending_gifts = {}

# List of sudo users (user IDs who can access special commands)
sudo_user_ids = ["6402009857","7334126640"]

# Function to generate a random string of length 10
def generate_random_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Function to format the amount
def format_amount(amount):
    return f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"

# Generate random codes with custom amounts and quantity
@app.on_message(filters.command(["gen"]))
async def gen(client, message):
    sudo_user_id = 6402009857  # Example sudo user
    if message.from_user.id != sudo_user_id:
        await message.reply_text("🚫 Sumimasen, but only the chosen ones can use this power.")
        return
    
    try:
        amount = float(message.command[1])  # Get the amount from the command
        quantity = int(message.command[2])  # Get the quantity from the command
    except (IndexError, ValueError):
        await message.reply_text("😅 Gomenasai! Invalid input. Try `/gen 10000000 5`")
        return
    
    # Generate a random code
    code = generate_random_code()
    
    # Store the generated code and its associated amount and quantity
    generated_codes[code] = {'amount': amount, 'quantity': quantity, 'claimed_by': []}
    
    formatted_amount = format_amount(amount)
    
    await message.reply_text(
        f"✨ Konnichiwa! 🌸 Your special code is here:\n`{code}`\n💰 Amount: Ŧ `{formatted_amount}`\n📦 Quantity: `{quantity}`\nGood luck, and may your journey bring many rewards!"
    )

# Redeem generated codes and update tokens
@app.on_message(filters.command(["redeem"]))
async def redeem(client, message):
    code = " ".join(message.command[1:])  # Get the code from the command
    user_id = message.from_user.id
    
    if code in generated_codes:
        code_info = generated_codes[code]
        
        # Check if the user has already claimed this code
        if user_id in code_info['claimed_by']:
            await message.reply_text("😅 Ah, you’ve already claimed this gift. No need to be greedy!")
            return
        
        # Check if there are claims remaining for the code
        if len(code_info['claimed_by']) >= code_info['quantity']:
            await message.reply_text("😮 Omoshiroi! This code has been fully claimed by others.")
            return
        
        # Update the user's tokens
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'tokens': float(code_info['amount'])}}  # Update tokens instead of balance
        )
        
        # Add user to the claimed_by list
        code_info['claimed_by'].append(user_id)
        
        formatted_amount = format_amount(code_info['amount'])
        
        await message.reply_text(
            f"🎉 Arigato! Successfully redeemed! Ŧ `{formatted_amount}` tokens have been added to your balance. Keep going, hero! 💪"
        )
    else:
        await message.reply_text("💔 Oh no, that code doesn’t exist in this realm. Try again!")

# Waifu Generation (only for sudo users)
@app.on_message(filters.command(["wgen"]))
async def waifugen(client, message):
    if str(message.from_user.id) not in sudo_user_ids:
        await message.reply_text("🙏 Gomen, but only chosen heroes can summon waifus.")
        return
    
    try:
        character_id = message.command[1]  # Get the character_id from the command
        quantity = int(message.command[2])  # Get the quantity from the command
    except (IndexError, ValueError):
        await message.reply_text("😅 Oops, incorrect usage. Try `/wgen 56 1`")
        return

    # Retrieve the waifu with the given character_id
    waifu = await collection.find_one({'id': character_id})
    if not waifu:
        await message.reply_text("🧐 Sadly, no waifu found with that ID. Double-check, brave warrior!")
        return

    code = generate_random_code()
    
    # Store the generated waifu and its details
    generated_waifus[code] = {'waifu': waifu, 'quantity': quantity}
    
    response_text = (
        f"🌸 Your Waifu Code has arrived!\n`{code}`\n"
        f"💖 Name: {waifu['name']}\n🌟 Rarity: {waifu['rarity']}\n📦 Quantity: {quantity}\nSummon her with honor! 🥀"
    )
    
    await message.reply_text(response_text)

# Waifu Redeem (users can claim waifus using codes)
@app.on_message(filters.command(["wredeem"]))
async def claimwaifu(client, message):
    code = " ".join(message.command[1:])  # Get the code from the command
    user_id = message.from_user.id
    user_mention = f"[{message.from_user.first_name}](tg://user?id={user_id})"

    if code in generated_waifus:
        details = generated_waifus[code]
        
        if details['quantity'] > 0:
            waifu = details['waifu']
            
            # Update the user's characters collection
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': waifu}}
            )
            
            # Decrement the remaining quantity
            details['quantity'] -= 1
            
            # Remove the code if its quantity is 0
            if details['quantity'] == 0:
                del generated_waifus[code]
            
            response_text = (
                f"🎊 Yatta! {user_mention}, you have received a new companion! 🌸\n"
                f"💖 Name: {waifu['name']}\n"
                f"🌟 Rarity: {waifu['rarity']}\n"
                f"📺 Anime: {waifu['anime']}\n"
                "May she bring you strength and fortune! 💫"
            )
            await message.reply_photo(photo=waifu['img_url'], caption=response_text)
        else:
            await message.reply_text("😢 Alas, this code has been fully claimed.")
    else:
        await message.reply_text("❌ Invalid code. It seems to be lost in another dimension.")
