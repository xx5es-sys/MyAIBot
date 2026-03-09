"""
بوابة Stripe CHK الوهمية
الأمر: /chk
النوع: CHARGE
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_chk_command(message: types.Message):
    """
    معالج الأمر /chk للفحص الوهمي - Stripe CHK Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Stripe Charge",
        gateway_amount="$1.00"
    )
