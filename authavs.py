"""
بوابة AVS الوهمية
الأمر: /avs
النوع: AVS Check
"""

from aiogram import types
from mock_checker_template import handle_mock_command


async def handle_avs_command(message: types.Message):
    """
    معالج الأمر /avs للفحص الوهمي - AVS Gateway
    """
    await handle_mock_command(
        message, 
        gateway_name="AVS Check",
        gateway_amount="$0.00"
    )
