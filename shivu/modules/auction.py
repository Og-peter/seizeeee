from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pyrogram.enums import ChatMemberStatus
import asyncio
from datetime import datetime, timedelta
import aiocron
from shivu import user_collection, shivuu as bot

CHANNEL_ID = -1002208875879
CHANNEL_USERNAME = "seize_market"  # Replace with your channel username
SUPPORT_GROUP_ID = -1002104939708  # Replace with your support group ID
OWNER_ID = 6402009857  # Replace with the owner ID

# Auction data storage
auction_data = {
    'active': False,
    'character': None,
    'bids': [],
    'message_id': None,
    'last_bid_time': None,
    'warning_sent': False
}

# Timeout duration for no new bids (2 minutes)
AUCTION_TIMEOUT = timedelta(minutes=2)

# Morning message to request character IDs for auction
@aiocron.crontab('0 8 * * *')
async def morning_auction_request():
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="Good morning! Ready to start an auction? Send the character ID you'd like to auction!"
    )
    await bot.send_message(
        chat_id=SUPPORT_GROUP_ID,
        text="Attention! Ready to start an auction today? Please provide a character ID to participate."
    )

# Check if a user is a channel member
async def check_channel_membership(user_id):
    try:
        member_status = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member_status.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

# Start an auction - restricted to owner
@bot.on_message(filters.command("startauction") & filters.user(OWNER_ID))
async def start_auction(client, message: t.Message):
    global auction_data

    args = message.command
    if len(args) != 2:
        return await message.reply_text("Usage: /startauction <character_id>")

    character_id = args[1]

    # Fetch character details from the database or user collection
    character_data = await user_collection.find_one({"characters.id": character_id}, {"characters.$": 1})
    if not character_data:
        return await message.reply_text("Character not found in the database.")
    character = character_data['characters'][0]

    auction_data = {
        'active': True,
        'character': character,
        'bids': [],
        'message_id': None,
        'last_bid_time': datetime.now(),
        'warning_sent': False
    }

    caption = (
        f"✨ Auction started for **{character.get('name', 'Unknown')}**!\n\n"
        f"⛩️ **Anime**: {character.get('anime', 'Unknown Anime')}\n"
        f"🍁 **Rarity**: {character.get('rarity', 'Unknown Rarity')}\n"
        "💰 Place your bids using /placebid <amount>!\n\n"
        "Note: Only users who have joined the official channel can participate."
    )

    img_url = character.get('img_url')
    if not img_url:
        return await message.reply_text("No image found for this character.")

    # Send auction details with image to the channel
    msg = await client.send_photo(
        chat_id=CHANNEL_ID,
        photo=img_url,
        caption=caption
    )

    auction_data['message_id'] = msg.id

    # Send the same auction message to the support group
    await client.send_photo(
        chat_id=SUPPORT_GROUP_ID,
        photo=img_url,
        caption=caption
    )

    await message.reply_text("Auction has started successfully in both the channel and support group!")

# Place a bid command - requires channel membership
@bot.on_message(filters.command("placebid"))
async def place_bid(client, message: t.Message):
    if not auction_data['active']:
        return await message.reply_text("No auction is currently active.")

    if not await check_channel_membership(message.from_user.id):
        return await message.reply_text(
            "Please join our channel to participate in the auction.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
            ])
        )

    try:
        bid_amount = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply_text("Please provide a valid bid amount.")

    user_data = await user_collection.find_one({'id': message.from_user.id})
    if not user_data or user_data.get('balance', 0) < bid_amount:
        return await message.reply_text("Insufficient balance for this bid.")

    # Add the new bid and sort by highest bid
    auction_data['bids'].append({'user_id': message.from_user.id, 'amount': bid_amount})
    auction_data['bids'].sort(key=lambda x: x['amount'], reverse=True)

    # Fetch character image URL
    img_url = auction_data['character'].get('img_url')
    if not img_url:
        return await message.reply_text("No image found for this character.")

    highest_bidder = next((user for user in auction_data['bids'] if user['amount'] == bid_amount), None)
    if highest_bidder:
        highest_bidder_mention = await bot.get_users(highest_bidder['user_id'])
        highest_bidder_mention = highest_bidder_mention.mention

    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=img_url,
        caption=f"New highest bid! {highest_bidder_mention} bid {bid_amount} coins for **{auction_data['character']['name']}**."
    )

    # Send a "view post" message to the support group with the latest bid info
    await bot.send_message(
        chat_id=SUPPORT_GROUP_ID,
        text=f"🎉 New bid placed!\n\n"
             f"User: {highest_bidder_mention}\n"
             f"Bid Amount: {bid_amount} coins\n\n"
             f"🔗 [View Auction Post](https://t.me/{CHANNEL_USERNAME}/{auction_data['message_id']})"
    )

    # Update last bid time
    auction_data['last_bid_time'] = datetime.now()

    # Reset warning flag
    auction_data['warning_sent'] = False

    await message.reply_text("Bid placed successfully!")

# View auction status
@bot.on_message(filters.command("viewauction"))
async def view_auction(client, message: t.Message):
    if not auction_data['active']:
        return await message.reply_text("There's no active auction at the moment.")

    # Retrieve character details
    character = auction_data['character']
    name = character.get('name', 'Unknown Character')
    anime = character.get('anime', 'Unknown Anime')
    rarity = character.get('rarity', 'Unknown Rarity')
    img_url = character.get('img_url')

    # Check if there are bids in the auction
    if auction_data['bids']:
        top_bids_list = []
        for idx, bid in enumerate(sorted(auction_data['bids'], key=lambda x: x['amount'], reverse=True)):
            user = await bot.get_users(bid['user_id'])
            mention = f"[{user.first_name}](tg://user?id={user.id})"  # Create a proper mention
            top_bids_list.append(f"{idx + 1}. {mention} - {bid['amount']} coins")
        top_bids = "\n".join(top_bids_list)
    else:
        top_bids = "No bids have been placed yet."

    caption = (
        f"🌋 **Current Auction**\n\n"
        f"⚜️ **Character**: {name}\n"
        f"⛩️ **Anime**: {anime}\n"
        f"🍁 **Rarity**: {rarity}\n\n"
        "💵 **Top Bids**:\n"
        f"{top_bids}"
    )

    if img_url:
        await message.reply_photo(img_url, caption=caption)
    else:
        await message.reply_text(caption)

async def add_character_to_collection(user_id, character):
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': character}},
        upsert=True
    )

async def check_auction_timeout():
    if auction_data['active'] and auction_data['last_bid_time']:
        time_diff = datetime.now() - auction_data['last_bid_time']
        if time_diff >= AUCTION_TIMEOUT and not auction_data['warning_sent']:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text="⏰ Last bid placed a while ago! If no new bids are placed soon, the auction will end."
            )
            await bot.send_message(
                chat_id=SUPPORT_GROUP_ID,
                text="⏰ No new bids placed. The auction will end soon unless a new bid is made."
            )
            auction_data['warning_sent'] = True

        if time_diff >= AUCTION_TIMEOUT and len(auction_data['bids']) > 0:
            winner = auction_data['bids'][0]
            winner_user = await bot.get_users(winner['user_id'])
            winner_mention = winner_user.mention

            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🏆 Auction for **{auction_data['character']['name']}** has ended!\n\n"
                     f"Winner: {winner_mention} with {winner['amount']} coins. Congratulations!"
            )
            
            await bot.send_message(
                chat_id=SUPPORT_GROUP_ID,
                text=f"🏆 Auction has ended!\n\n"
                     f"Character: **{auction_data['character']['name']}**\n"
                     f"Winner: {winner_mention} with a bid of {winner['amount']} coins. 🎉"
            )

            # Add character to winner's collection
            await add_character_to_collection(winner['user_id'], auction_data['character'])

            # End the auction and reset the data
            auction_data.update({
                'active': False,
                'character': None,
                'bids': [],
                'message_id': None,
                'last_bid_time': None,
                'warning_sent': False
            })
# Background task to regularly check for auction timeout
async def auction_timeout_task():
    while True:
        await check_auction_timeout()
        await asyncio.sleep(10)  # Check every 10 seconds

# Run the background timeout checker task
bot.loop.create_task(auction_timeout_task())
