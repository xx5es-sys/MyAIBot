"""
=================================================================
gate_handler.py — Universal Single Gate Handler
IGNISX Bot — Production Grade
=================================================================
هذا الملف يحتوي على الدالة الموحدة لمعالجة أوامر الفحص الفردي
لجميع البوابات الحقيقية المدمجة في النظام.

الاستخدام:
    from gate_handler import handle_real_gate_command
    await handle_real_gate_command(message, process_func, gateway_name, gateway_amount)
=================================================================
"""
import asyncio
import datetime
import logging
from typing import Callable, Awaitable

from aiogram import types

import config
import premium_util
from branding import apply_branding
from mass import get_bin_info

logger = logging.getLogger(__name__)


async def handle_real_gate_command(
    message: types.Message,
    process_func: Callable[..., Awaitable[tuple[str, str]]],
    gateway_name: str,
    gateway_amount: str = "$0.00",
) -> None:
    """
    الدالة الموحدة لمعالجة أوامر الفحص الفردي الحقيقي.

    المعاملات:
        message       : رسالة Telegram الواردة
        process_func  : دالة process_GATE_NAME من Service Module
        gateway_name  : اسم البوابة للعرض (مثل "Braintree Auth B3-1")
        gateway_amount: قيمة المعاملة للعرض (مثل "$0.00")

    التدفق:
        1. التحقق من الصلاحيات وخصم الكريدت
        2. تحليل بيانات البطاقة من الرسالة
        3. إرسال رسالة "Processing..."
        4. استدعاء process_func الحقيقية
        5. جلب BIN info
        6. تعديل الرسالة بالنتيجة النهائية
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"

    # ── 1. التحقق من الصلاحيات ──────────────────────────────────
    if not await config.can_use_b3(chat_id, user_id):
        await message.reply(
            apply_branding("⛔ لا تملك الصلاحية أو يجب الانتظار 30 ثانية (للمستخدمين المجانيين)."),
            parse_mode="HTML",
        )
        return

    # ── 2. تحليل بيانات البطاقة ─────────────────────────────────
    parts = message.text.split(maxsplit=1)
    command = parts[0] if parts else ""

    if len(parts) < 2:
        await message.reply(
            apply_branding(
                f"❌ يرجى إدخال بيانات البطاقة\n\n"
                f"📝 <b>الاستخدام:</b>\n"
                f"<code>{command} CC|MM|YYYY|CVV</code>\n\n"
                f"✅ <b>مثال:</b>\n"
                f"<code>{command} 4111111111111111|12|2025|123</code>"
            ),
            parse_mode="HTML",
        )
        return

    card_info = parts[1].replace("/", "|").strip()
    card_data = card_info.split("|")

    if len(card_data) != 4:
        await message.reply(
            apply_branding(
                f"❌ صيغة غير صحيحة\n\n"
                f"📝 <b>الصيغة المطلوبة:</b>\n"
                f"<code>CC|MM|YYYY|CVV</code>\n\n"
                f"✅ <b>مثال:</b>\n"
                f"<code>{command} 4111111111111111|12|2025|123</code>"
            ),
            parse_mode="HTML",
        )
        return

    cc, mes, ano, cvv = [x.strip() for x in card_data]

    # تحويل السنة من رقمين إلى 4 أرقام
    if len(ano) == 2:
        ano = "20" + ano

    # ── 3. تحديد حالة المستخدم ──────────────────────────────────
    premium_status = await premium_util.is_premium(str(user_id))
    if user_id == config.Admin:
        user_status = "Owner"
    elif premium_status:
        user_status = "Premium"
    else:
        user_status = "Free"

    # ── 4. إرسال رسالة Processing ───────────────────────────────
    await message.bot.send_chat_action(chat_id, "typing")
    processing_msg = await message.reply(
        apply_branding("𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 ..."),
        parse_mode="HTML",
    )
    message_id_to_edit = processing_msg.message_id

    # ── 5. استدعاء دالة الفحص الحقيقية ─────────────────────────
    start_time = datetime.datetime.now()
    try:
        result_label, result_msg = await process_func(cc, mes, ano, cvv)
    except Exception as exc:
        logger.exception("Gate %s raised an unhandled exception: %s", gateway_name, exc)
        result_label = "❌"
        result_msg = f"Internal Error: {exc}"

    end_time = datetime.datetime.now()
    actual_duration = (end_time - start_time).total_seconds()

    # ── 6. جلب BIN info ─────────────────────────────────────────
    try:
        bin_info = await get_bin_info(cc)
    except Exception:
        bin_info = {
            "brand": "UNKNOWN", "type": "UNKNOWN", "level": "UNKNOWN",
            "bank": "Unknown Bank", "country": "Unknown",
            "country_flag": "🌍", "blacklisted": False,
        }

    # ── 7. تجهيز رسالة الرد النهائية ────────────────────────────
    response_message = apply_branding(
        f"{result_label}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐚𝐫𝐝 ⇾ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ {gateway_name} {gateway_amount}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ {result_msg}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐧𝐟𝐨 ⇾ {bin_info['brand']} - {bin_info['level']} - {bin_info['type']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bin_info['bank']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {bin_info['country']} {bin_info['country_flag']}\n\n"
        f"𝐓𝐨𝐨𝐤 ⇾ {actual_duration:.2f} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
        f"𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ {user_mention} "
        f"{{<code><b>{user_status}</b></code>}}"
    )

    # ── 8. تعديل رسالة Processing بالنتيجة ──────────────────────
    try:
        await message.bot.edit_message_text(
            text=response_message,
            chat_id=chat_id,
            message_id=message_id_to_edit,
            parse_mode="HTML",
        )
    except Exception:
        await message.reply(response_message, parse_mode="HTML")

    # ── 9. تحديث last_chk ───────────────────────────────────────
    try:
        await premium_util.update_last_chk(str(user_id))
    except Exception as exc:
        logger.warning("Failed to update last_chk for user %s: %s", user_id, exc)
