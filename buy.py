import re
from aiogram import types
from aiogram.types import LabeledPrice
from loader import dp, bot  # إذا ما عندك loader.py غيّرها إلى import من main
import premium_util


# كل check = 1 star
PRICE_PER_CHECK = 1


def extract_amount(text: str) -> int:
    """ استخراج العدد من /buy أو الرسالة التالية """
    nums = re.findall(r'\d+', text)
    return int(nums[0]) if nums else 0


@dp.message_handler(commands=["buy"])
async def buy_command(message: types.Message):
    """
    يدعم:
    /buy -> يطلب العدد
    /buy 20 -> يتجه مباشرة للدفع
    """
    amount = extract_amount(message.text)

    if amount <= 0:
        await message.answer(
            "💳 <b>Buy Stars</b>\n\n"
            "Send the number of Stars you want to buy.\n"
            "Example:\n"
            "<code>/buy 20</code>\n"
            "or simply send a number after this message ⭐"
        )
        return

    await send_invoice_stars(message, amount)


@dp.message_handler(lambda m: m.text.isdigit())
async def buy_amount_after(message: types.Message):
    """
    إذا المستخدم كتب رقم بعد /buy
    """
    amount = int(message.text)
    if amount <= 0:
        return await message.answer("❌ Invalid number.")

    await send_invoice_stars(message, amount)


async def send_invoice_stars(message: types.Message, stars: int):
    """
    إرسال فاتورة Telegram Stars
    """
    prices = [
        LabeledPrice(
            label=f"{stars} Stars",
            amount=stars * PRICE_PER_CHECK  # كل نجمة = 1 Star = 1 XTR
        )
    ]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Buy {stars} Stars",
        description=f"You are purchasing {stars} ⭐ Stars.",
        payload=f"stars:{stars}",
        provider_token="",       # مهم: فارغ للدفع بالنجوم ⚠️
        currency="XTR",          # Telegram Stars
        prices=prices
    )
