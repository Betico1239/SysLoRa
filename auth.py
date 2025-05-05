import json

def load_users(filepath="users.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def authenticate_user(username, password, users_db):
    user = users_db.get(username)
    return user and user.get("password") == password

