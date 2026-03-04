"""
=================================================================
Mock Checker Template - قالب الفحص الوهمي المشترك
=================================================================
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

# ========= Config =========
BRAND_ANCHOR = '<a href="https://t.me/lgnisXBot">𝖨𝖦𝖭𝖨𝖲𝖷</a>'
DOT_ANCHOR = '<a href="https://t.me/lgnisXBot">•</a>'
BOT_LINK = f"{DOT_ANCHOR} https://t.me/lgnisXBot"

# ===========================
# النتائج الوهمية المحتملة
# ===========================

MOCK_RESPONSES = [
    ("Payment method successfully added", "𝘼𝙥𝙥𝙧𝙤𝙫𝙚𝙙 ✅", False),
    ("Insufficient Funds", "𝘾𝙑𝙑 𝙇𝙞𝙫𝙚 ✅", False),
    ("Card Issuer Declined CVV", "𝘾𝘾𝙉 ♻️", False),
    ("Do Not Honor", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("Transaction not allowed", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("Gateway Timeout", "𝙏𝙞𝙢𝙚𝙤𝙪𝙩 ⚠️", True),
    ("Network Error", "𝙉𝙚𝙩𝙬𝙤𝙧𝙠 ⚠️", True),
    ("Invalid Card Number", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("Expired Card", "𝙀𝙭𝙥𝙞𝙧𝙚𝙙 ❌", False),
    ("Lost Card", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("Stolen Card", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("Card Not Supported", "𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌", False),
    ("3D Secure Required", "𝟑𝐃𝐒 ♻️", False),
    ("Risk Declined", "𝙍𝙞𝙨𝙠 ❌", False),
]

RESPONSE_WEIGHTS = [10, 15, 12, 15, 10, 3, 2, 8, 5, 3, 3, 5, 5, 4]


# ===========================
# دوال BIN API
# ===========================

async def get_bin_info(cc: str) -> dict:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            url = f"https://bins.antipublic.cc/bins/{cc[:6]}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    bin_data = await response.json()
                    return {
                        "brand": bin_data.get('brand', 'Unknown').upper(),
                        "type": bin_data.get('type', 'Unknown').upper(),
                        "level": bin_data.get('level', 'Unknown').upper(),
                        "bank": bin_data.get('bank', 'Unknown Bank'),
                        "country": bin_data.get('country', 'Unknown'),
                        "country_flag": bin_data.get('country_flag', '🌍')
                    }
    except:
        pass
    
    return {
        "brand": "UNKNOWN", "type": "UNKNOWN", "level": "UNKNOWN",
        "bank": "Unknown Bank", "country": "Unknown", "country_flag": "🌍"
    }


# ===========================
# دالة الفحص الوهمي النهائية
# ===========================

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
    start_time = datetime.datetime.now()
    
    found_message, response_status, is_transient_error = random.choices(
        MOCK_RESPONSES, 
        weights=RESPONSE_WEIGHTS, 
        k=1
    )[0]

    bin_info = await get_bin_info(cc)
    duration_seconds = random.uniform(1.5, 3.0)
    await asyncio.sleep(duration_seconds)

    if is_transient_error:
        await refund_credit(str(user_id), 1, found_message)
        response_status = f"{response_status} (Refunded)"

    end_time = datetime.datetime.now()
    actual_duration = (end_time - start_time).total_seconds()

    response_message = (
        f"{DOT_ANCHOR} {response_status}\n"
        "\n"
        f"{DOT_ANCHOR} 𝗖𝗮𝗿𝗱 ⌁ <code>{cc}|{mes}|{ano}|{cvv}</code>\n"
        f"{DOT_ANCHOR} 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {gateway_name} {gateway_amount}\n"
        f"{DOT_ANCHOR} 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {found_message}\n"
        "\n"
        f"{DOT_ANCHOR} 𝗜𝗻𝗳𝗼 ⌁ {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
        f"{DOT_ANCHOR} 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
        f"{DOT_ANCHOR} 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}\n"
        "\n"
        f"{DOT_ANCHOR} 𝐓𝐨𝐨𝐤 ⌁ {actual_duration:.2f} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
        f"{DOT_ANCHOR} 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ {user_mention} [<code><b>{user_status}</b></code>]\n"
        f"{DOT_ANCHOR} 𝐁𝐨𝐭 ➺ {BRAND_ANCHOR}\n"
        "\n"
        f"{BOT_LINK}"
    )

    try:
        await message.bot.edit_message_text(
            text=response_message,
            chat_id=chat_id,
            message_id=message_id_to_edit,
            parse_mode="HTML"
        )
    except:
        await message.bot.send_message(chat_id, response_message, reply_to_message_id=message.message_id, parse_mode="HTML")

    if not is_transient_error:
        await update_last_chk(str(user_id))


# ===========================
# دالة المعالجة الرئيسية
# ===========================

async def handle_mock_command(
    message: types.Message, 
    gateway_name: str,
    gateway_amount: str = "$0.00"
):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"

    if not await config.can_use_b3(chat_id, user_id):
        await message.reply(f"{DOT_ANCHOR} ⛔ لا تملك الصلاحية أو يجب الانتظار 30 ثانية.\n\n{BOT_LINK}", parse_mode="HTML")
        return

    parts = message.text.split(maxsplit=1)
    command = parts[0] if parts else ""
    
    if len(parts) < 2:
        await message.reply(
            f"{DOT_ANCHOR} ❌ يرجى إدخال بيانات البطاقة\n"
            "\n"
            f"{DOT_ANCHOR} 📝 <b>الاستخدام:</b>\n"
            f"{DOT_ANCHOR} <code>{command} CC|MM|YYYY|CVV</code>\n"
            "\n"
            f"{BOT_LINK}",
            parse_mode="HTML"
        )
        return

    card_info = parts[1].replace('/', '|').strip()
    card_data = card_info.split('|')

    if len(card_data) != 4:
        await message.reply(
            f"{DOT_ANCHOR} ❌ صيغة غير صحيحة\n"
            "\n"
            f"{DOT_ANCHOR} 📝 <b>الصيغة المطلوبة:</b>\n"
            f"{DOT_ANCHOR} <code>CC|MM|YYYY|CVV</code>\n"
            "\n"
            f"{BOT_LINK}",
            parse_mode="HTML"
        )
        return

    cc, mes, ano, cvv = [x.strip() for x in card_data]
    if len(ano) == 2: ano = "20" + ano

    premium_status = await premium_util.is_premium(str(user_id))
    user_status = "Owner" if user_id == config.Admin else "Premium" if premium_status else "Free"

    await message.bot.send_chat_action(chat_id, "typing")
    response_message = await message.reply(f"{DOT_ANCHOR} 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 ...", parse_mode="HTML")
    
    await final_mock(
        response_message.message_id,
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
