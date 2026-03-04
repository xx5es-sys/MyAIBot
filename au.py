"""
بوابة Auth الوهمية
الأمر: /auth
النوع: AUTH
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_au_command(message: types.Message):
    """
    معالج الأمر /auth للفحص الوهمي - Auth Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Auth.net",
        gateway_amount="$0.00"
    )
