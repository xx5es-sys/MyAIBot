"""
بوابة VBV (Verified by Visa) الوهمية
الأمر: /vbv
النوع: VBV/3DS
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_vbv_command(message: types.Message):
    """
    معالج الأمر /vbv للفحص الوهمي - VBV Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="VBV Lookup",
        gateway_amount="$0.00"
    )
