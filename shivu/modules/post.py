from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import user_collection, shivuu as bot
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, ChatAdminRequired
from pyrogram.enums import ChatMemberStatus
import asyncio

CHANNEL_ID = -1002208875879
CHANNEL_USERNAME = "seize_market"  # Ganti dengan username channel kamu
GROUP_URL = "https://t.me/dynamic_gangs"

# Fungsi untuk memeriksa keanggotaan pengguna di channel menggunakan username
async def check_channel_membership(user_id, channel_username):
    try:
        member_status = await bot.get_chat_member(channel_username, user_id)
        return member_status.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        print("Bot needs to be an admin in the channel to check membership.")
        return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

# Fungsi untuk mengurangi atau menambah balance
async def update_balance(user_id, amount):
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        user_data = {'id': user_id, 'balance': 0}

    user_data['balance'] = user_data.get('balance', 0) + amount
    await user_collection.update_one({'id': user_id}, {'$set': user_data}, upsert=True)

# Fungsi retry untuk menangani error RANDOM_ID_DUPLICATE
async def send_with_retry(func, *args, retries=3, **kwargs):
    attempt = 0
    while attempt < retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if "RANDOM_ID_DUPLICATE" in str(e):
                attempt += 1
                await asyncio.sleep(1)  # Tunggu sebelum mencoba kembali
            else:
                raise e
    raise Exception("Failed to send message after retries")

@bot.on_message(filters.command("post"))
async def post_character(_, message: t.Message):
    user_id = message.from_user.id
    args = message.command

    # Cek apakah pengguna sudah join channel menggunakan username
    is_member = await check_channel_membership(user_id, CHANNEL_USERNAME)
    if not is_member:
        return await message.reply_text(
            "🚫 Oops! It seems like you're not a part of our official channel yet. Join now to share your characters with everyone!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
            ])
        )

    # Cek format perintah
    if len(args) != 3:
        return await message.reply_text("❓ How to use: `/post {char_id} {price}`.\nMake sure to provide the correct details!")

    character_id, price_in_balance_str = args[1], args[2]

    # Validasi harga balance
    try:
        price_in_balance = int(price_in_balance_str)
    except ValueError:
        return await message.reply_text("💸 The price must be a valid integer. Check and try again!")

    # Ambil data pengguna dari database
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data or 'characters' not in user_data:
        return await message.reply_text("😢 You currently don't own any characters! Collect some first.")

    # Cari karakter dengan id_char
    character = next((char for char in user_data['characters'] if char['id'] == character_id), None)

    if not character:
        return await message.reply_text("🚫 Character not found! Make sure you're posting a character you own.")

    # Posting karakter ke channel
    caption = (
        f"🥂 {message.from_user.mention} is selling an exclusive character!\n\n"
        f"⚡ **Name**: {character['name']}\n"
        f"⚜️ **Anime**: {character['anime']}\n"
        f"❄️ **Rarity**: {character['rarity']}\n"
        f"💵 **Price**: {price_in_balance} balance\n\n"
        "💡 *Grab it before someone else does!*"
    )
    
    # Membuat tombol "Buy It"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Buy It", callback_data=f"buy_{user_id}_{character_id}_{price_in_balance}")]
    ])

    # Mengirim postingan ke channel dengan retry
    try:
        post_message = await send_with_retry(
            bot.send_photo,
            chat_id=f"@{CHANNEL_USERNAME}",
            photo=character['img_url'],
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error sending photo: {e}")
        return await message.reply_text("😓 Failed to post character. Please try again in a moment.")

    post_message_id = post_message.id if hasattr(post_message, 'id') else post_message.message_id

    # Kirim pesan konfirmasi ke pengguna
    await message.reply_text(
        f"🎉 Your character has been posted successfully!\n[👀 View Your Post](https://t.me/{CHANNEL_USERNAME}/{post_message_id})",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 View Post", url=f"https://t.me/{CHANNEL_USERNAME}/{post_message_id}")]
        ])
    )

@bot.on_callback_query(filters.regex(r"buy_(\d+)_(\d+)_(\d+)"))
async def handle_buy(_, query: t.CallbackQuery):
    try:
        # Uraikan data dari callback query
        data = query.data.split('_')
        if len(data) != 4:
            return await query.answer("🚫 Invalid callback data format. Please try again.", show_alert=True)

        seller_id = int(data[1])
        character_id = data[2]
        price_in_balance = int(data[3])

        buyer_id = query.from_user.id

        # Cek apakah pembeli adalah penjual
        if buyer_id == seller_id:
            return await query.answer("🛑 You cannot buy your own character!", show_alert=True)

        # Ambil balance pembeli
        buyer_data = await user_collection.find_one({'id': buyer_id})
        if not buyer_data or buyer_data.get('balance', 0) < price_in_balance:
            return await query.answer("💸 Insufficient balance! Top up and try again.", show_alert=True)

        # Ambil data penjual dari MongoDB
        seller_data = await user_collection.find_one({'id': seller_id})
        if not seller_data or 'characters' not in seller_data:
            print(f"Error: seller_data or characters not found for seller {seller_id}")
            return await query.answer("🚫 Seller data or characters not found. Please try again later.", show_alert=True)

        # Cek apakah karakter masih ada di daftar penjual
        character = next((char for char in seller_data['characters'] if char['id'] == character_id), None)
        if not character:
            print(f"Error: Character {character_id} is no longer available for seller {seller_id}")
            return await query.answer("❌ Character is no longer available!", show_alert=True)

        # Lanjutkan proses transfer karakter
        seller_data['characters'].remove(character)
        if 'characters' not in buyer_data:
            buyer_data['characters'] = []
        buyer_data['characters'].append(character)

        # Update balance
        buyer_data['balance'] -= price_in_balance
        seller_data['balance'] = seller_data.get('balance', 0) + price_in_balance

        # Simpan perubahan ke database
        await user_collection.update_one({'id': buyer_id}, {'$set': {'characters': buyer_data['characters'], 'balance': buyer_data['balance']}})
        await user_collection.update_one({'id': seller_id}, {'$set': {'characters': seller_data['characters'], 'balance': seller_data['balance']}})

        # Ambil informasi pengguna
        try:
            seller_user = await bot.get_users(seller_id)
            seller_mention = seller_user.mention
        except Exception as e:
            print(f"Error fetching seller's user info: {e}")
            seller_mention = "Seller"

        try:
            buyer_user = await bot.get_users(buyer_id)
            buyer_mention = buyer_user.mention
        except Exception as e:
            print(f"Error fetching buyer's user info: {e}")
            buyer_mention = "Buyer"

        # Update caption untuk menunjukkan karakter terjual
        sold_out_caption = (
            f"{seller_mention} is selling a character!\n\n"
            f"🎀 **Name**: {character['name']}\n"
            f"⚜️ **Anime**: {character['anime']}\n"
            f"⚕️ **Rarity**: {character['rarity']}\n"
            f"💵 **Status**: Sold Out\n"
            f"🔖 **Sold by**: {buyer_mention}"
        )

        # Perbarui caption jika berbeda dengan yang ada saat ini
        current_caption = query.message.caption
        if current_caption != sold_out_caption:
            try:
                await query.message.edit_caption(caption=sold_out_caption)
            except Exception as e:
                print(f"Error updating caption: {e}")

        # Kirim pesan ke pembeli dan penjual
        await query.answer("🎉 Purchase successful! Check your DMs for details.", show_alert=True)

        # Kirim pesan ke penjual
        await bot.send_message(
            seller_id,
            f"🎉 Your character **{character['name']}** has been bought by {buyer_mention}!\n"
            f"💰 You've received **{price_in_balance} balance**. Keep collecting and trading characters!"
        )

        # Kirim pesan ke pembeli
        await bot.send_message(
            buyer_id,
            f"🎉 Congratulations! You've successfully bought **{character['name']}** from {seller_mention}.\n"
            f"💸 It cost you **{price_in_balance} balance**. Enjoy your new character!"
        )

    except Exception as e:
        print(f"Error handling purchase: {e}")
        await query.answer("⚠️ An error occurred while processing the purchase. Please try again later.", show_alert=True)
