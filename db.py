import json
import os
import time


database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.json')


def load_db():
    try:
        with open(database_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}


def save_db(data):
    with open(database_path, 'w') as file:
        json.dump(data, file, indent=4)


def register_user(user_id, username):
    db = load_db()
    for user in db["users"]:
        if user["id"] == user_id:
            return False  # User already exists
    db["users"].append({"id": user_id, "username": username})
    save_db(db)
    return True


def check_user_registered(user_id):
    db = load_db()
    return any(user["id"] == user_id for user in db["users"])


def add_user(user_id, username):
    db = load_db()
    # تحقق من عدم وجود المستخدم
    if not any(user["id"] == user_id for user in db["users"]):
        db["users"].append({"id": user_id, "username": username, "permissions": ""})
        save_db(db)
        return True
    return False


def log_command_usage(user_id, command):
    db = load_db()
    current_time = int(time.time())
    found = False
    for usage in db.get("command_usage", []):
        if usage["user_id"] == user_id and usage["command"] == command:
            usage["last_used"] = current_time
            found = True
            break
    if not found:
        db.setdefault("command_usage", []).append({"user_id": user_id, "command": command, "last_used": current_time})
    save_db(db)
    
    
def can_use_command(user_id, command, cooldown):
    db = load_db()
    for usage in db.get("command_usage", []):
        if usage["user_id"] == user_id and usage["command"] == command:
            last_used = usage["last_used"]
            current_time = int(time.time())
            return current_time - last_used >= cooldown
    return True

blacklist = {}

def is_user_blacklisted(user_id):
    return user_id in blacklist and time.time() < blacklist[user_id]

def blacklist_user(user_id, duration):
    blacklist[user_id] = time.time() + duration

# ===========================
# BIN Blacklist Management
# ===========================

def load_bin_blacklist():
    db = load_db()
    return db.get("bin_blacklist", [])

def is_bin_blacklisted(bin_number):
    blacklist = load_bin_blacklist()
    return str(bin_number)[:6] in blacklist

def add_bin_to_blacklist(bin_number):
    db = load_db()
    bin_number = str(bin_number)[:6]
    if "bin_blacklist" not in db:
        db["bin_blacklist"] = []
    if bin_number not in db["bin_blacklist"]:
        db["bin_blacklist"].append(bin_number)
        save_db(db)
        return True
    return False

def remove_bin_from_blacklist(bin_number):
    db = load_db()
    bin_number = str(bin_number)[:6]
    if "bin_blacklist" in db and bin_number in db["bin_blacklist"]:
        db["bin_blacklist"].remove(bin_number)
        save_db(db)
        return True
    return False