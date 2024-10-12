class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "6402009857"
    sudo_users = ["6402009857", "7004889403", "1135445089", "5158013355", "5630057244", "1374057577", "6305653111", "5421067814", "7497950160", "7334126640", "6835013483", "1993290981", "1742711103"]
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
    SPECIALGRADE = ["6402009857","1993290981"]

    Genin = []
    Chunin = []
    Jonin = ["7334126640"]
    Hokage = ["5421067814"]
    Akatsuki = ["6402009857", "5158013355" , "5630057244"]
    Princess = ["1993290981"]
    
class Production(Config):
    LOGGER = True

class Development(Config):
    LOGGER = True
