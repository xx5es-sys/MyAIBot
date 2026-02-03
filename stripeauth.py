"""
بوابة Stripe Auth الوهمية
الأمر: /st
النوع: AUTH
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_auths_command(message: types.Message):
    """
    معالج الأمر /st للفحص الوهمي - Stripe Auth Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Stripe Auth",
        gateway_amount="$0.00"
    )
