"""
middlewares.py

Professional Aiogram 3.x middlewares:
- RateLimitMiddleware: throttle user messages per second.
- ExceptionMiddleware: catches exceptions in handlers and logs them.
- MaintenanceMiddleware: block commands during maintenance mode.
"""
import logging
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types

# Configure module-level logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RateLimitMiddleware(BaseMiddleware):
    """
    Limits messages per user to a maximum rate.
    Usage: router.message.middleware(RateLimitMiddleware(limit=1.0))
    """
    def __init__(self, limit: float = 1.0):
        self.rate_limit = limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.monotonic()
        last_time = self.user_timestamps.get(user_id, 0)
        elapsed = now - last_time

        if elapsed < self.rate_limit:
            retry_after = self.rate_limit - elapsed
            logger.warning(f"User {user_id} throttled. Retry after {retry_after:.2f}s.")
            await event.reply(f"🕒 You're sending messages too fast. Please wait {retry_after:.1f} seconds.")
            return  # Cancel handler

        self.user_timestamps[user_id] = now
        return await handler(event, data)


class ExceptionMiddleware(BaseMiddleware):
    """
    Catches all exceptions in handler processing and logs them.
    """
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            return None


class MaintenanceMiddleware(BaseMiddleware):
    """
    Blocks or delays commands when maintenance mode is active.
    Toggle `maintenance_mode` flag externally.
    """
    maintenance_mode: bool = False

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        if MaintenanceMiddleware.maintenance_mode and event.text and event.text.startswith('/'):
            logger.info(f"Maintenance mode active. Blocking command {event.text} from {event.from_user.id}")
            await event.reply("⚙️ The bot is currently under maintenance. Please try again later.")
            return  # Cancel handler

        return await handler(event, data)


# Usage example (aiogram 3.x):
# from middlewares import RateLimitMiddleware, ExceptionMiddleware, MaintenanceMiddleware
# dp.message.middleware(RateLimitMiddleware(limit=1.0))
# dp.message.middleware(ExceptionMiddleware())
# dp.message.middleware(MaintenanceMiddleware())
