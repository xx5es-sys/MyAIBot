"""
message_handler.py

Centralized message‐handling utilities for the bot.
Provides premium‐status checks and related helpers,
with robust logging and clear docstrings.
"""

import logging
from premium_util import is_premium as _admin_is_premium, send_premium_data as _admin_send_premium_data
from aiogram import types

# Configure module‐level logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


async def is_premium(user_id: str):
    """
    Check whether a user has active premium status.

    Args:
        user_id (str): The Telegram user ID as a string.

    Returns:
        dict or None: Returns the premium user record if active, otherwise None.
    """
    try:
        result = await _admin_is_premium(user_id)
        logger.debug(f"is_premium({user_id}) → {bool(result)}")
        return result
    except Exception as e:
        logger.error(f"Failed to check premium for user {user_id}: {e}", exc_info=True)
        # Propagate so caller can decide to fallback or abort
        raise


async def send_premium_data(message: types.Message):
    """
    Send premium account details (e.g., expiry time) to a user message.

    Args:
        message (aiogram.types.Message): Incoming message instance.

    Raises:
        Exception: Propagates any errors from the admin module.
    """
    try:
        await _admin_send_premium_data(message)
        logger.info(f"Premium data sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Failed to send premium data to {message.from_user.id}: {e}", exc_info=True)
        raise


# Optional: generic placeholder for future message‐handling utilities
async def handle_generic_message(message: types.Message):
    """
    Default catch‐all handler for incoming messages.
    Extend this to add common preprocessing (e.g., logging, filters).
    """
    logger.info(f"Received message from {message.from_user.id}: {message.text!r}")
    # Add any shared logic here, or simply pass to specific handlers
    pass
