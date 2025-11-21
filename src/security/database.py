import json
import os
from typing import List, Optional, Dict
from . import schemas

# Define the path to the database file
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_FILE = os.path.join(DATA_DIR, 'users.json')

# In-memory cache for the database
_users_db: Dict[str, Dict] = {}

def _load_db():
    """Loads the user database from the JSON file into memory."""
    global _users_db
    if not os.path.exists(DATABASE_FILE):
        _users_db = {}
        _save_db()
        return

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        try:
            _users_db = json.load(f)
        except json.JSONDecodeError:
            _users_db = {}

def _save_db():
    """Saves the in-memory user database to the JSON file."""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(_users_db, f, indent=4)

def get_user(username: str) -> Optional[schemas.UserInDB]:
    """Retrieves a user from the database by username."""
    user_data = _users_db.get(username)
    if user_data:
        return schemas.UserInDB(**user_data)
    return None

def create_user(user: schemas.UserInDB) -> schemas.UserInDB:
    """Adds a new user to the database."""
    _users_db[user.username] = user.dict()
    _save_db()
    return user

# Load the database on module import
_load_db()
