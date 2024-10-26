from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

class Config(object):
    LOGGER = True

    OWNER_ID = "6402009857"
    sudo_users = [
        "6402009857", "7004889403", "1135445089", "5158013355", "5630057244", 
        "1374057577", "6305653111", "5421067814", "7497950160", "7334126640", 
        "6835013483", "1993290981", "1742711103", "6180567980"
    ]
    GROUP_ID = -1002104939708
    TOKEN = "7335799800:AAHgRmfPm4BPHRnQby1G7tsGkhFLyAGlwEQ"
    mongo_url = "mongodb+srv://seizewaifubot:seizewaifubot@itachi.9qya0.mongodb.net/?retryWrites=true&w=majority&appName=itachi"
    PHOTO_URL = [
        "https://telegra.ph/file/c74151f4c2b56a107a24b.jpg",
        "https://telegra.ph/file/6a81a91aa4a660a73194b.jpg",
        "https://telegra.ph/file/ffb2e954748d841176463.jpg",
        "https://telegra.ph/file/f20dbe987e174d03780f0.jpg"
    ]
    SUPPORT_CHAT = "dynamic_gangs"
    UPDATE_CHAT = "Seizer_update"
    BOT_USERNAME = "Character_seize_bot"
    CHARA_CHANNEL_ID = -1002049694247
    api_id = 29098103
    api_hash = "06baef4020832888ccf3ebf4e746d52b"
    JOINLOGS = -1002104939708
    LEAVELOGS = -1002104939708

    # New Administration System
    GRADE4 = []
    GRADE3 = ["7334126640"]
    GRADE2 = ["6305653111", "5421067814"]
    GRADE1 = ["7004889403", "1374057577", "5158013355", "5630057244", "7334126640", "5421067814"]
    SPECIALGRADE = ["6402009857", "1993290981"]

    Genin = []
    Chunin = []
    Jonin = ["7334126640"]
    Hokage = ["5421067814"]
    Akatsuki = ["6402009857", "5158013355", "5630057244"]
    Princess = ["1993290981"]

    @classmethod
    def add_sudo_user(cls, user_id: str):
        if user_id not in cls.sudo_users:
            cls.sudo_users.append(user_id)
            return True
        return False

class Production(Config):
    LOGGER = True

class Development(Config):
    LOGGER = True

# Bot command to add a new sudo user
def add_sudo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_id_str = str(user_id)

    if user_id_str == Config.OWNER_ID or user_id_str in Config.sudo_users:
        # Check if the command is used as a reply
        if update.message.reply_to_message:
            replied_user_id = str(update.message.reply_to_message.from_user.id)
            if Config.add_sudo_user(replied_user_id):
                update.message.reply_text(
                    f"User [{replied_user_id}](tg://user?id={replied_user_id}) has been added as a sudo user.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text(
                    f"User [{replied_user_id}](tg://user?id={replied_user_id}) is already a sudo user.",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text("Please reply to a user's message to add them as a sudo user.")
    else:
        update.message.reply_text("You don't have permission to use this command.")

# Initialize bot and command
def main():
    updater = Updater(Config.TOKEN)
    dp = updater.dispatcher

    # Add command handler for /addsudo
    dp.add_handler(CommandHandler("addsudo", add_sudo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
