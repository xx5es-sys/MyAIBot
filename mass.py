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
import re
from aiogram import types, Bot, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, InputMediaPhoto
)
import config
from premium_util import can_start_mass, consume_for_single, refund_credit, update_last_chk, is_premium
from branding import apply_branding

# Banner ثابت
BANNER_URL = "https://t.me/i5ese/347"

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
    ("challenge_required", "𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅", "otp", False),
    ("authenticate_successful", "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "passed", False),
    ("authenticate_attempt_successful", "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "passed", False),
    ("authenticate_rejected", "𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌", "rejected", False),
    ("authenticate_frictionless_failed", "𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌", "rejected", False),
    ("Gateway Timeout", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown", True),
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
            InlineKeyboardButton(text="AUTH", callback_data="mass:type:auth", style="primary"),
            InlineKeyboardButton(text="CHARGE", callback_data="mass:type:charge", style="primary")
        ],
        [InlineKeyboardButton(text="LOOKUP", callback_data="mass:type:lookup", style="primary")],
        [InlineKeyboardButton(text="CANCEL", callback_data="mass:cancel", style="danger")]
    ])


def kb_auth_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in AUTH_GATES]
    buttons.append([InlineKeyboardButton(text="⬅️ BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="CANCEL", callback_data="mass:cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_charge_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in CHARGE_GATES]
    buttons.append([InlineKeyboardButton(text="⬅️ BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="CANCEL", callback_data="mass:cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_lookup_gates():
    buttons = [[InlineKeyboardButton(text=g["name"], callback_data=f"mass:gate:{g['id']}", style="success")] for g in LOOKUP_GATES]
    buttons.append([InlineKeyboardButton(text="⬅️ BACK", callback_data="mass:back_to_types", style="primary")])
    buttons.append([InlineKeyboardButton(text="CANCEL", callback_data="mass:cancel", style="danger")])
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
        [InlineKeyboardButton(text=f"𝙏𝙊𝙏𝘼𝙇 🌪️: [ {total} ]", callback_data="mass_info", style="primary")],
        [InlineKeyboardButton(text=f"𝙋𝙍𝙊𝙂𝙍𝙀𝙎𝙎 🥷🏻: [ {progress:.2f}% ]", callback_data="mass_info", style="primary")]
    ]

    # New Category Logic
    if gate_type == "auth":
        buttons.append([InlineKeyboardButton(text=f"𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅: [ {session.get('approved', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌: [ {session.get('declined', 0)} ]", callback_data="mass_info", style="danger")])
        buttons.append([InlineKeyboardButton(text=f"𝘾𝘾𝙉 ♻️: [ {session.get('ccn', 0)} ]", callback_data="mass_info", style="success")])
    elif gate_type == "charge":
        buttons.append([InlineKeyboardButton(text=f"𝘾𝙃𝘼𝙍𝙂𝙀 💰: [ {session.get('charge', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅: [ {session.get('approved', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌: [ {session.get('declined', 0)} ]", callback_data="mass_info", style="danger")])
    else: # lookup / 3ds
        buttons.append([InlineKeyboardButton(text=f"𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅: [ {session.get('otp', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"𝙋𝘼𝙎𝙎𝙀𝘿 ✅: [ {session.get('passed', 0)} ]", callback_data="mass_info", style="success")])
        buttons.append([InlineKeyboardButton(text=f"𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌: [ {session.get('rejected', 0)} ]", callback_data="mass_info", style="danger")])

    buttons.append([InlineKeyboardButton(text=f"𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓: [ {session.get('unknown', 0)} ]", callback_data="mass_info", style="primary")])

    if session["status"] == "processing":
        # STOP button must be without style
        buttons.append([InlineKeyboardButton(text="[ STOP ]", callback_data="mass:stop")])
    elif session["status"] == "paused":
        buttons.append([InlineKeyboardButton(text="𝙍𝙀𝙎𝙐𝙈𝙀 🪢", callback_data="mass:resume", style="success")])
        buttons.append([InlineKeyboardButton(text="𝙉𝙀𝙒 𝙁𝙄𝙇𝙀 🪐", callback_data="mass:new_file", style="primary")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_completed():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


# =================================================================
# Captions
# =================================================================

def cap_file_uploaded(file_name: str, total_lines: int, valid_items: int) -> str:
    return apply_branding(
        "𝖨𝖦𝖭𝖨𝖲𝖷 Bot — File Uploaded\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n\n"
        "Your file has been received successfully.\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> File name   ⌁  {file_name}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Total lines ⌁  {total_lines}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Valid items ⌁  {valid_items}\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "↯  Select Gate Type To Continue  ↯"
    )


# =================================================================
# دالة فحص بطاقة واحدة
# =================================================================

async def check_single_card_mock(card_data: str, user_id: int, bot: Bot) -> bool:
    session = mass_sessions.get(user_id)
    if not session:
        return False

    user_id_str = str(user_id)
    gate_type = session.get("gate_type", "auth")

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

    # Determine mock response based on gate type
    if gate_type == "auth":
        # AUTH: APPROVED, DECLINED, CCN
        status_code, response_text, category = random.choice([
            ("Approved", "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"),
            ("Declined", "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"),
            ("CCN", "𝘾𝘾𝙉 ♻️", "ccn"),
            ("Unknown", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown")
        ])
    elif gate_type == "charge":
        # CHARGE: CHARGE, APPROVED, DECLINED
        status_code, response_text, category = random.choice([
            ("Charged", "𝘾𝙃𝘼𝙍𝙂𝙀 💰", "charge"),
            ("Approved", "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"),
            ("Declined", "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"),
            ("Unknown", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown")
        ])
    else:
        # 3DS: OTP REQUEST, PASSED, REJECTED
        status_code, response_text, category = random.choice([
            ("OTP Required", "𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅", "otp"),
            ("Passed", "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "passed"),
            ("Rejected", "𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌", "rejected"),
            ("Unknown", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown")
        ])

    await asyncio.sleep(random.uniform(0.5, 1.5))

    session["processed"] += 1
    session[category] = session.get(category, 0) + 1

    if category in ["otp", "passed", "approved", "charge", "ccn"]:
        gateway_name = session.get("gateway_name", "Unknown")
        text = apply_branding(
            f"{response_text}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{card_data}</code>\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {gateway_name}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {status_code}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗜𝗻𝗳𝗼 ⌁ {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}"
        )
        try:
            await bot.send_message(
                session["chat_id"], 
                text, 
                parse_mode="HTML",
                reply_to_message_id=session.get("message_id")
            )
        except:
            pass

    return True


# =================================================================
# Handlers (aiogram 3.x - Router + decorators)
# =================================================================

@mass_router.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    """معالج رفع الملفات .txt"""
    user_id = message.from_user.id

    if not message.document:
        return

    file_name = message.document.file_name
    if not file_name.endswith('.txt'):
        return

    # Check permission
    if not await can_start_mass(str(user_id)):
        await message.reply(apply_branding("❌ Your subscription does not allow mass check."), parse_mode="HTML")
        return

    file_id = message.document.file_id
    bot = message.bot
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    downloaded_file = await bot.download_file(file_path)
    content = downloaded_file.read().decode('utf-8', errors='ignore')
    
    lines = content.splitlines()
    cards = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if re.search(r'\d{15,16}', line):
            cards.append(line)

    if not cards:
        await message.reply(apply_branding("❌ No valid cards found in the file."), parse_mode="HTML")
        return

    mass_sessions[user_id] = {
        "cards": cards,
        "processed": 0,
        "approved": 0,
        "declined": 0,
        "ccn": 0,
        "charge": 0,
        "passed": 0,
        "rejected": 0,
        "otp": 0,
        "unknown": 0,
        "status": "waiting",
        "chat_id": message.chat.id,
        "message_id": None,
        "gateway_id": None,
        "gateway_name": None,
        "gate_type": None
    }

    await state.set_state(MassCheckState.waiting_for_gate_type)
    msg = await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_file_uploaded(file_name, len(lines), len(cards)),
        reply_markup=kb_file_uploaded(),
        parse_mode="HTML"
    )
    mass_sessions[user_id]["message_id"] = msg.message_id


@mass_router.callback_query(F.data.startswith("mass:type:"))
async def select_gate_type(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id not in mass_sessions:
        await call.answer("Session expired. Please upload the file again.")
        return

    gate_type = call.data.split(":")[2]
    mass_sessions[user_id]["gate_type"] = gate_type
    
    if gate_type == "auth":
        kb = kb_auth_gates()
    elif gate_type == "charge":
        kb = kb_charge_gates()
    else:
        kb = kb_lookup_gates()

    await call.message.edit_caption(
        caption=apply_branding("み 𝖨𝖦𝖭𝖨𝖲𝖷 Bot — Select Gateway\n\nSelect the gateway to start mass check."),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(MassCheckState.waiting_for_gateway)
    await call.answer()


@mass_router.callback_query(F.data == "mass:back_to_types")
async def back_to_types(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id not in mass_sessions:
        await call.answer()
        return

    await call.message.edit_caption(
        caption=apply_branding("𝖨𝖦𝖭𝖨𝖲𝖷 Bot — File Uploaded\n\nSelect Gate Type To Continue"),
        reply_markup=kb_file_uploaded(),
        parse_mode="HTML"
    )
    await state.set_state(MassCheckState.waiting_for_gate_type)
    await call.answer()


@mass_router.callback_query(F.data.startswith("mass:gate:"))
async def start_mass_check(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id not in mass_sessions:
        await call.answer()
        return

    gate_id = call.data.split(":")[2]
    
    # Find gate name
    all_gates = AUTH_GATES + CHARGE_GATES + LOOKUP_GATES
    gate_name = next((g["name"] for g in all_gates if g["id"] == gate_id), "Unknown")

    session = mass_sessions[user_id]
    session["gateway_id"] = gate_id
    session["gateway_name"] = gate_name
    session["status"] = "processing"

    await call.message.edit_caption(
        caption=apply_branding(f"み 𝖨𝖦𝖭𝖨𝖲𝖷 Bot — Processing\n\nGate: {gate_name}\nStarting the process..."),
        reply_markup=create_stats_keyboard(user_id),
        parse_mode="HTML"
    )
    
    await state.set_state(MassCheckState.processing)
    await call.answer(f"Started checking with {gate_name}")

    # Start processing loop
    asyncio.create_task(mass_process_loop(user_id, call.message.bot))


async def mass_process_loop(user_id: int, bot: Bot):
    session = mass_sessions.get(user_id)
    if not session: return

    cards = session["cards"]
    
    while session["processed"] < len(cards) and session["status"] == "processing":
        card = cards[session["processed"]]
        
        success = await check_single_card_mock(card, user_id, bot)
        if not success:
            break
        
        if session["processed"] % 5 == 0 or session["processed"] == len(cards):
            try:
                await bot.edit_message_reply_markup(
                    chat_id=session["chat_id"],
                    message_id=session["message_id"],
                    reply_markup=create_stats_keyboard(user_id)
                )
            except:
                pass
        
        await asyncio.sleep(0.1)

    if session["processed"] >= len(cards):
        session["status"] = "completed"
        try:
            await bot.edit_message_caption(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                caption=apply_branding("✅ <b>Mass Check Completed!</b>\n\nAll cards have been processed."),
                reply_markup=kb_completed(),
                parse_mode="HTML"
            )
        except:
            pass


@mass_router.callback_query(F.data == "mass:stop")
async def stop_mass(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in mass_sessions:
        mass_sessions[user_id]["status"] = "paused"
        await call.message.edit_reply_markup(reply_markup=create_stats_keyboard(user_id))
        await call.answer("Stopped.")


@mass_router.callback_query(F.data == "mass:resume")
async def resume_mass(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in mass_sessions:
        mass_sessions[user_id]["status"] = "processing"
        await call.message.edit_reply_markup(reply_markup=create_stats_keyboard(user_id))
        asyncio.create_task(mass_process_loop(user_id, call.message.bot))
        await call.answer("Resumed.")


@mass_router.callback_query(F.data == "mass:new_file")
async def new_file_mass(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id in mass_sessions:
        del mass_sessions[user_id]
    
    await call.message.reply(apply_branding("Send the new .txt file now."), parse_mode="HTML")
    await call.answer()


@mass_router.callback_query(F.data == "mass:cancel")
async def cancel_mass(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id in mass_sessions:
        del mass_sessions[user_id]
    
    await state.clear()
    await call.message.delete()
    await call.answer("Cancelled.")


def register_handlers(dp):
    dp.include_router(mass_router)
