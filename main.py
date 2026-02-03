"""
=================================================================
O.T Bot - Main Entry Point (Updated UI/UX Spec)
=================================================================
بوت تيليجرام لفحص البطاقات مع نظام كريدت واشتراكات

البوابات المتاحة:
AUTH:
- /au   - Stripe Auth
- /ba   - Braintree Auth
- /sq   - Square Auth

CHARGE:
- /Pv   - PayPal Cvv
- /Sh   - Square Charge
- /az   - Azathoth (Authorize.Net)
- /sc   - Stripe Charge

LOOKUP:
- /vbv  - Verify Secure (Braintree 3DS)
- /G3   - Global 3DS
- /GP   - Global Passed
- /BP   - Verify Passed (Braintree Passed)

الأدوات:
- /gen  - توليد بطاقات
- /bin  - فحص BIN
- /mgen - توليد متعدد

الفحص الجماعي:
- أرسل ملف .txt مباشرة (لا يوجد أمر /mass)

أوامر أخرى:
- /start - شاشة البداية
- /cmds  - مركز الأوامر الرئيسي
- /sup   - عرض حالة الاشتراك (MY PROFILE)
- /buy   - شراء كريدت
"""

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, ContentType
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
import asyncio
import json
from datetime import datetime

# =================================================================
# الإعدادات والاستيرادات
# =================================================================

from config import API_TOKEN, Admin

from cmds import start_command, cmds_entry, cmds_callbacks, start_callbacks, sup_command

from middlewares import RateLimitMiddleware
from blacklist_handler import track_message

# استيراد البوابات
from b3 import handle_b3_command
from vbv import handle_vbv_command
from ad import handle_ad_command
from au import handle_au_command
from stripe_ import handle_chk_command
from stripeauth import handle_auths_command
from authavs import handle_avs_command
from checkout import handle_out_command
from foundy import handle_fo_command

# استيراد الأدوات
from proxy_ import proxycheck
from gen import generate_card
from scrape import handle_scrape_command

# استيراد الفحص الجماعي
from mass import register_handlers as register_mass_handlers

# استيراد الإدارة
from admin import (
    admin_commands, add_premium_user, process_remove_premium, AdminActions,
    process_add_premium, remove_premium_user, view_premium_users, process_duration,
    process_add_credits, process_credits_amount, process_credits_user_id,
    process_set_unlimited, process_unlimited_user_id
)
from premium_util import check_subscriptions, send_premium_data, add_credits, is_premium


# =================================================================
# تهيئة البوت
# =================================================================

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
dp.middleware.setup(RateLimitMiddleware())


# =================================================================
# المهام المجدولة
# =================================================================

async def scheduler():
    """فحص الاشتراكات المنتهية"""
    while True:
        await check_subscriptions()
        await asyncio.sleep(5)

loop = asyncio.get_event_loop()
loop.create_task(scheduler())


# =================================================================
# نظام الدفع (Telegram Stars XTR)
# =================================================================

@dp.pre_checkout_query_handler(lambda q: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """تأكيد الدفع قبل الإكمال"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    """معالجة الدفع الناجح"""
    sp = message.successful_payment
    payload = sp.invoice_payload or ""

    print("SUCCESSFUL_PAYMENT RECEIVED:", sp.to_python())

    if payload.startswith("stars:"):
        try:
            stars = int(payload.split(":")[1])
        except ValueError:
            stars = 0

        if stars > 0:
            username = message.from_user.username or message.from_user.first_name
            await add_credits(str(message.from_user.id), stars, username)
            await message.answer(
                f"✅ تم استلام الدفع بنجاح!\n"
                f"⭐ تم إضافة <b>{stars}</b> نجمة إلى رصيدك.\n"
                "استخدم /sup حتى تشوف رصيدك الجديد.",
                parse_mode="HTML"
            )
        else:
            await message.answer("⚠️ صار خطأ بكمية النجوم، تواصل ويا الأدمن.")
        return

    await message.answer(
        "تم استلام دفع، لكن الـ payload غير معروف 🤔.\n"
        "تواصل ويا الأدمن للتأكد."
    )


# =================================================================
# أمر شراء النجوم
# =================================================================

async def send_invoice_stars(message: types.Message, stars: int):
    """إرسال فاتورة Telegram Stars"""
    if stars <= 0:
        await message.reply("❌ رقم غير صالح.")
        return

    prices = [LabeledPrice(label=f"{stars} Stars", amount=stars)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"شراء {stars} نجمة",
        description=f"شراء {stars} نجمة لاستخدامها داخل O.T Bot",
        payload=f"stars:{stars}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="buy-stars"
    )


@dp.message_handler(commands=['buy'])
async def handle_buy_command(message: types.Message):
    """/buy - شراء النجوم"""
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "💳 <b>Buy Stars</b>\n\n"
            "اكتب عدد النجوم بهالشكل:\n"
            "<code>/buy 10</code>\n"
            "كل 1 Star = 1 Credit ⭐",
            parse_mode="HTML"
        )
        return

    try:
        stars = int(parts[1])
    except ValueError:
        await message.reply("❌ اكتب رقم صحيح، مثال: /buy 10")
        return

    await send_invoice_stars(message, stars)


# =================================================================
# تسجيل الأوامر الأساسية
# =================================================================

# /start
dp.register_message_handler(start_command, commands=['start'])

# /cmds فقط - حذف الأوامر الأخرى (help, menu, command, commands)
dp.register_message_handler(cmds_entry, commands=['cmds'])

# /sup - عرض MY PROFILE
dp.register_message_handler(sup_command, commands=['sup'])


# =================================================================
# أوامر الإدارة
# =================================================================

@dp.message_handler(commands=['admin'], state="*")
async def admin_entry(message: types.Message, state: FSMContext):
    """دخول لوحة الإدارة"""
    if message.from_user.id == Admin:
        await admin_commands(message, state)
    else:
        await message.reply("❌ You are not authorized to use this command.")

dp.register_callback_query_handler(process_add_premium, lambda c: c.data == 'add_premium', state=AdminActions.authorized)
dp.register_callback_query_handler(remove_premium_user, lambda c: c.data == 'remove_premium', state=AdminActions.authorized)
dp.register_callback_query_handler(view_premium_users, lambda c: c.data == 'view_premium', state=AdminActions.authorized)
dp.register_message_handler(process_duration, state=AdminActions.waiting_for_duration)
dp.register_message_handler(add_premium_user, content_types=types.ContentTypes.TEXT, state=AdminActions.waiting_for_user_id)
dp.register_message_handler(process_remove_premium, content_types=types.ContentTypes.TEXT, state=AdminActions.waiting_for_user_id_remove)


# =================================================================
# Premium Gating Helper
# =================================================================

async def check_premium_access(message: types.Message) -> bool:
    """
    التحقق من صلاحية المستخدم للبوابات Premium
    إذا كان FREE يُرفض ويُوجه إلى /buy
    """
    user_id = message.from_user.id
    
    # Admin always allowed
    if user_id == Admin:
        return True
    
    # Check premium status
    if await is_premium(str(user_id)):
        return True
    
    # FREE user - deny access
    await message.reply(
        "⛔ <b>Premium Access Required</b>\n\n"
        "هذه البوابة متاحة فقط للمستخدمين Premium.\n"
        "استخدم /buy لشراء اشتراك وفتح جميع الميزات.",
        parse_mode="HTML"
    )
    return False


# =================================================================
# AUTH Gates (3 بوابات)
# =================================================================

@dp.message_handler(commands=['au'])
async def handle_au_cmd(message: types.Message):
    """/au - Stripe Auth"""
    if not await check_premium_access(message):
        return
    await handle_au_command(message)


@dp.message_handler(commands=['ba'])
async def handle_ba_cmd(message: types.Message):
    """/ba - Braintree Auth"""
    if not await check_premium_access(message):
        return
    await handle_b3_command(message)


@dp.message_handler(commands=['sq'])
async def handle_sq_cmd(message: types.Message):
    """/sq - Square Auth"""
    if not await check_premium_access(message):
        return
    # استخدام نفس القالب مع اسم مختلف
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Square Auth", gateway_amount="$0.00")


# =================================================================
# CHARGE Gates (4 بوابات)
# =================================================================

@dp.message_handler(commands=['Pv', 'pv'])
async def handle_pv_cmd(message: types.Message):
    """/Pv - PayPal Cvv"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="PayPal CVV", gateway_amount="$0.00")


@dp.message_handler(commands=['Sh', 'sh'])
async def handle_sh_cmd(message: types.Message):
    """/Sh - Square Charge"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Square Charge", gateway_amount="$1.00")


@dp.message_handler(commands=['az'])
async def handle_az_cmd(message: types.Message):
    """/az - Azathoth (Authorize.Net)"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Authorize.Net [AIM]", gateway_amount="$0.50")


@dp.message_handler(commands=['sc'])
async def handle_sc_cmd(message: types.Message):
    """/sc - Stripe Charge"""
    if not await check_premium_access(message):
        return
    await handle_chk_command(message)


# =================================================================
# LOOKUP Gates (4 بوابات)
# =================================================================

@dp.message_handler(commands=['vbv'])
async def handle_vbv_cmd(message: types.Message):
    """/vbv - Verify Secure (Braintree 3DS)"""
    if not await check_premium_access(message):
        return
    await handle_vbv_command(message)


@dp.message_handler(commands=['G3', 'g3'])
async def handle_g3_cmd(message: types.Message):
    """/G3 - Global 3DS"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Global 3DS", gateway_amount="$0.00")


@dp.message_handler(commands=['GP', 'gp'])
async def handle_gp_cmd(message: types.Message):
    """/GP - Global Passed"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Global Passed", gateway_amount="$0.00")


@dp.message_handler(commands=['BP', 'bp'])
async def handle_bp_cmd(message: types.Message):
    """/BP - Verify Passed (Braintree Passed)"""
    if not await check_premium_access(message):
        return
    from mock_checker_template import handle_mock_command
    await handle_mock_command(message, gateway_name="Braintree Passed", gateway_amount="$0.00")


# =================================================================
# الأدوات
# =================================================================

@dp.message_handler(commands=['gen'])
async def handle_gen_command(message: types.Message):
    """/gen - توليد بطاقات"""
    await generate_card(message)


@dp.message_handler(commands=['ip'])
async def handle_ip_cmd(message: types.Message):
    """/ip - فحص البروكسي"""
    await proxycheck(message)


# =================================================================
# Callbacks
# =================================================================

dp.register_callback_query_handler(
    cmds_callbacks,
    lambda c: c.data and (c.data.startswith("cmds:") or c.data.startswith("gw:") or c.data.startswith("tools:"))
)
dp.register_callback_query_handler(
    start_callbacks,
    lambda c: c.data and c.data.startswith("st:")
)


# =================================================================
# نقطة الدخول
# =================================================================

if __name__ == '__main__':
    # تسجيل الفحص الجماعي
    register_mass_handlers(dp)
    
    # تسجيل معالجات الإدارة
    dp.register_callback_query_handler(process_add_credits, lambda c: c.data == 'add_credits', state=AdminActions.authorized)
    dp.register_message_handler(process_credits_amount, state=AdminActions.waiting_for_credits_amount)
    dp.register_message_handler(process_credits_user_id, state=AdminActions.waiting_for_credits_user_id)
    dp.register_callback_query_handler(process_set_unlimited, lambda c: c.data == 'set_unlimited', state=AdminActions.authorized)
    dp.register_message_handler(process_unlimited_user_id, state=AdminActions.waiting_for_unlimited_user_id)

    print("=" * 50)
    print("O.T Bot Started!")
    print("=" * 50)
    print("\nAUTH Gates:")
    print("  /au  - Stripe Auth")
    print("  /ba  - Braintree Auth")
    print("  /sq  - Square Auth")
    print("\nCHARGE Gates:")
    print("  /Pv  - PayPal CVV")
    print("  /Sh  - Square Charge")
    print("  /az  - Azathoth (Authorize.Net)")
    print("  /sc  - Stripe Charge")
    print("\nLOOKUP Gates:")
    print("  /vbv - Verify Secure")
    print("  /G3  - Global 3DS")
    print("  /GP  - Global Passed")
    print("  /BP  - Verify Passed")
    print("\nTools:")
    print("  /gen - Generate cards")
    print("  /sup - Subscription status (MY PROFILE)")
    print("  /buy - Buy credits")
    print("\nMass Check:")
    print("  Send .txt file directly")
    print("=" * 50)

    executor.start_polling(dp, skip_updates=True)
