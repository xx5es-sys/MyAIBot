"""
بوابة Checkout الوهمية
الأمر: /out
النوع: CHARGE
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_out_command(message: types.Message):
    """
    معالج الأمر /out للفحص الوهمي - Checkout Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Checkout.com",
        gateway_amount="$1.00"
    )
