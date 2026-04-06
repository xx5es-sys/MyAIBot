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

# ── Real Gate Handlers (المرحلة 3) ──────────────────────────────────────────
from handlers_gates import (
    handle_b31_command, handle_b32_command, handle_b33_command, handle_b3s_command,
    handle_st1_command, handle_st2_command, handle_sts_command,
    handle_sq1_command, handle_sq2_command, handle_sq3_command, handle_sqs_command,
    handle_au1_command, handle_aus_command,
    handle_pp1_command, handle_pp2_command, handle_pp3_command, handle_pps_command,
    handle_sqc1_command, handle_sqc2_command, handle_sqcs_command,
    handle_stc1_command, handle_stc2_command, handle_stc3_command, handle_stcs_command,
    handle_gp1_command, handle_gp2_command, handle_gps_command,
    handle_gpp1_command, handle_gpp2_command, handle_gpps_command,
    handle_vp1_command, handle_vp2_command, handle_vp3_command, handle_vps_command,
    handle_vs1_command, handle_vs2_command, handle_vs3_command, handle_vss_command,
)


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
# AUTH Gates — Braintree Real (b31/b32/b33/b3s)
# =================================================================

@router.message(Command("b31"))
async def handle_b31_cmd(message: types.Message):
    """/b31 - Braintree Auth B3-1"""
    if not await check_premium_access(message):
        return
    await handle_b31_command(message)


@router.message(Command("b32"))
async def handle_b32_cmd(message: types.Message):
    """/b32 - Braintree Auth B3-2"""
    if not await check_premium_access(message):
        return
    await handle_b32_command(message)


@router.message(Command("b33"))
async def handle_b33_cmd(message: types.Message):
    """/b33 - Braintree Auth B3-3"""
    if not await check_premium_access(message):
        return
    await handle_b33_command(message)


@router.message(Command("b3s"))
async def handle_b3s_cmd(message: types.Message):
    """/b3s - Braintree Auth Single"""
    if not await check_premium_access(message):
        return
    await handle_b3s_command(message)


# =================================================================
# AUTH Gates — Stripe Real (st1/st2/sts)
# =================================================================

@router.message(Command("st1"))
async def handle_st1_cmd(message: types.Message):
    """/st1 - Stripe Auth ST-1"""
    if not await check_premium_access(message):
        return
    await handle_st1_command(message)


@router.message(Command("st2"))
async def handle_st2_cmd(message: types.Message):
    """/st2 - Stripe Auth ST-2"""
    if not await check_premium_access(message):
        return
    await handle_st2_command(message)


@router.message(Command("sts"))
async def handle_sts_cmd(message: types.Message):
    """/sts - Stripe Auth Single"""
    if not await check_premium_access(message):
        return
    await handle_sts_command(message)


# =================================================================
# AUTH Gates — Square Real (sq1/sq2/sq3/sqs)
# =================================================================

@router.message(Command("sq1"))
async def handle_sq1_cmd(message: types.Message):
    """/sq1 - Square Auth SQ-1"""
    if not await check_premium_access(message):
        return
    await handle_sq1_command(message)


@router.message(Command("sq2"))
async def handle_sq2_cmd(message: types.Message):
    """/sq2 - Square Auth SQ-2"""
    if not await check_premium_access(message):
        return
    await handle_sq2_command(message)


@router.message(Command("sq3"))
async def handle_sq3_cmd(message: types.Message):
    """/sq3 - Square Auth SQ-3"""
    if not await check_premium_access(message):
        return
    await handle_sq3_command(message)


@router.message(Command("sqs"))
async def handle_sqs_cmd(message: types.Message):
    """/sqs - Square Auth Single"""
    if not await check_premium_access(message):
        return
    await handle_sqs_command(message)


# =================================================================
# CHARGE Gates — Authorize.Net Real (au1/aus)
# =================================================================

@router.message(Command("au1"))
async def handle_au1_cmd(message: types.Message):
    """/au1 - Authorize.Net Charge AU-1"""
    if not await check_premium_access(message):
        return
    await handle_au1_command(message)


@router.message(Command("aus"))
async def handle_aus_cmd(message: types.Message):
    """/aus - Authorize.Net Charge Single"""
    if not await check_premium_access(message):
        return
    await handle_aus_command(message)


# =================================================================
# CHARGE Gates — PayPal Real (pp1/pp2/pp3/pps)
# =================================================================

@router.message(Command("pp1"))
async def handle_pp1_cmd(message: types.Message):
    """/pp1 - PayPal Charge PP-1"""
    if not await check_premium_access(message):
        return
    await handle_pp1_command(message)


@router.message(Command("pp2"))
async def handle_pp2_cmd(message: types.Message):
    """/pp2 - PayPal Charge PP-2"""
    if not await check_premium_access(message):
        return
    await handle_pp2_command(message)


@router.message(Command("pp3"))
async def handle_pp3_cmd(message: types.Message):
    """/pp3 - PayPal Charge PP-3"""
    if not await check_premium_access(message):
        return
    await handle_pp3_command(message)


@router.message(Command("pps"))
async def handle_pps_cmd(message: types.Message):
    """/pps - PayPal Charge Single"""
    if not await check_premium_access(message):
        return
    await handle_pps_command(message)


# =================================================================
# CHARGE Gates — Square Real (sqc1/sqc2/sqcs)
# =================================================================

@router.message(Command("sqc1"))
async def handle_sqc1_cmd(message: types.Message):
    """/sqc1 - Square Charge SQ-1"""
    if not await check_premium_access(message):
        return
    await handle_sqc1_command(message)


@router.message(Command("sqc2"))
async def handle_sqc2_cmd(message: types.Message):
    """/sqc2 - Square Charge SQ-2"""
    if not await check_premium_access(message):
        return
    await handle_sqc2_command(message)


@router.message(Command("sqcs"))
async def handle_sqcs_cmd(message: types.Message):
    """/sqcs - Square Charge Single"""
    if not await check_premium_access(message):
        return
    await handle_sqcs_command(message)


# =================================================================
# CHARGE Gates — Stripe Real (stc1/stc2/stc3/stcs)
# =================================================================

@router.message(Command("stc1"))
async def handle_stc1_cmd(message: types.Message):
    """/stc1 - Stripe Charge ST-1"""
    if not await check_premium_access(message):
        return
    await handle_stc1_command(message)


@router.message(Command("stc2"))
async def handle_stc2_cmd(message: types.Message):
    """/stc2 - Stripe Charge ST-2"""
    if not await check_premium_access(message):
        return
    await handle_stc2_command(message)


@router.message(Command("stc3"))
async def handle_stc3_cmd(message: types.Message):
    """/stc3 - Stripe Charge ST-3"""
    if not await check_premium_access(message):
        return
    await handle_stc3_command(message)


@router.message(Command("stcs"))
async def handle_stcs_cmd(message: types.Message):
    """/stcs - Stripe Charge Single"""
    if not await check_premium_access(message):
        return
    await handle_stcs_command(message)


# =================================================================
# LOOKUP Gates — Global 3DS Real (gp1/gp2/gps)
# =================================================================

@router.message(Command("gp1"))
async def handle_gp1_cmd(message: types.Message):
    """/gp1 - Global 3DS GP-1"""
    if not await check_premium_access(message):
        return
    await handle_gp1_command(message)


@router.message(Command("gp2"))
async def handle_gp2_cmd(message: types.Message):
    """/gp2 - Global 3DS GP-2"""
    if not await check_premium_access(message):
        return
    await handle_gp2_command(message)


@router.message(Command("gps"))
async def handle_gps_cmd(message: types.Message):
    """/gps - Global 3DS Single"""
    if not await check_premium_access(message):
        return
    await handle_gps_command(message)


# =================================================================
# LOOKUP Gates — Global Passed Real (gpp1/gpp2/gpps)
# =================================================================

@router.message(Command("gpp1"))
async def handle_gpp1_cmd(message: types.Message):
    """/gpp1 - Global Passed GP-1"""
    if not await check_premium_access(message):
        return
    await handle_gpp1_command(message)


@router.message(Command("gpp2"))
async def handle_gpp2_cmd(message: types.Message):
    """/gpp2 - Global Passed GP-2"""
    if not await check_premium_access(message):
        return
    await handle_gpp2_command(message)


@router.message(Command("gpps"))
async def handle_gpps_cmd(message: types.Message):
    """/gpps - Global Passed Single"""
    if not await check_premium_access(message):
        return
    await handle_gpps_command(message)


# =================================================================
# LOOKUP Gates — Verify Passed Real (vp1/vp2/vp3/vps)
# =================================================================

@router.message(Command("vp1"))
async def handle_vp1_cmd(message: types.Message):
    """/vp1 - Verify Passed B3-1"""
    if not await check_premium_access(message):
        return
    await handle_vp1_command(message)


@router.message(Command("vp2"))
async def handle_vp2_cmd(message: types.Message):
    """/vp2 - Verify Passed B3-2"""
    if not await check_premium_access(message):
        return
    await handle_vp2_command(message)


@router.message(Command("vp3"))
async def handle_vp3_cmd(message: types.Message):
    """/vp3 - Verify Passed B3-3"""
    if not await check_premium_access(message):
        return
    await handle_vp3_command(message)


@router.message(Command("vps"))
async def handle_vps_cmd(message: types.Message):
    """/vps - Verify Passed Single"""
    if not await check_premium_access(message):
        return
    await handle_vps_command(message)


# =================================================================
# LOOKUP Gates — Verify Secure Real (vs1/vs2/vs3/vss)
# =================================================================

@router.message(Command("vs1"))
async def handle_vs1_cmd(message: types.Message):
    """/vs1 - Verify Secure B3-1"""
    if not await check_premium_access(message):
        return
    await handle_vs1_command(message)


@router.message(Command("vs2"))
async def handle_vs2_cmd(message: types.Message):
    """/vs2 - Verify Secure B3-2"""
    if not await check_premium_access(message):
        return
    await handle_vs2_command(message)


@router.message(Command("vs3"))
async def handle_vs3_cmd(message: types.Message):
    """/vs3 - Verify Secure B3-3"""
    if not await check_premium_access(message):
        return
    await handle_vs3_command(message)


@router.message(Command("vss"))
async def handle_vss_cmd(message: types.Message):
    """/vss - Verify Secure Single"""
    if not await check_premium_access(message):
        return
    await handle_vss_command(message)


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
