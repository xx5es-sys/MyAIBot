"""
=================================================================
نظام الفحص الجماعي المطور - Advanced Mass Check System
(aiogram 3.25.0)
=================================================================
"""

import asyncio
import aiohttp
import ssl
import datetime
import random
import time
import io
from aiogram import types, Bot, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, InputMediaPhoto
)
import config
from premium_util import can_start_mass, consume_for_single, refund_credit, update_last_chk, is_premium

# ========= Config =========
BANNER_URL = "https://t.me/i5ese/347"
DOT_ANCHOR = '<a href="http://t.me/IgnisXBot">•</a>'

# Router خاص بالـ mass
mass_router = Router()


# =================================================================
# البوابات المتاحة للفحص الجماعي
# =================================================================

AUTH_GATES = [
    {"id": "au", "name": "Stripe Auth", "cmd": "/au"},
    {"id": "ba", "name": "Braintree Auth", "cmd": "/ba"},
    {"id": "sq", "name": "Square Auth", "cmd": "/sq"},
]

CHARGE_GATES = [
    {"id": "pv", "name": "PayPal CVV", "cmd": "/Pv"},
    {"id": "sh", "name": "Square Charge", "cmd": "/Sh"},
    {"id": "az", "name": "Azathoth", "cmd": "/az"},
    {"id": "sc", "name": "Stripe Charge", "cmd": "/sc"},
]

LOOKUP_GATES = [
    {"id": "vbv", "name": "Verify Secure", "cmd": "/vbv"},
    {"id": "g3", "name": "Global 3DS", "cmd": "/G3"},
    {"id": "gp", "name": "Global Passed", "cmd": "/GP"},
    {"id": "bp", "name": "Verify Passed", "cmd": "/BP"},
]


# =================================================================
# النتائج الوهمية المحتملة
# =================================================================

MOCK_RESPONSES_MASS = [
    ("challenge_required", "OTP REQUIRED ✅", "otp", False),
    ("authenticate_successful", "PASSED ✅", "passed", False),
    ("authenticate_attempt_successful", "PASSED ✅", "passed", False),
    ("authenticate_rejected", "REJECTED ❌", "rejected", False),
    ("authenticate_frictionless_failed", "REJECTED ❌", "rejected", False),
    ("Gateway Timeout", "UNKNOWN ❓", "unknown", True),
]

RESPONSE_WEIGHTS = [20, 15, 15, 20, 20, 10]


# =================================================================
# حالة الآلة لتتبع جلسة الفحص الجماعي
# =================================================================

class MassCheckState(StatesGroup):
    waiting_for_gate_type = State()
    waiting_for_gateway = State()
    processing = State()


# =================================================================
# قاموس لتخزين جلسات الفحص الجماعي
# =================================================================

mass_sessions = {}


# =================================================================
# دوال BIN API
# =================================================================

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


# =================================================================
# Keyboards (aiogram 3.x - inline_keyboard parameter)
# =================================================================

def kb_file_uploaded():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="AUTH", callback_data="mass:type:auth", style="success"),
            InlineKeyboardButton(text="CHARGE", callback_data="mass:type:charge", style="success")
        ],
        [InlineKeyboardButton(text="LOOKUP", callback_data="mass:type:lookup", style="success")],
        [InlineKeyboardButton(text="EXIT", callback_data="mass:cancel", style="danger")]
    ])


def kb_auth_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in AUTH_GATES]
    buttons.append([InlineKeyboardButton(text="BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="EXIT", callback_data="mass:cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_charge_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in CHARGE_GATES]
    buttons.append([InlineKeyboardButton(text="BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="EXIT", callback_data="mass:cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_lookup_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in LOOKUP_GATES]
    buttons.append([InlineKeyboardButton(text="BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="EXIT", callback_data="mass:cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_stats_keyboard(user_id: int) -> InlineKeyboardMarkup:
    session = mass_sessions.get(user_id)
    if not session:
        return InlineKeyboardMarkup(inline_keyboard=[])

    total = len(session["cards"])
    processed = session["processed"]
    progress = (processed / total * 100) if total > 0 else 0
    gate_type = session.get("gate_type", "auth")

    buttons = [
        [InlineKeyboardButton(text=f"TOTAL: [ {total} ]", callback_data="mass_info", style="primary")],
        [InlineKeyboardButton(text=f"PROGRESS: [ {progress:.2f}% ]", callback_data="mass_info", style="primary")],
    ]

    if gate_type == "auth":
        buttons.append([InlineKeyboardButton(text=f"APPROVED: [ {session.get('approved', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"DECLINED: [ {session.get('declined', 0)} ]", callback_data="mass_info", style="danger")])
        buttons.append([InlineKeyboardButton(text=f"CCN: [ {session.get('ccn', 0)} ]", callback_data="mass_info", style="danger")])
    elif gate_type == "charge":
        buttons.append([InlineKeyboardButton(text=f"CHARGE: [ {session.get('charge', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"APPROVED: [ {session.get('approved', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"DECLINED: [ {session.get('declined', 0)} ]", callback_data="mass_info", style="danger")])
    elif gate_type == "lookup":
        buttons.append([InlineKeyboardButton(text=f"OTP REQUEST: [ {session.get('otp', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"PASSED: [ {session.get('passed', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"REJECTED: [ {session.get('rejected', 0)} ]", callback_data="mass_info", style="danger")])

    buttons.append([InlineKeyboardButton(text=f"UNKNOWN: [ {session['unknown']} ]", callback_data="mass_info", style="danger")])

    if session["status"] == "processing":
        buttons.append([InlineKeyboardButton(text="STOP", callback_data="mass:stop")])
    elif session["status"] == "paused":
        buttons.append([InlineKeyboardButton(text="RESUME", callback_data="mass:resume", style="success")])
        buttons.append([InlineKeyboardButton(text="NEW FILE", callback_data="mass:new_file", style="success")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_completed():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:home", style="primary")]
    ])


# =================================================================
# Captions
# =================================================================

def cap_file_uploaded(file_name: str, total_lines: int, valid_items: int) -> str:
    return (
        f"{DOT_ANCHOR} 𝖨𝖦𝖭𝖨𝖲𝖷 — File Uploaded\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "\n"
        f"{DOT_ANCHOR} Your file has been received successfully.\n"
        "\n"
        f"{DOT_ANCHOR} File name   ⌁  {file_name}\n"
        f"{DOT_ANCHOR} Total lines ⌁  {total_lines}\n"
        f"{DOT_ANCHOR} Valid items ⌁  {valid_items}\n"
        "\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} ↯  Select Gate Type To Continue  ↯"
    )


# =================================================================
# دالة فحص بطاقة واحدة
# =================================================================

async def check_single_card_mock(card_data: str, user_id: int, bot: Bot) -> bool:
    session = mass_sessions.get(user_id)
    if not session:
        return False

    user_id_str = str(user_id)

    card_info = card_data.strip().replace('/', '|')
    parts = card_info.split('|')
    if len(parts) < 3:
        session["processed"] += 1
        session["unknown"] += 1
        return True

    cc = parts[0]

    success, msg = await consume_for_single(user_id_str)
    if not success:
        session["status"] = "paused"
        return False

    bin_info = await get_bin_info(cc)

    # محاكاة لنتائج مختلفة حسب نوع البوابة
    gate_type = session.get("gate_type", "auth")
    
    if gate_type == "auth":
        # (Status, Result, Category)
        results = [
            ("Approved ✅", "Payment method successfully added", "approved"),
            ("Declined ❌", "Your card was declined", "declined"),
            ("CCN ❌", "Card Issuer Declined CVV", "ccn"),
        ]
        status, result, category = random.choices(results, weights=[20, 60, 20], k=1)[0]
    elif gate_type == "charge":
        results = [
            ("Charged ✅", "Transaction successful", "charge"),
            ("Approved ✅", "Insufficient Funds", "approved"),
            ("Declined ❌", "Your card was declined", "declined"),
        ]
        status, result, category = random.choices(results, weights=[10, 20, 70], k=1)[0]
    else: # lookup
        status, result, category, _ = random.choices(MOCK_RESPONSES_MASS, weights=RESPONSE_WEIGHTS, k=1)[0]

    session[category] = session.get(category, 0) + 1
    session["processed"] += 1

    # إرسال نتيجة البطاقة كـ Reply على رسالة الإحصائيات أو رسالة الملف
    user_mention = f"<a href='tg://user?id={user_id}'>{session['user_name']}</a>"
    
    response_text = (
        f"{DOT_ANCHOR} {status}\n"
        "\n"
        f"{DOT_ANCHOR} 𝗖𝗮𝗿𝗱 ⌁ <code>{card_info}</code>\n"
        f"{DOT_ANCHOR} 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {session['gateway_name']}\n"
        f"{DOT_ANCHOR} 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {result}\n"
        "\n"
        f"{DOT_ANCHOR} 𝗜𝗻𝗳𝗼 ⌁ {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
        f"{DOT_ANCHOR} 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
        f"{DOT_ANCHOR} 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}\n"
        "\n"
        f"{DOT_ANCHOR} 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ {user_mention}\n"
        f"{DOT_ANCHOR} 𝐁𝐨𝐭 ➺ 𝖨𝖦𝖭𝖨𝖲𝖷"
    )

    try:
        # إرسال النتيجة كـ Reply على رسالة الـ Stats
        await bot.send_message(
            chat_id=session["chat_id"],
            text=response_text,
            reply_to_message_id=session["message_id"],
            parse_mode="HTML"
        )
    except:
        pass

    return True


# =================================================================
# Handlers
# =================================================================

@mass_router.message(F.document)
async def handle_document_upload(message: Message, state: FSMContext):
    """استلام ملف البطاقات"""
    if not message.document.file_name.endswith('.txt'):
        return

    # التحقق من الصلاحية
    can_start, msg = await can_start_mass(str(message.from_user.id))
    if not can_start:
        await message.reply(f"{DOT_ANCHOR} {msg}", parse_mode="HTML")
        return

    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    
    # تحميل الملف ومعالجته
    content = await message.bot.download_file(file_path)
    text_content = content.read().decode('utf-8', errors='ignore')
    lines = text_content.splitlines()
    
    valid_cards = []
    for line in lines:
        if len(line.strip()) > 10:
            valid_cards.append(line.strip())

    if not valid_cards:
        await message.reply(f"{DOT_ANCHOR} No valid cards found in the file.", parse_mode="HTML")
        return

    # تخزين الجلسة
    mass_sessions[message.from_user.id] = {
        "cards": valid_cards,
        "processed": 0,
        "approved": 0,
        "declined": 0,
        "ccn": 0,
        "charge": 0,
        "otp": 0,
        "passed": 0,
        "rejected": 0,
        "unknown": 0,
        "status": "waiting",
        "chat_id": message.chat.id,
        "user_name": message.from_user.first_name,
        "file_name": message.document.file_name
    }

    # تم تغيير الـ reply_photo ليكون reply على الملف
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_file_uploaded(message.document.file_name, len(lines), len(valid_cards)),
        reply_markup=kb_file_uploaded(),
        parse_mode="HTML"
    )
    await state.set_state(MassCheckState.waiting_for_gate_type)


@mass_router.callback_query(F.data.startswith("mass:"))
async def handle_mass_callbacks(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    session = mass_sessions.get(user_id)
    if not session:
        await call.answer("Session not found. Please upload the file again.")
        return

    data = call.data.split(":")

    if data[1] == "cancel":
        mass_sessions.pop(user_id, None)
        await call.message.delete()
        await state.clear()
        await call.answer("Mass check cancelled.")

    elif data[1] == "type":
        gate_type = data[2]
        session["gate_type"] = gate_type
        if gate_type == "auth":
            kb = kb_auth_gates()
        elif gate_type == "charge":
            kb = kb_charge_gates()
        else:
            kb = kb_lookup_gates()
        
        await call.message.edit_caption(
            caption=f"{DOT_ANCHOR} 𝖨𝖦𝖭𝖨𝖲𝖷 — Select Gateway\n\n{DOT_ANCHOR} Choose the gateway you want to use for mass checking.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        await state.set_state(MassCheckState.waiting_for_gateway)

    elif data[1] == "back_to_types":
        await call.message.edit_caption(
            caption=cap_file_uploaded(session["file_name"], 0, len(session["cards"])),
            reply_markup=kb_file_uploaded(),
            parse_mode="HTML"
        )
        await state.set_state(MassCheckState.waiting_for_gate_type)

    elif data[1] == "gate":
        gate_id = data[2]
        session["gateway_id"] = gate_id
        
        # البحث عن اسم البوابة
        all_gates = AUTH_GATES + CHARGE_GATES + LOOKUP_GATES
        gate_name = next((g["name"] for g in all_gates if g["id"] == gate_id), "Unknown")
        session["gateway_name"] = gate_name
        session["status"] = "processing"
        session["message_id"] = call.message.message_id
        
        await call.message.edit_caption(
            caption=f"{DOT_ANCHOR} 𝖨𝖦𝖭𝖨𝖲𝖷 — Mass Checking Started\n\n{DOT_ANCHOR} Gateway: {gate_name}\n{DOT_ANCHOR} Status: Processing...",
            reply_markup=create_stats_keyboard(user_id),
            parse_mode="HTML"
        )
        
        # بدء عملية الفحص في الخلفية
        asyncio.create_task(run_mass_check(user_id, bot))

    elif data[1] == "stop":
        session["status"] = "paused"
        await call.message.edit_reply_markup(reply_markup=create_stats_keyboard(user_id))
        await call.answer("Processing paused.")

    elif data[1] == "resume":
        session["status"] = "processing"
        await call.message.edit_reply_markup(reply_markup=create_stats_keyboard(user_id))
        asyncio.create_task(run_mass_check(user_id, bot))
        await call.answer("Processing resumed.")

    elif data[1] == "new_file":
        mass_sessions.pop(user_id, None)
        await call.message.delete()
        await state.clear()
        await call.answer("Please upload a new file.")

    await call.answer()


async def run_mass_check(user_id: int, bot: Bot):
    session = mass_sessions.get(user_id)
    if not session: return

    cards = session["cards"]
    start_index = session["processed"]

    for i in range(start_index, len(cards)):
        if session["status"] != "processing":
            break
        
        card = cards[i]
        success = await check_single_card_mock(card, user_id, bot)
        
        if not success: # رصيد منتهي
            break
            
        # تحديث لوحة الإحصائيات كل 3 بطاقات أو في النهاية
        if (i + 1) % 3 == 0 or (i + 1) == len(cards):
            try:
                await bot.edit_message_reply_markup(
                    chat_id=session["chat_id"],
                    message_id=session["message_id"],
                    reply_markup=create_stats_keyboard(user_id)
                )
            except:
                pass
        
        # تأخير بسيط بين البطاقات
        await asyncio.sleep(1.5)

    if session["processed"] >= len(cards):
        session["status"] = "completed"
        try:
            await bot.edit_message_caption(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                caption=f"{DOT_ANCHOR} 𝖨𝖦𝖭𝖨𝖲𝖷 — Mass Check Completed ✅\n\n{DOT_ANCHOR} All cards have been processed.",
                reply_markup=kb_completed(),
                parse_mode="HTML"
            )
        except:
            pass


def register_handlers(dp: Router):
    dp.include_router(mass_router)
