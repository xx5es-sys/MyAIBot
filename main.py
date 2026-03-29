"""
=================================================================
𝖨𝖦𝖭𝖨𝖲𝖷 — Main Entry Point (aiogram 3.25.0 + Bot API 9.4)
=================================================================
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import LabeledPrice

from config import API_TOKEN, Admin
import config
from branding import apply_branding

# ========= Bot & Dispatcher =========

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ========= Logging =========

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========= Imports =========

from cmds import (
    handle_start as start_command,
    handle_cmds as cmds_entry,
    handle_profile as sup_command,
    on_callback_query as start_callbacks,
)
from mock_checker_template import handle_mock_command
from gen import generate_card
from proxy_ import proxycheck
from scrape import handle_scrape_command

from admin import (
    AdminActions,
    admin_commands,
    process_add_premium,
    process_duration,
    add_premium_user,
    process_add_credits,
    process_credits_amount,
    process_credits_user_id,
    process_set_unlimited,
    process_unlimited_user_id,
    remove_premium_user,
    process_remove_premium,
    view_premium_users,
    admin_router
)
from mass import mass_router
from broadcast import broadcast_router
from premium_util import check_subscriptions, add_credits, is_premium


# =================================================================
# Premium Gating Helper
# =================================================================

async def check_premium_access(message: types.Message) -> bool:
    """التحقق من صلاحية المستخدم (Premium gating)"""
    user_id = message.from_user.id
    if user_id == Admin:
        return True
    if await is_premium(str(user_id)):
        return True
    await message.reply(
        apply_branding("⛔ <b>Premium Access Required</b>\n\n"
        "هذه البوابة متاحة فقط للمستخدمين Premium.\n"
        "استخدم /buy لشراء اشتراك وفتح جميع الميزات."),
        parse_mode="HTML"
    )
    return False


# =================================================================
# المهام المجدولة
# =================================================================

async def scheduler():
    """فحص الاشتراكات المنتهية"""
    while True:
        await check_subscriptions()
        await asyncio.sleep(5)


# =================================================================
# نظام الدفع (Telegram Stars XTR)
# =================================================================

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """تأكيد الدفع قبل الإكمال"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """معالجة الدفع الناجح"""
    sp = message.successful_payment
    payload = sp.invoice_payload or ""

    print("SUCCESSFUL_PAYMENT RECEIVED:", sp)

    if payload.startswith("stars:"):
        try:
            stars = int(payload.split(":")[1])
        except ValueError:
            stars = 0

        if stars > 0:
            username = message.from_user.username or message.from_user.first_name
            await add_credits(str(message.from_user.id), stars, username)
            await message.reply(
                apply_branding(f"✅ تم استلام الدفع بنجاح!\n"
                f"⭐ تم إضافة <b>{stars}</b> نجمة إلى رصيدك.\n"
                "استخدم /sup حتى تشوف رصيدك الجديد."),
                parse_mode="HTML"
            )
        else:
            await message.reply(apply_branding("⚠️ صار خطأ بكمية النجوم، تواصل ويا الأدمن."), parse_mode="HTML")
        return

    await message.reply(
        apply_branding("تم استلام دفع، لكن الـ payload غير معروف.\n"
        "تواصل ويا الأدمن للتأكد."),
        parse_mode="HTML"
    )


# =================================================================
# أمر شراء النجوم
# =================================================================

async def send_invoice_stars(message: types.Message, stars: int):
    """إرسال فاتورة Telegram Stars"""
    if stars <= 0:
        await message.reply(apply_branding("❌ رقم غير صالح."), parse_mode="HTML")
        return

    prices = [LabeledPrice(label=f"{stars} Stars", amount=stars)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=apply_branding(f"شراء {stars} نجمة"),
        description=apply_branding(f"شراء {stars} نجمة لاستخدامها داخل 𝖨𝖦𝖭𝖨𝖲𝖷 Bot"),
        payload=f"stars:{stars}",
        provider_token="",
        currency="XTR",
        prices=prices,
    )


# =================================================================
# الأوامر الأساسية
# =================================================================

@router.message(CommandStart())
async def handle_start_cmd(message: types.Message):
    """/start"""
    await start_command(message)


@router.message(Command("cmds"))
async def handle_cmds_cmd(message: types.Message):
    """/cmds - مركز الأوامر"""
    await cmds_entry(message)


@router.message(Command("sup"))
async def handle_sup_cmd(message: types.Message):
    """/sup - MY PROFILE بدون أزرار"""
    await sup_command(message)


@router.message(Command("buy"))
async def handle_buy_command(message: types.Message):
    """/buy - شراء النجوم"""
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            apply_branding("💳 <b>Buy Stars</b>\n\n"
            "اكتب عدد النجوم بهالشكل:\n"
            "<code>/buy 10</code>\n"
            "كل 1 Star = 1 Credit ⭐"),
            parse_mode="HTML"
        )
        return
    try:
        stars = int(parts[1])
    except ValueError:
        await message.reply(apply_branding("❌ اكتب رقم صحيح، مثال: /buy 10"), parse_mode="HTML")
        return
    await send_invoice_stars(message, stars)


@router.message(Command("admin"))
async def handle_admin(message: types.Message, state: FSMContext):
    """/admin - لوحة الإدارة"""
    if message.from_user.id == Admin:
        await admin_commands(message, state)
    else:
        await message.reply(apply_branding("❌ You are not authorized to use this command."), parse_mode="HTML")


# =================================================================
# AUTH Gates (3 بوابات)
# =================================================================

@router.message(Command("au"))
async def handle_au_cmd(message: types.Message):
    """/au - Stripe Auth"""
    if not await check_premium_access(message):
        return
    from au import handle_au_command
    await handle_au_command(message)


@router.message(Command("b3", "ba"))
async def handle_ba_cmd(message: types.Message):
    """/b3, /ba - Braintree Auth"""
    if not await check_premium_access(message):
        return
    from b3 import handle_b3_command
    await handle_b3_command(message)


@router.message(Command("ad"))
async def handle_ad_cmd(message: types.Message):
    """/ad - Adyen Auth"""
    if not await check_premium_access(message):
        return
    from ad import handle_ad_command
    await handle_ad_command(message)


@router.message(Command("auth"))
async def handle_auth_cmd(message: types.Message):
    """/auth - Auth.net"""
    if not await check_premium_access(message):
        return
    from au import handle_au_command
    await handle_au_command(message)


@router.message(Command("chk"))
async def handle_chk_cmd(message: types.Message):
    """/chk - Stripe CHK"""
    if not await check_premium_access(message):
        return
    from stripe_ import handle_chk_command
    await handle_chk_command(message)


@router.message(Command("st"))
async def handle_st_cmd(message: types.Message):
    """/st - Stripe Auth"""
    if not await check_premium_access(message):
        return
    from stripeauth import handle_auths_command
    await handle_auths_command(message)


@router.message(Command("avs"))
async def handle_avs_cmd(message: types.Message):
    """/avs - AVS Check"""
    if not await check_premium_access(message):
        return
    from authavs import handle_avs_command
    await handle_avs_command(message)


@router.message(Command("out"))
async def handle_out_cmd(message: types.Message):
    """/out - Square Auth (Alias for /sq)"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Square Auth", gateway_amount="$0.00")


@router.message(Command("fo"))
async def handle_fo_cmd(message: types.Message):
    """/fo - Foundy Auth"""
    if not await check_premium_access(message):
        return
    from foundy import handle_fo_command
    await handle_fo_command(message)


@router.message(Command("sq"))
async def handle_sq_cmd(message: types.Message):
    """/sq - Square Auth"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Square Auth", gateway_amount="$0.00")


# =================================================================
# CHARGE Gates (4 بوابات)
# =================================================================

@router.message(Command("Pv", "pv"))
async def handle_pv_cmd(message: types.Message):
    """/Pv - PayPal CVV"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="PayPal CVV", gateway_amount="$1.00")


@router.message(Command("Sh", "sh"))
async def handle_sh_cmd(message: types.Message):
    """/Sh - Square Charge"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Square Charge", gateway_amount="$1.00")


@router.message(Command("az"))
async def handle_az_cmd(message: types.Message):
    """/az - Azathoth (Authorize.Net)"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Authorize.Net [AIM]", gateway_amount="$0.50")


@router.message(Command("sc"))
async def handle_sc_cmd(message: types.Message):
    """/sc - Stripe Charge"""
    if not await check_premium_access(message):
        return
    from stripe_ import handle_chk_command
    await handle_chk_command(message)


# =================================================================
# LOOKUP Gates (4 بوابات)
# =================================================================

@router.message(Command("vbv"))
async def handle_vbv_cmd(message: types.Message):
    """/vbv - Verify Secure (Braintree 3DS)"""
    if not await check_premium_access(message):
        return
    from vbv import handle_vbv_command
    await handle_vbv_command(message)


@router.message(Command("G3", "g3"))
async def handle_g3_cmd(message: types.Message):
    """/G3 - Global 3DS"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Global 3DS", gateway_amount="$0.00")


@router.message(Command("GP", "gp"))
async def handle_gp_cmd(message: types.Message):
    """/GP - Global Passed"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Global Passed", gateway_amount="$0.00")


@router.message(Command("BP", "bp"))
async def handle_bp_cmd(message: types.Message):
    """/BP - Verify Passed (Braintree Passed)"""
    if not await check_premium_access(message):
        return
    await handle_mock_command(message, gateway_name="Braintree Passed", gateway_amount="$0.00")


# =================================================================
# الأدوات
# =================================================================

@router.message(Command("gen"))
async def handle_gen_cmd(message: types.Message):
    """/gen - توليد بطاقات"""
    await generate_card(message)


@router.message(Command("ip"))
async def handle_ip_cmd(message: types.Message):
    """/ip - فحص البروكسي"""
    await proxycheck(message)


@router.message(Command("scr"))
async def handle_scr_cmd(message: types.Message):
    """/scr - سحب البطاقات"""
    await handle_scrape_command(message)


# =================================================================
# تسجيل Handlers البوت
# =================================================================

# تسجيل الكولباكات
router.callback_query.register(start_callbacks, F.data.startswith("st:"))
router.callback_query.register(start_callbacks, F.data.startswith("cmds:"))
router.callback_query.register(start_callbacks, F.data.startswith("gw:"))
router.callback_query.register(start_callbacks, F.data.startswith("tools:"))

# تسجيل أوامر الإدارة
dp.include_router(admin_router)

# تسجيل Broadcast Handler (يجب أن يكون قبل mass_router لأن mass_router يلتقط جميع الرسائل)
dp.include_router(broadcast_router)

# تسجيل Mass Handlers
dp.include_router(mass_router)

# =================================================================
# تشغيل البوت
# =================================================================

async def main():
    print("𝖨𝖦𝖭𝖨𝖲𝖷 Started! (aiogram 3.25.0 + Bot API 9.4)")
    # تشغيل المجدول في الخلفية
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
