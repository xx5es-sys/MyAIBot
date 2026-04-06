"""
بوابة Foundy الوهمية
الأمر: /fo
النوع: AUTH
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_fo_command(message: types.Message):
    """
    معالج الأمر /fo للفحص الوهمي - Foundy Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Foundy Auth",
        gateway_amount="$0.00"
    )
