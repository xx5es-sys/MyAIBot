import re
from aiogram import types, Router, F
from aiogram.types import LabeledPrice
import premium_util

buy_router = Router()

# كل check = 1 star
PRICE_PER_CHECK = 1


def extract_amount(text: str) -> int:
    nums = re.findall(r'\d+', text)
    return int(nums[0]) if nums else 0


@buy_router.message(F.text.startswith("/buy"))
async def buy_command(message: types.Message):
    amount = extract_amount(message.text)

    if amount <= 0:
        await message.answer(
            "💳 <b>Buy Stars</b>\n\n"
            "Send the number of Stars you want to buy.\n"
            "Example:\n"
            "<code>/buy 20</code>\n"
            "or simply send a number after this message ⭐",
            parse_mode="HTML"
        )
        return

    await send_invoice_stars(message, amount)


async def send_invoice_stars(message: types.Message, stars: int):
    prices = [
        LabeledPrice(
            label=f"{stars} Stars",
            amount=stars * PRICE_PER_CHECK
        )
    ]

    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Buy {stars} Stars",
        description=f"You are purchasing {stars} ⭐ Stars.",
        payload=f"stars:{stars}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
