"""
blacklist_handler.py

Professional blacklist management for the bot (aiogram 3.x):
- Middleware-based enforcement of user and keyword blacklists.
- Provides utilities to load, save, add, and remove entries in `blacklist.json`.
"""
import json
import os
import logging
from typing import Set, Tuple, Callable, Dict, Any, Awaitable
from aiogram import types, BaseMiddleware

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

BLACKLIST_FILE = os.path.join(os.path.dirname(__file__), 'blacklist.json')

DEFAULT_BLACKLIST = {
    "user_ids": [],
    "keywords": []
}


def load_blacklist() -> Tuple[Set[int], Set[str]]:
    if not os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'w') as f:
                json.dump(DEFAULT_BLACKLIST, f, indent=4)
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
    payload = {
        "user_ids": sorted(list(user_ids)),
        "keywords": sorted(list(keywords))
    }
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(payload, f, indent=4)
    except OSError as e:
        logger.error(f"Failed saving blacklist: {e}")


class BlacklistMiddleware(BaseMiddleware):
    """Aiogram 3.x middleware to enforce blacklist rules."""
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        user_ids, keywords = load_blacklist()
        user_id = event.from_user.id

        if user_id in user_ids:
            try:
                await event.delete()
            except Exception:
                pass
            return

        text = event.text or ''
        for kw in keywords:
            if kw.lower() in text.lower():
                try:
                    await event.delete()
                except Exception:
                    pass
                return

        return await handler(event, data)


def add_user_to_blacklist(user_id: int) -> None:
    user_ids, keywords = load_blacklist()
    user_ids.add(user_id)
    save_blacklist(user_ids, keywords)


def remove_user_from_blacklist(user_id: int) -> None:
    user_ids, keywords = load_blacklist()
    if user_id in user_ids:
        user_ids.discard(user_id)
        save_blacklist(user_ids, keywords)


def add_keyword_to_blacklist(keyword: str) -> None:
    user_ids, keywords = load_blacklist()
    keywords.add(keyword)
    save_blacklist(user_ids, keywords)


def remove_keyword_from_blacklist(keyword: str) -> None:
    user_ids, keywords = load_blacklist()
    if keyword in keywords:
        keywords.discard(keyword)
        save_blacklist(user_ids, keywords)


__all__ = [
    'BlacklistMiddleware',
    'add_user_to_blacklist',
    'remove_user_from_blacklist',
    'add_keyword_to_blacklist',
    'remove_keyword_from_blacklist'
]
