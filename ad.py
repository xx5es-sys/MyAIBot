"""
بوابة AD الوهمية
الأمر: /ad
النوع: AUTH
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_ad_command(message: types.Message):
    """
    معالج الأمر /ad للفحص الوهمي - AD Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="Adyen Auth",
        gateway_amount="$0.00"
    )
