from pymongo import MongoClient
import os


MONGO_URI = os.getenv("mongodb+srv://seizewaifubot:seizewaifubot@itachi.9qya0.mongodb.net/?retryWrites=true&w=majority&appName=itachi")
DB_NAME = os.getenv("DB_NAME", "seizewaifubot")
COLLECTION_NAME = "users"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_user_data(user_id):
    return collection.find_one({"user_id": user_id})

def save_user_data(user_id, user_data):
    collection.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)
    print("User data saved successfully.")
