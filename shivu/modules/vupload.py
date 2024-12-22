import os
import requests
from pymongo import ReturnDocument
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

WRONG_FORMAT_TEXT_VIDEO = """⚠️ *Invalid Format!*
Please use the correct format:
`/up <Video_URL> <character_name> <anime_name> <rarity_number>`.

Examples:
- `/up https://files.catbox.moe/btit4d.mp4 Naruto Naruto_Shonen 1`
"""

RARITY_MAP = {
    1: "⚜️ Animated",
    2: "🌟 Ultra Rare",
    3: "⭐ Rare",
    4: "✨ Common",
    5: "🔸 Basic",
}

CATEGORY_MAP = {
    '❄️': '❄️ Infinity ❄️',
    '🔥': '🔥 Flame Master 🔥',
    '🌊': '🌊 Water Bender 🌊',
    '⚡': '⚡ Lightning Wizard ⚡',
    # Add more categories here
}

def get_category(name):
    for emoji, category in CATEGORY_MAP.items():
        if emoji in name:
            return category
    return "🌟 Unknown"

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

async def upload_video(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('⛔ *Access Denied!* Only the owner can use this command.')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT_VIDEO, parse_mode='Markdown')
            return

        video_url, character_name, anime_name, rarity_number = args
        character_name = character_name.replace('-', ' ').title()
        anime_name = anime_name.replace('-', ' ').title()

        # Validate rarity
        rarity = RARITY_MAP.get(int(rarity_number))
        if not rarity:
            await update.message.reply_text(f"❌ *Invalid Rarity!*\nValid rarities: {', '.join(map(str, RARITY_MAP.keys()))}", parse_mode='Markdown')
            return

        # Generate unique ID
        character_id = str(await get_next_sequence_number('character_id')).zfill(3)
        category = get_category(character_name)

        # Character data
        character_data = {
            'img_url': video_url,
            'name': character_name,
            'anime': anime_name,
            'rarity': rarity,
            'id': character_id,
            'category': category
        }

        # Caption for the channel
        caption = (
            f"🎥 *New Character Added!*\n\n"
            f"🎭 *Anime:* {anime_name}\n"
            f"🆔 *ID:* {character_id}\n"
            f"🌟 *Name:* {character_name}\n"
            f"🏆 *Rarity:* {rarity}\n"
            f"🔖 *Category:* {category}\n\n"
            f"➼ *Added By:* [{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
        )

        # Buttons
        buttons = [
            [
                InlineKeyboardButton("📺 View in Channel", url=f"https://t.me/{CHARA_CHANNEL_ID}/{character_id}"),
            ],
            [
                InlineKeyboardButton(f"🔍 Search {anime_name}", callback_data=f"search_anime_{anime_name}"),
                InlineKeyboardButton(f"🔍 Search {character_name}", callback_data=f"search_character_{character_name}")
            ],
            [
                InlineKeyboardButton("📩 Report Issue", url=f"https://t.me/{SUPPORT_CHAT}")
            ]
        ]

        # Handle Catbox URL
        local_file = None
        try:
            response = requests.get(video_url)
            if response.status_code == 200:
                local_file = f"{character_id}.mp4"
                with open(local_file, "wb") as file:
                    file.write(response.content)
            else:
                raise Exception("Failed to download the video from the provided URL.")
        except Exception as e:
            await update.message.reply_text(f"❌ *Invalid URL or Unable to Download Video!*\nError: {str(e)}", parse_mode='Markdown')
            return

        # Upload video to channel
        try:
            if local_file:
                with open(local_file, "rb") as video:
                    message = await context.bot.send_video(
                        chat_id=CHARA_CHANNEL_ID,
                        video=video,
                        caption=caption,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    character_data['message_id'] = message.message_id

                await collection.insert_one(character_data)
                await update.message.reply_text("✅ *Character Added Successfully!*", parse_mode='Markdown')
            else:
                raise Exception("Local file is missing.")
        except Exception as e:
            await update.message.reply_text(f"❌ *Failed to Upload Character!*\nError: {str(e)}", parse_mode='Markdown')
        finally:
            # Clean up local file
            if local_file and os.path.exists(local_file):
                os.remove(local_file)

    except Exception as e:
        await update.message.reply_text(f"❌ *Unexpected Error:*\n{str(e)}", parse_mode='Markdown')

# Add handler for the command
application.add_handler(CommandHandler('upvideo', upload_video))
