"""
blacklist_handler.py

Professional blacklist management for the bot:
- Intercepts every incoming message to enforce user and keyword blacklists.
- Provides utilities to load, save, add, and remove entries in `blacklist.json`.
- Robust logging and error handling for maintainability.
"""
import json
import os
import logging
from typing import Set, Tuple
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler

# Configure module-level logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Path to blacklist storage
BLACKLIST_FILE = os.path.join(os.path.dirname(__file__), 'blacklist.json')

# Default structure when file is missing or corrupted
DEFAULT_BLACKLIST = {
    "user_ids": [],  # Telegram user IDs to block
    "keywords": []   # Forbidden keywords or phrases
}


def load_blacklist() -> Tuple[Set[int], Set[str]]:
    """
    Load or initialize blacklist data from JSON file.

    Returns:
        A tuple of (user_ids_set, keywords_set).
    """
    if not os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'w') as f:
                json.dump(DEFAULT_BLACKLIST, f, indent=4)
            logger.info("Created new blacklist.json with default structure.")
        except OSError as e:
            logger.error(f"Failed creating {BLACKLIST_FILE}: {e}")
        return set(), set()

    try:
        with open(BLACKLIST_FILE, 'r') as f:
            data = json.load(f)
            user_ids = set(data.get('user_ids', []))
            keywords = set(data.get('keywords', []))
            return user_ids, keywords
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading blacklist file: {e}")
        return set(), set()


def save_blacklist(user_ids: Set[int], keywords: Set[str]) -> None:
    """
    Persist blacklist data back to JSON file.
    """
    payload = {
        "user_ids": sorted(list(user_ids)),
        "keywords": sorted(list(keywords))
    }
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(payload, f, indent=4)
        logger.info(f"Blacklist saved ({len(user_ids)} users, {len(keywords)} keywords).")
    except OSError as e:
        logger.error(f"Failed saving blacklist: {e}")


async def track_message(message: types.Message) -> None:
    """
    Aiogram handler to enforce blacklist rules:
    - Deletes messages from blacklisted user IDs.
    - Deletes messages containing forbidden keywords.
    Raises:
        CancelHandler: Stops further processing of the message.
    """
    user_ids, keywords = load_blacklist()
    user_id = message.from_user.id

    # Block blacklisted users
    if user_id in user_ids:
        try:
            await message.delete()
            logger.info(f"Deleted message from blacklisted user {user_id}.")
        except Exception as e:
            logger.error(f"Error deleting message from {user_id}: {e}")
        raise CancelHandler()

    # Block messages with forbidden keywords
    text = (message.text or '') if isinstance(message, types.Message) else ''
    for kw in keywords:
        if kw.lower() in text.lower():
            try:
                await message.delete()
                logger.info(f"Deleted message containing keyword '{kw}': {text}")
            except Exception as e:
                logger.error(f"Error deleting keyword message: {e}")
            raise CancelHandler()

    # No match: allow message
    logger.debug(f"Allowed message from {user_id}: {text}")


def add_user_to_blacklist(user_id: int) -> None:
    """Add a user ID to the blacklist."""
    user_ids, keywords = load_blacklist()
    user_ids.add(user_id)
    save_blacklist(user_ids, keywords)
    logger.info(f"Added user {user_id} to blacklist.")


def remove_user_from_blacklist(user_id: int) -> None:
    """Remove a user ID from the blacklist."""
    user_ids, keywords = load_blacklist()
    if user_id in user_ids:
        user_ids.discard(user_id)
        save_blacklist(user_ids, keywords)
        logger.info(f"Removed user {user_id} from blacklist.")


def add_keyword_to_blacklist(keyword: str) -> None:
    """Add a forbidden keyword to the blacklist."""
    user_ids, keywords = load_blacklist()
    keywords.add(keyword)
    save_blacklist(user_ids, keywords)
    logger.info(f"Added keyword '{keyword}' to blacklist.")


def remove_keyword_from_blacklist(keyword: str) -> None:
    """Remove a forbidden keyword from the blacklist."""
    user_ids, keywords = load_blacklist()
    if keyword in keywords:
        keywords.discard(keyword)
        save_blacklist(user_ids, keywords)
        logger.info(f"Removed keyword '{keyword}' from blacklist.")


__all__ = [
    'track_message',
    'add_user_to_blacklist',
    'remove_user_from_blacklist',
    'add_keyword_to_blacklist',
    'remove_keyword_from_blacklist'
]
