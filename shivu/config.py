from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

class Development:
    # Define all the required configurations here
    api_id = 29098103
    api_hash = "06baef4020832888ccf3ebf4e746d52b"
    TOKEN = "7335799800:AAHgRmfPm4BPHRnQby1G7tsGkhFLyAGlwEQ"  # Replace with your actual bot token
    GROUP_ID = -1002104939708
    CHARA_CHANNEL_ID = -1002049694247
    mongo_url = "mongodb+srv://seizewaifubot:seizewaifubot@itachi.9qya0.mongodb.net/?retryWrites=true&w=majority&appName=itachi"  # Replace with your actual MongoDB URL
    PHOTO_URL = [
        "https://telegra.ph/file/c74151f4c2b56a107a24b.jpg",
        "https://telegra.ph/file/6a81a91aa4a660a73194b.jpg"
    ]
    SUPPORT_CHAT = "dynamic_gangs"
    UPDATE_CHAT = "Seizer_update"
    BOT_USERNAME = "Character_seize_bot"
    OWNER_ID = "6402009857"
    sudo_users = ["6402009857", "7004889403"]
    JOINLOGS = -1002104939708
    LEAVELOGS = -1002104939708

    # User Roles
    GRADE4 = []
    GRADE3 = ["7334126640"]
    GRADE2 = ["6305653111", "5421067814"]
    GRADE1 = ["7004889403", "1374057577", "5158013355", "5630057244", "7334126640", "5421067814"]
    SPECIALGRADE = ["6402009857", "1993290981"]

    @classmethod
    def add_sudo_user(cls, user_id: str):
        if user_id not in cls.sudo_users:
            cls.sudo_users.append(user_id)
            return True
        return False

# Command to add a new sudo user
def add_sudo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_id_str = str(user_id)

    # Only the owner and sudo users can add others as sudo
    if user_id_str == Development.OWNER_ID or user_id_str in Development.sudo_users:
        # Ensure the command is a reply to a message
        if update.message.reply_to_message:
            new_sudo_id = str(update.message.reply_to_message.from_user.id)
            if Development.add_sudo_user(new_sudo_id):
                update.message.reply_text(f"User {new_sudo_id} has been added as a sudo user.")
            else:
                update.message.reply_text(f"User {new_sudo_id} is already a sudo user.")
        else:
            update.message.reply_text("Please reply to the user you want to add as a sudo user.")
    else:
        update.message.reply_text("You don't have permission to use this command.")

# Initialize bot and command
def main():
    updater = Updater(Development.TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handler for /addsudo
    dp.add_handler(CommandHandler("addsudo", add_sudo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
