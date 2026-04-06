"""
بوابة Braintree الوهمية
الأمر: /b3
النوع: AUTH
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_b3_command(message: types.Message):
    """
    معالج الأمر /b3 للفحص الوهمي - Braintree Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Braintree",
        gateway_amount="$0.00"
    )
