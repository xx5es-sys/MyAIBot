"""
=================================================================
Mock Checker Template - قالب الفحص الوهمي المشترك
=================================================================
هذا القالب يُستخدم من جميع البوابات الوهمية
يوفر تدفق 1:1 مطابق للبوابات الحقيقية مع نتائج عشوائية

الميزات:
- معلومات BIN حقيقية من API خارجي
- نتائج عشوائية بأوزان واقعية
- دعم نظام الكريدت والصلاحيات
- تنسيق احترافي للنتائج
"""

import datetime
import random
import asyncio
import aiohttp
import ssl
from aiogram import types
from aiogram.types import Message
import config
import premium_util
from premium_util import refund_credit, update_last_chk
from branding import apply_branding


# =================================================================
# النتائج الوهمية المحتملة مع أوزانها
# =================================================================

MOCK_RESPONSES = [
    # (رسالة الاستجابة, الحالة, هل يحتاج Refund)
    ("Payment method successfully added", "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅", False),
    ("Insufficient Funds", "𝐂𝐕𝐕 𝐋𝐢𝐯𝐞 ✅", False),
    ("Card Issuer Declined CVV", "𝐂𝐂𝐍 ♻️", False),
    ("Do Not Honor", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("Transaction not allowed", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("Gateway Timeout", "𝐓𝐢𝐦𝐞𝐨𝐮𝐭 ⚠️", True),
    ("Network Error", "𝐍𝐞𝐭𝐰𝐨𝐫𝐤 ⚠️", True),
    ("Invalid Card Number", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("Expired Card", "𝐄𝐱𝐩𝐢𝐫𝐞𝐝 ❌", False),
    ("Lost Card", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("Stolen Card", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("Card Not Supported", "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌", False),
    ("3D Secure Required", "𝟑𝐃𝐒 ♻️", False),
    ("Risk Declined", "𝐑𝐢𝐬𝐤 ❌", False),
]

# أوزان النتائج (لتحديد احتمالية كل نتيجة)
RESPONSE_WEIGHTS = [10, 15, 12, 15, 10, 3, 2, 8, 5, 3, 3, 5, 5, 4]


# =================================================================
# دوال BIN API
# =================================================================

async def fetch_bin_details(session, cc: str) -> dict:
    """
    الحصول على معلومات BIN الحقيقية من API
    """
    try:
        url = "https://api.voidex.dev/api/bin"
        params = {"bin": cc[:6]}
        
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Error fetching BIN details: {str(e)}")
    return None


async def get_bin_info(cc: str) -> dict:
    """
    الحصول على معلومات BIN مع معالجة الأخطاء
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            bin_details = await fetch_bin_details(session, cc)
            
            if bin_details:
                return {
                    "brand": bin_details.get('brand', 'Unknown').upper(),
                    "type": bin_details.get('type', 'Unknown').upper(),
                    "level": bin_details.get('level', 'Unknown').upper(),
                    "bank": bin_details.get('bank', 'Unknown Bank'),
                    "country": bin_details.get('country_name', 'Unknown'),
                    "country_flag": bin_details.get('country_flag', '🌍')
                }
    except Exception as e:
        print(f"Error in get_bin_info: {e}")
    
    # بيانات افتراضية في حالة الفشل
    return {
        "brand": "UNKNOWN",
        "type": "UNKNOWN",
        "level": "UNKNOWN",
        "bank": "Unknown Bank",
        "country": "Unknown",
        "country_flag": "🌍"
    }


# =================================================================
# دالة الفحص الوهمي النهائية
# =================================================================

async def final_mock(
    message_id_to_edit: int,
    chat_id: int,
    message: Message,
    user_id: int,
    cc: str,
    mes: str,
    ano: str,
    cvv: str,
    user_status: str,
    user_mention: str,
    gateway_name: str,
    gateway_amount: str = "$0.00"
):
    """
    دالة الفحص الوهمي النهائية
    تُرجع نتيجة عشوائية مع معلومات BIN حقيقية
    """
    start_time = datetime.datetime.now()
    
    # 1) اختيار نتيجة عشوائية بناءً على الأوزان
    found_message, response_status, is_transient_error = random.choices(
        MOCK_RESPONSES, 
        weights=RESPONSE_WEIGHTS, 
        k=1
    )[0]

    # 2) الحصول على معلومات BIN الحقيقية
    bin_info = await get_bin_info(cc)

    # 3) زمن استجابة وهمي (1.5 - 4 ثواني)
    duration_seconds = random.uniform(1.5, 4.0)
    await asyncio.sleep(duration_seconds)

    # 4) إذا خطأ مؤقت → رجّع الكريدت
    if is_transient_error:
        await refund_credit(str(user_id), 1, found_message)
        response_status = f"{response_status} (Refunded)"

    # 5) حساب الوقت الفعلي
    end_time = datetime.datetime.now()
    actual_duration = (end_time - start_time).total_seconds()

    # 6) تجهيز رسالة الرد
    response_message = apply_branding(
        f"{response_status}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐚𝐫𝐝 ⇾ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ {gateway_name} {gateway_amount}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ {found_message}\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐧𝐟𝐨 ⇾ {bin_info['brand']} - {bin_info['level']} - {bin_info['type']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bin_info['bank']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {bin_info['country']} {bin_info['country_flag']}\n\n"
        f"𝐓𝐨𝐨𝐤 ⇾ {actual_duration:.2f} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
        f"𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ {user_mention} "
        f"{{<code><b>{user_status}</b></code>}}"
    )

    # 7) تعديل رسالة Processing بالنتيجة النهائية
    try:
        await message.bot.edit_message_text(
            text=response_message,
            chat_id=chat_id,
            message_id=message_id_to_edit,
            parse_mode="HTML"
        )
    except Exception:
        # إذا فشل التعديل، أرسل رسالة جديدة كـ Reply
        await message.reply(
            response_message,
            parse_mode="HTML"
        )

    # 8) تحديث last_chk إذا مو خطأ مؤقت
    if not is_transient_error:
        try:
            await update_last_chk(str(user_id))
        except Exception as e:
            print(f"[last_chk] Error updating last check for {user_id}: {e}")


# =================================================================
# دالة المعالجة الرئيسية
# =================================================================

async def handle_mock_command(
    message: types.Message, 
    gateway_name: str,
    gateway_amount: str = "$0.00"
):
    """
    الدالة الرئيسية لمعالجة أوامر الفحص الوهمي
    
    التدفق 1:1:
    1. التحقق من الصلاحيات
    2. تحليل بيانات البطاقة
    3. إرسال "Processing..."
    4. تأخير وهمي + جلب BIN
    5. تعديل الرسالة بالنتيجة
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"

    # 1. التحقق من الصلاحيات وخصم الكريدت
    if not await config.can_use_b3(chat_id, user_id):
        await message.reply(apply_branding("⛔ لا تملك الصلاحية أو يجب الانتظار 30 ثانية (للمستخدمين المجانيين)."), parse_mode="HTML")
        return

    # 2. استخراج بيانات البطاقة من الرسالة
    parts = message.text.split(maxsplit=1)
    command = parts[0] if parts else ""
    
    if len(parts) < 2:
        await message.reply(
            apply_branding(f"❌ يرجى إدخال بيانات البطاقة\n\n"
            f"📝 **الاستخدام:**\n"
            f"`{command} CC|MM|YYYY|CVV`\n\n"
            f"✅ **مثال:**\n"
            f"`{command} 4111111111111111|12|2025|123`"),
            parse_mode="HTML"
        )
        return

    # 3. تحليل بيانات البطاقة
    card_info = parts[1].replace('/', '|').strip()
    card_data = card_info.split('|')

    if len(card_data) != 4:
        await message.reply(
            apply_branding(f"❌ صيغة غير صحيحة\n\n"
            f"📝 **الصيغة المطلوبة:**\n"
            f"`CC|MM|YYYY|CVV`\n\n"
            f"✅ **مثال:**\n"
            f"`{command} 4111111111111111|12|2025|123`"),
            parse_mode="HTML"
        )
        return

    cc, mes, ano, cvv = [x.strip() for x in card_data]

    # تحويل السنة من رقمين إلى 4 أرقام
    if len(ano) == 2:
        ano = "20" + ano

    # 4. تحديد حالة المستخدم
    premium_status = await premium_util.is_premium(str(user_id))
    if user_id == config.Admin:
        user_status = "Owner"
    elif premium_status:
        user_status = "Premium"
    else:
        user_status = "Free"

    # 5. إرسال رسالة "Processing..."
    await message.bot.send_chat_action(chat_id, "typing")
    response_message = await message.reply(apply_branding("𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 ..."), parse_mode="HTML")
    message_id_to_edit = response_message.message_id

    # 6. استدعاء دالة الفحص الوهمي
    await final_mock(
        message_id_to_edit,
        chat_id,
        message,
        user_id,
        cc,
        mes,
        ano,
        cvv,
        user_status,
        user_mention,
        gateway_name,
        gateway_amount
    )
