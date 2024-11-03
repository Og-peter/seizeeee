from shivu import shivuu as app
from shivu import sudo_users_collection

# Function to fetch the username of a user based on their user ID
async def get_user_username(user_id):
    user = await app.get_chat(user_id)
    return user.username

# Function to add a user to the sudo users collection
async def add_to_sudo_users(user_id, username, sudo_title):
    await sudo_users_collection.update_one(
        {'id': user_id},
        {'$set': {'username': username, 'sudo_title': sudo_title}},
        upsert=True
    )

# Function to remove a user from the sudo users collection
async def remove_from_sudo_users(user_id):
    await sudo_users_collection.delete_one({"id": user_id})

# Function to check if a user is in the sudo users collection
async def is_user_sudo(user_id):
    user = await sudo_users_collection.find_one({"id": user_id})
    return bool(user)

# Function to retrieve the list of sudo users from the collection
async def fetch_sudo_users():
    sudo_users = []
    async for user in sudo_users_collection.find({}):
        user_id = user.get('id')
        username = user.get('username')
        sudo_title = user.get('sudo_title')
        if user_id and username:
            sudo_users.append({"user_id": user_id, "username": username, "sudo_title": sudo_title})
    return sudo_users
