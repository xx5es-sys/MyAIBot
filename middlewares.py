"""
middlewares.py

Professional Aiogram middlewares:
- RateLimitMiddleware: throttle user messages per second.
- LoggingMiddleware: enhanced context-based logging.
- ExceptionMiddleware: catches exceptions in handlers and logs/report them.
- MaintenanceMiddleware: block commands during maintenance mode.
"""
import asyncio
import logging
import time
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.utils.exceptions import Throttled

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
    Usage: dispatcher.setup_middleware(RateLimitMiddleware(limit=1.0))
    """
    def __init__(self, limit: float = 1.0):
        super().__init__()
        self.rate_limit = limit  # seconds between messages
        self.user_timestamps = {}

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        now = time.monotonic()
        last_time = self.user_timestamps.get(user_id, 0)
        elapsed = now - last_time
        if elapsed < self.rate_limit:
            retry_after = self.rate_limit - elapsed
            try:
                raise Throttled(rate=self.rate_limit, key=str(user_id), timeout=retry_after)
            except Throttled as t:
                logger.warning(f"User {user_id} throttled. Retry after {retry_after:.2f}s.")
                await message.reply(f"🕒 You're sending messages too fast. Please wait {retry_after:.1f} seconds.")
                raise CancelHandler()
        self.user_timestamps[user_id] = now

class ExceptionMiddleware(BaseMiddleware):
    """
    Catches all exceptions in handler processing and logs them.
    """
    async def on_post_process_update(self, update: types.Update, result, data: dict):
        # after handler executed, check for exceptions stored in data
        exception = data.get('exception')
        if exception:
            logger.error(f"Exception in handler {current_handler.get().__name__}: {exception}", exc_info=True)

    async def on_process_error(self, update: types.Update, exception: Exception):
        logger.exception(f"Unhandled exception: {exception}")
        # Optionally notify admin or implement custom reporting here

class MaintenanceMiddleware(BaseMiddleware):
    """
    Blocks or delays commands when maintenance mode is active.
    Toggle `maintenance_mode` flag externally.
    """
    maintenance_mode: bool = False

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if MaintenanceMiddleware.maintenance_mode and message.text.startswith('/'):
            logger.info(f"Maintenance mode active. Blocking command {message.text} from {message.from_user.id}")
            await message.reply("⚙️ The bot is currently under maintenance. Please try again later.")
            raise CancelHandler()

# Usage example:
# from middlewares import RateLimitMiddleware, ExceptionMiddleware, MaintenanceMiddleware
# dp.middleware.setup(RateLimitMiddleware(limit=1.0))
# dp.middleware.setup(ExceptionMiddleware())
# dp.middleware.setup(MaintenanceMiddleware())
