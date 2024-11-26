from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

class Development:
    # Define all the required configurations here
    api_id = 29098103
    api_hash = "06baef4020832888ccf3ebf4e746d52b"
    TOKEN = "7335799800:AAEv5-TnLwwOhQZj2CKWPjHwR4PBJyZ2OH0"  # Replace with your actual bot token
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
    sudo_users = [
        "6402009857", "7004889403", "1135445089", "5158013355", "5630057244", 
        "1374057577", "6305653111", "5421067814", "7497950160", "7334126640", 
        "6835013483", "1993290981", "1742711103", "6180567980"
    ]
    JOINLOGS = -1002104939708
    LEAVELOGS = -1002104939708

    # User Roles
    GRADE4 = []
    GRADE3 = ["7334126640"]
    GRADE2 = ["6305653111", "5421067814"]
    GRADE1 = ["7004889403", "1374057577", "5158013355", "5630057244", "7334126640", "5421067814"]
    SPECIALGRADE = ["6402009857", "1993290981"]
    # Additional user roles
    Genin = []
    Chunin = []
    Jonin = ["7334126640"]
    Hokage = ["5421067814"]
    Akatsuki = ["6402009857", "5158013355", "5630057244"]
    Princess = ["1993290981"]
    
    # Method to add a sudo user
    @classmethod
    def add_sudo_user(cls, user_id: str):
        if user_id not in cls.sudo_users:
            cls.sudo_users.append(user_id)
            return True
        return False

    # Method to remove a sudo user
    @classmethod
    def remove_sudo_user(cls, user_id: str):
        if user_id in cls.sudo_users:
            cls.sudo_users.remove(user_id)
            return True
        return False

    # Method to get all sudo users
    @classmethod
    def get_sudo_users(cls):
        return cls.sudo_users

# Command to add a new sudo user
def add_sudo(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    # Only the owner and existing sudo users can add others as sudo
    if user_id == Development.OWNER_ID or user_id in Development.sudo_users:
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

# Command to remove a sudo user
def remove_sudo(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    # Only the owner and existing sudo users can remove others as sudo
    if user_id == Development.OWNER_ID or user_id in Development.sudo_users:
        if update.message.reply_to_message:
            sudo_id_to_remove = str(update.message.reply_to_message.from_user.id)
            if Development.remove_sudo_user(sudo_id_to_remove):
                update.message.reply_text(f"User {sudo_id_to_remove} has been removed from sudo users.")
            else:
                update.message.reply_text(f"User {sudo_id_to_remove} is not a sudo user.")
        else:
            update.message.reply_text("Please reply to the user you want to remove as a sudo user.")
    else:
        update.message.reply_text("You don't have permission to use this command.")

# Command to list all sudo users
def list_sudo(update: Update, context: CallbackContext):
    sudo_users = Development.get_sudo_users()
    if sudo_users:
        message = "List of Sudo Users:\n" + "\n".join(f"- {user_id}" for user_id in sudo_users)
    else:
        message = "There are no sudo users."
    update.message.reply_text(message)

# Initialize bot and command handlers
def main():
    updater = Updater(Development.TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("addsudo", add_sudo))
    dp.add_handler(CommandHandler("removesudo", remove_sudo))
    dp.add_handler(CommandHandler("listsudo", list_sudo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
