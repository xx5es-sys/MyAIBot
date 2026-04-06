"""
=================================================================
mass_real_workers.py — Real Gate Workers for Mass Check
IGNISX Bot — Production Grade
=================================================================
هذا الملف يحتوي على:
    1. check_single_card_real() — دالة Worker الموحدة للفحص الجماعي الحقيقي
    2. REAL_GATE_MAP — خريطة تربط gate_id بدالة process_ الخاصة به

يُستدعى هذا الملف من mass.py بدلاً من check_single_card_mock()
عندما يكون gate_id مدرجاً في REAL_GATE_MAP.

منطق التكامل:
    - إذا كان gate_id موجوداً في REAL_GATE_MAP → استخدم check_single_card_real()
    - إذا لم يكن موجوداً → ارجع إلى check_single_card_mock() (Fallback)
=================================================================
"""
import asyncio
import logging
from typing import Callable, Awaitable

from aiogram import Bot

import config
from branding import apply_branding
# إزالة استيراد mass_sessions لتجنب Circular Import
from mass_utils import get_bin_info # نفترض نقل get_bin_info إلى mass_utils، أو تمرير session كمعامل
from premium_util import consume_for_single, is_premium

logger = logging.getLogger(__name__)

# =================================================================
# خريطة البوابات الحقيقية: gate_id → (process_func, gate_type)
# gate_type: "auth" | "charge" | "lookup"
# =================================================================

# ── Auth: Braintree ──────────────────────────────────────────────
from gates.Auth.B3_Auth.B3_1 import process_B3_1
from gates.Auth.B3_Auth.B3_2 import process_B3_2
from gates.Auth.B3_Auth.B3_3 import process_B3_3
from gates.Auth.B3_Auth.Single_B3 import process_B3_single

# ── Auth: Stripe ─────────────────────────────────────────────────
from gates.Auth.ST_AUTH.ST_1 import process_ST_1
from gates.Auth.ST_AUTH.ST_2 import process_ST_2
from gates.Auth.ST_AUTH.ST_single import process_ST_single

# ── Auth: Square ─────────────────────────────────────────────────
from gates.Auth.SQ_Auth.SQ_1 import process_SQ_1
from gates.Auth.SQ_Auth.SQ_2 import process_SQ_2
from gates.Auth.SQ_Auth.SQ_3 import process_SQ_3
from gates.Auth.SQ_Auth.SQ_single import process_SQ_single

# ── Charge: Authorize.Net ────────────────────────────────────────
from gates.Charge.Authorize_Net.Au_1 import process_Au_1
from gates.Charge.Authorize_Net.Au_single import process_Au_single

# ── Charge: PayPal ───────────────────────────────────────────────
from gates.Charge.PayPal.paypal_1 import process_paypal_1
from gates.Charge.PayPal.paypal_2 import process_paypal_2
from gates.Charge.PayPal.paypal_3 import process_paypal_3
from gates.Charge.PayPal.paypal_single import process_paypal_single

# ── Charge: Square ───────────────────────────────────────────────
from gates.Charge.SQ_Charge.SQ_1_charge import process_SQ_1_charge
from gates.Charge.SQ_Charge.SQ_2_charge import process_SQ_2_charge
from gates.Charge.SQ_Charge.SQ_single_charge import process_SQ_single_charge

# ── Charge: Stripe ───────────────────────────────────────────────
from gates.Charge.ST_Charge.St_1 import process_ST_1_charge
from gates.Charge.ST_Charge.ST_2_charge import process_ST_2_charge
from gates.Charge.ST_Charge.ST_3 import process_ST_3_charge
from gates.Charge.ST_Charge.ST_single_charge import process_ST_single_charge

# ── LookUp: Global 3DS ───────────────────────────────────────────
from gates.LookUp.Global_3DS.GP_1_3ds import process_GP_1 as process_GP_1_3ds
from gates.LookUp.Global_3DS.GP_2_3ds import process_GP_2 as process_GP_2_3ds
from gates.LookUp.Global_3DS.GP_single_3ds import process_GP_single as process_GP_single_3ds

# ── LookUp: Global Passed ────────────────────────────────────────
from gates.LookUp.Global_Passed.GP_1_passed import process_GP_1_passed
from gates.LookUp.Global_Passed.GP_2_passed import process_GP_2_passed
from gates.LookUp.Global_Passed.GP_single_passed import process_GP_single_passed

# ── LookUp: Verify Passed ────────────────────────────────────────
from gates.LookUp.Verify_Passed.B3_LookUp1_passed import process_B3_LookUp1_passed
from gates.LookUp.Verify_Passed.B3_LookUp2_passed import process_B3_LookUp2_passed
from gates.LookUp.Verify_Passed.B3_LookUp3_passed import process_B3_LookUp3_passed
from gates.LookUp.Verify_Passed.B3_LookUp_single_passed import process_B3_LookUp_single_passed

# ── LookUp: Verify Secure ────────────────────────────────────────
from gates.LookUp.Verify_Secure.B3_LookUp1_secure import process_B3_LookUp1_secure
from gates.LookUp.Verify_Secure.B3_LookUp2_secure import process_B3_LookUp2_secure
from gates.LookUp.Verify_Secure.B3_LookUp3_secure import process_B3_LookUp3_secure
from gates.LookUp.Verify_Secure.B3_LookUp_single_secure import process_B3_LookUp_single_secure


# =================================================================
# REAL_GATE_MAP: gate_id → (process_func, gate_type, display_name)
# =================================================================
REAL_GATE_MAP: dict[str, tuple[Callable, str, str]] = {
    # ── AUTH: Braintree ──────────────────────────────────────────
    "b31":  (process_B3_1,      "auth",   "Braintree Auth B3-1"),
    "b32":  (process_B3_2,      "auth",   "Braintree Auth B3-2"),
    "b33":  (process_B3_3,      "auth",   "Braintree Auth B3-3"),
    "b3s":  (process_B3_single, "auth",   "Braintree Auth Single"),
    # ── AUTH: Stripe ─────────────────────────────────────────────
    "st1":  (process_ST_1,      "auth",   "Stripe Auth ST-1"),
    "st2":  (process_ST_2,      "auth",   "Stripe Auth ST-2"),
    "sts":  (process_ST_single, "auth",   "Stripe Auth Single"),
    # ── AUTH: Square ─────────────────────────────────────────────
    "sq1":  (process_SQ_1,      "auth",   "Square Auth SQ-1"),
    "sq2":  (process_SQ_2,      "auth",   "Square Auth SQ-2"),
    "sq3":  (process_SQ_3,      "auth",   "Square Auth SQ-3"),
    "sqs":  (process_SQ_single, "auth",   "Square Auth Single"),
    # ── CHARGE: Authorize.Net ────────────────────────────────────
    "au1":  (process_Au_1,           "charge", "Authorize.Net AU-1"),
    "aus":  (process_Au_single,      "charge", "Authorize.Net Single"),
    # ── CHARGE: PayPal ───────────────────────────────────────────
    "pp1":  (process_paypal_1,       "charge", "PayPal CVV PP-1"),
    "pp2":  (process_paypal_2,       "charge", "PayPal CVV PP-2"),
    "pp3":  (process_paypal_3,       "charge", "PayPal CVV PP-3"),
    "pps":  (process_paypal_single,  "charge", "PayPal CVV Single"),
    # ── CHARGE: Square ───────────────────────────────────────────
    "sqc1": (process_SQ_1_charge,    "charge", "Square Charge SQ-1"),
    "sqc2": (process_SQ_2_charge,    "charge", "Square Charge SQ-2"),
    "sqcs": (process_SQ_single_charge, "charge", "Square Charge Single"),
    # ── CHARGE: Stripe ───────────────────────────────────────────
    "stc1": (process_ST_1_charge,    "charge", "Stripe Charge ST-1"),
    "stc2": (process_ST_2_charge,    "charge", "Stripe Charge ST-2"),
    "stc3": (process_ST_3_charge,    "charge", "Stripe Charge ST-3"),
    "stcs": (process_ST_single_charge, "charge", "Stripe Charge Single"),
    # ── LOOKUP: Global 3DS ───────────────────────────────────────
    "gp1":  (process_GP_1_3ds,       "lookup", "Global 3DS GP-1"),
    "gp2":  (process_GP_2_3ds,       "lookup", "Global 3DS GP-2"),
    "gps":  (process_GP_single_3ds,  "lookup", "Global 3DS Single"),
    # ── LOOKUP: Global Passed ────────────────────────────────────
    "gpp1": (process_GP_1_passed,    "lookup", "Global Passed GP-1"),
    "gpp2": (process_GP_2_passed,    "lookup", "Global Passed GP-2"),
    "gpps": (process_GP_single_passed, "lookup", "Global Passed Single"),
    # ── LOOKUP: Verify Passed ────────────────────────────────────
    "vp1":  (process_B3_LookUp1_passed,      "lookup", "Verify Passed B3-1"),
    "vp2":  (process_B3_LookUp2_passed,      "lookup", "Verify Passed B3-2"),
    "vp3":  (process_B3_LookUp3_passed,      "lookup", "Verify Passed B3-3"),
    "vps":  (process_B3_LookUp_single_passed, "lookup", "Verify Passed Single"),
    # ── LOOKUP: Verify Secure ────────────────────────────────────
    "vs1":  (process_B3_LookUp1_secure,      "lookup", "Verify Secure B3-1"),
    "vs2":  (process_B3_LookUp2_secure,      "lookup", "Verify Secure B3-2"),
    "vs3":  (process_B3_LookUp3_secure,      "lookup", "Verify Secure B3-3"),
    "vss":  (process_B3_LookUp_single_secure, "lookup", "Verify Secure Single"),
}


# =================================================================
# دوال تصنيف النتيجة حسب نوع البوابة
# =================================================================

def _classify_auth_result(result_label: str) -> tuple[str, str]:
    """
    تصنيف نتيجة بوابة AUTH.
    Returns: (display_icon, counter_key)
    counter_key: "approved" | "declined" | "ccn" | "unknown"
    """
    label_lower = result_label.lower()
    if "✅" in result_label or "auth" in label_lower:
        return "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"
    elif "♻️" in result_label or "ccn" in label_lower:
        return "𝘾𝘾𝙉 ♻️", "ccn"
    elif "❌" in result_label or "declined" in label_lower or "decline" in label_lower:
        return "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"
    else:
        return "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"


def _classify_charge_result(result_label: str) -> tuple[str, str]:
    """
    تصنيف نتيجة بوابة CHARGE.
    Returns: (display_icon, counter_key)
    counter_key: "charge" | "approved" | "declined" | "unknown"
    """
    label_lower = result_label.lower()
    if "charged" in label_lower or "💰" in result_label:
        return "𝘾𝙃𝘼𝙍𝙂𝙀 💰", "charge"
    elif "✅" in result_label or "auth" in label_lower or "live" in label_lower:
        return "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"
    elif "❌" in result_label or "declined" in label_lower or "decline" in label_lower:
        return "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"
    else:
        return "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"


def _classify_lookup_result(result_label: str) -> tuple[str, str]:
    """
    تصنيف نتيجة بوابة LOOKUP/3DS.
    Returns: (display_icon, counter_key)
    counter_key: "otp" | "passed" | "rejected" | "unknown"
    """
    label_lower = result_label.lower()
    if "otp" in label_lower or "challenge" in label_lower:
        return "𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅", "otp"
    elif "passed" in label_lower or "✅" in result_label:
        return "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "passed"
    elif "rejected" in label_lower or "❌" in result_label:
        return "𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌", "rejected"
    else:
        return "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"


def _classify_result(gate_type: str, result_label: str) -> tuple[str, str]:
    """دالة التصنيف الموحدة."""
    if gate_type == "auth":
        return _classify_auth_result(result_label)
    elif gate_type == "charge":
        return _classify_charge_result(result_label)
    else:
        return _classify_lookup_result(result_label)


# =================================================================
# دالة Worker الموحدة للفحص الجماعي الحقيقي
# =================================================================

async def check_single_card_real(
    card_data: str,
    user_id: int,
    bot: Bot,
    session: dict,
) -> bool:
    """
    Worker الحقيقي للفحص الجماعي.

    يُستدعى من mass_process_loop() في mass.py عندما يكون gate_id
    مدرجاً في REAL_GATE_MAP.

    المعاملات:
        card_data : بيانات البطاقة بصيغة "CC|MM|YYYY|CVV"
        user_id   : معرف المستخدم
        bot       : كائن Bot لإرسال الرسائل
        session   : جلسة الفحص الجماعي الخاصة بالمستخدم

    القيمة المُرجعة:
        True  → تمت المعالجة بنجاح (حتى لو كانت البطاقة مرفوضة)
        False → فشل خصم الكريدت (إيقاف الحلقة)
    """
    if not session:
        return False

    user_id_str = str(user_id)
    gate_id = session.get("gate_id", "")
    gate_entry = REAL_GATE_MAP.get(gate_id)

    if not gate_entry:
        # Fallback: هذا لا يجب أن يحدث إذا تم الاستدعاء بشكل صحيح
        logger.error("check_single_card_real called with unknown gate_id: %s", gate_id)
        return False

    process_func, gate_type, gate_display_name = gate_entry

    # ── خصم الكريدت ─────────────────────────────────────────────
    if user_id != config.Admin:
        success, msg = await consume_for_single(user_id_str)
        if not success:
            return False  # لا يوجد كريدت → إيقاف الحلقة

    # ── تحليل بيانات البطاقة ────────────────────────────────────
    normalized = card_data.replace("/", "|").strip()
    parts = normalized.split("|")
    if len(parts) != 4:
        session["processed"] += 1
        session["unknown"] += 1
        return True

    cc, mes, ano, cvv = [p.strip() for p in parts]
    if len(ano) == 2:
        ano = "20" + ano

    card_info = f"{cc}|{mes}|{ano}|{cvv}"

    # ── استدعاء دالة الفحص الحقيقية ─────────────────────────────
    try:
        result_label, result_msg = await process_func(cc, mes, ano, cvv)
    except Exception as exc:
        logger.exception("Gate %s failed for card %s: %s", gate_id, cc[:6], exc)
        result_label = "❌"
        result_msg = f"Error: {exc}"

    # ── تصنيف النتيجة وتحديث العدادات ───────────────────────────
    display_icon, counter_key = _classify_result(gate_type, result_label)
    session["processed"] += 1
    session[counter_key] += 1

    # ── إرسال رسالة Hit إذا كانت البطاقة مقبولة ─────────────────
    is_hit = counter_key in ("approved", "charge", "otp", "passed", "ccn")
    if is_hit:
        try:
            bin_info = await get_bin_info(cc)
        except Exception:
            bin_info = {
                "brand": "UNKNOWN", "type": "UNKNOWN", "level": "UNKNOWN",
                "bank": "Unknown Bank", "country": "Unknown",
                "country_flag": "🌍", "blacklisted": False,
            }

        premium_status = await is_premium(user_id_str)
        if user_id == config.Admin:
            user_status = "Owner"
        elif premium_status:
            user_status = "Premium"
        else:
            user_status = "Free"

        hit_msg = apply_branding(
            f"{display_icon}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{card_info}</code>\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {gate_display_name}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {result_msg}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐧𝐟𝐨 ⌁ {bin_info['type']} - {bin_info['level']} - {bin_info['brand']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}\n\n"
            f"𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⌁ <a href='tg://user?id={user_id}'>User</a> "
            f"{{<code><b>{user_status}</b></code>}}"
        )
        try:
            await bot.send_message(
                user_id,
                hit_msg,
                parse_mode="HTML",
                reply_to_message_id=session.get("message_id"),
            )
        except Exception as exc:
            logger.warning("Failed to send hit message to user %s: %s", user_id, exc)

    return True
