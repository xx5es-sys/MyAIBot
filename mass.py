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
from mass_utils import create_mass_keyboard

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
    bin_number = cc[:6]
    
    # Check if BIN is blacklisted
    from db import is_bin_blacklisted
    if is_bin_blacklisted(bin_number):
        return {"blacklisted": True, "bin": bin_number}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            url = f"https://bins.antipublic.cc/bins/{bin_number}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    bin_data = await response.json()
                    return {
                        "brand": bin_data.get('brand', 'Unknown').upper(),
                        "type": bin_data.get('type', 'Unknown').upper(),
                        "level": bin_data.get('level', 'Unknown').upper(),
                        "bank": bin_data.get('bank', 'Unknown Bank'),
                        "country": bin_data.get('country', 'Unknown'),
                        "country_flag": bin_data.get('country_flag', '🌍'),
                        "blacklisted": False
                    }
    except:
        pass

    return {
        "brand": "UNKNOWN", "type": "UNKNOWN", "level": "UNKNOWN",
        "bank": "Unknown Bank", "country": "Unknown", "country_flag": "🌍",
        "blacklisted": False
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


def kb_completed():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


# =================================================================
# Captions
# =================================================================

def cap_file_uploaded(file_name: str, total_lines: int, valid_items: int) -> str:
    return apply_branding(
        "<a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — File Uploaded\n"
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
    if bin_info.get("blacklisted"):
        session["processed"] += 1
        session["bind"] = session.get("bind", 0) + 1
        return True

    # Determine mock response based on gate type
    if gate_type == "auth":
        res_list = [
            ("Authorised", "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"),
            ("Insufficient Funds", "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"),
            ("Refused", "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"),
            ("CVC Declined", "𝘾𝘾𝙉 ♻️", "ccn"),
            ("Gateway Timeout", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"),
        ]
        weights = [15, 15, 40, 20, 10]
    elif gate_type == "charge":
        res_list = [
            ("Succeeded", "𝘾𝙃𝘼𝙍𝙂𝙀 💰", "charge"),
            ("Authorised", "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "approved"),
            ("Refused", "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌", "declined"),
            ("Gateway Timeout", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"),
        ]
        weights = [10, 20, 60, 10]
    else: # lookup / 3ds
        res_list = [
            ("challenge_required", "𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅", "otp"),
            ("authenticate_successful", "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "passed"),
            ("authenticate_rejected", "𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌", "rejected"),
            ("Gateway Timeout", "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓", "unknown"),
        ]
        weights = [30, 30, 30, 10]

    chosen = random.choices(res_list, weights=weights, k=1)[0]
    raw_res, display_res, counter_key = chosen

    session["processed"] += 1
    session[counter_key] += 1

    if display_res in ["𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅", "𝘾𝙃𝘼𝙍𝙂𝙀 💰", "𝙋𝘼𝙎𝙎𝙀𝘿 ✅", "𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅", "𝘾𝘾𝙉 ♻️"]:
        # Send live result to user
        premium_status = await is_premium(user_id_str)
        user_status = "Premium" if premium_status else "Free"
        if user_id == config.Admin: user_status = "Owner"
        
        hit_msg = apply_branding(
            f"{display_res}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{card_info}</code>\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {session['gate_name']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {raw_res}\n\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐧𝐟𝐨 ⌁ {bin_info['type']} - {bin_info['level']} - {bin_info['brand']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
            f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}\n\n"
            f"𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⌁ <a href='tg://user?id={user_id}'>User</a> {{<code><b>{user_status}</b></code>}}"
        )
        try:
            await bot.send_message(user_id, hit_msg, parse_mode="HTML", reply_to_message_id=session["message_id"])
        except:
            pass

    return True


# =================================================================
# حلقة المعالجة الرئيسية
# =================================================================

async def mass_process_loop(user_id: int, bot: Bot):
    session = mass_sessions.get(user_id)
    if not session:
        return

    while session["processed"] < len(session["cards"]):
        if session["status"] != "processing":
            break

        current_card = session["cards"][session["processed"]]
        
        # Check card
        success = await check_single_card_mock(current_card, user_id, bot)
        if not success: # Out of credits
            session["status"] = "paused"
            msg = apply_branding("⚠️ <b>Paused:</b> Out of credits or error.")
            await bot.edit_message_caption(
                chat_id=user_id,
                message_id=session["dashboard_id"],
                caption=msg,
                reply_markup=create_mass_keyboard(user_id, session),
                parse_mode="HTML"
            )
            break

        # Update dashboard every 5 cards or at the end
        if session["processed"] % 5 == 0 or session["processed"] == len(session["cards"]):
            try:
                await bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=session["dashboard_id"],
                    reply_markup=create_mass_keyboard(user_id, session)
                )
            except:
                pass
        
        await asyncio.sleep(0.5)

    if session["processed"] >= len(session["cards"]):
        session["status"] = "completed"
        msg = apply_branding("✅ <b>Mass Check Completed!</b>")
        try:
            await bot.edit_message_caption(
                chat_id=user_id,
                message_id=session["dashboard_id"],
                caption=msg,
                reply_markup=kb_completed(),
                parse_mode="HTML"
            )
        except:
            pass
        if user_id in mass_sessions:
            del mass_sessions[user_id]


# =================================================================
# Handlers
# =================================================================

@mass_router.message(F.document)
async def handle_document_upload(message: Message, state: FSMContext):
    if not await can_start_mass(str(message.from_user.id)):
        await message.reply(apply_branding("❌ You need credits to start a mass check."), parse_mode="HTML")
        return

    document = message.document
    if not document.file_name.endswith('.txt'):
        return

    file_info = await message.bot.get_file(document.file_id)
    file_content = await message.bot.download_file(file_info.file_path)
    
    text = file_content.read().decode('utf-8', errors='ignore')
    lines = text.splitlines()
    
    # Simple CC regex
    cards = []
    for line in lines:
        match = re.search(r'\d{15,16}[|/]\d{2}[|/]\d{2,4}[|/]\d{3,4}', line)
        if match:
            cards.append(match.group(0))

    if not cards:
        await message.reply(apply_branding("❌ No valid cards found in the file."), parse_mode="HTML")
        return

    user_id = message.from_user.id
    mass_sessions[user_id] = {
        "cards": cards,
        "processed": 0,
        "approved": 0,
        "declined": 0,
        "ccn": 0,
        "charge": 0,
        "otp": 0,
        "passed": 0,
        "rejected": 0,
        "unknown": 0,
        "status": "setup",
        "message_id": message.message_id
    }

    sent = await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_file_uploaded(document.file_name, len(lines), len(cards)),
        reply_markup=kb_file_uploaded(),
        parse_mode="HTML"
    )
    mass_sessions[user_id]["dashboard_id"] = sent.message_id
    await state.set_state(MassCheckState.waiting_for_gate_type)


@mass_router.callback_query(F.data.startswith("mass:"))
async def handle_mass_callbacks(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data.split(":")
    action = data[1]

    if user_id not in mass_sessions and action != "cancel":
        await callback.answer("Session expired.", show_alert=True)
        return

    session = mass_sessions.get(user_id)

    if action == "type":
        gate_type = data[2]
        session["gate_type"] = gate_type
        if gate_type == "auth": kb = kb_auth_gates()
        elif gate_type == "charge": kb = kb_charge_gates()
        else: kb = kb_lookup_gates()
        
        await callback.message.edit_caption(
            caption=apply_branding(f"<b>Select {gate_type.upper()} Gateway:</b>"),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await state.set_state(MassCheckState.waiting_for_gateway)

    elif action == "gate":
        gate_id = data[2]
        gate_name = "Unknown"
        for g in AUTH_GATES + CHARGE_GATES + LOOKUP_GATES:
            if g["id"] == gate_id:
                gate_name = g["name"]
                break
        
        session["gate_id"] = gate_id
        session["gate_name"] = gate_name
        session["status"] = "processing"
        
        await callback.message.edit_caption(
            caption=apply_branding(f"🚀 <b>Starting Mass Check...</b>\nGate: <code>{gate_name}</code>"),
            reply_markup=create_mass_keyboard(user_id, session),
            parse_mode="HTML"
        )
        asyncio.create_task(mass_process_loop(user_id, callback.bot))

    elif action == "stop":
        session["status"] = "paused"
        await callback.message.edit_caption(
            caption=apply_branding("⏸ <b>Paused</b>"),
            reply_markup=create_mass_keyboard(user_id, session),
            parse_mode="HTML"
        )
        await callback.answer("Stopped.")

    elif action == "resume":
        session["status"] = "processing"
        await callback.message.edit_caption(
            caption=apply_branding(f"🚀 <b>Resuming...</b>\nGate: <code>{session['gate_name']}</code>"),
            reply_markup=create_mass_keyboard(user_id, session),
            parse_mode="HTML"
        )
        asyncio.create_task(mass_process_loop(user_id, callback.bot))
        await callback.answer("Resumed.")

    elif action == "new_file":
        if user_id in mass_sessions:
            del mass_sessions[user_id]
        await callback.message.delete()
        await callback.message.answer(apply_branding("Please upload a new .txt file."), parse_mode="HTML")
        await state.clear()

    elif action == "cancel":
        if user_id in mass_sessions:
            del mass_sessions[user_id]
        try:
            await callback.message.delete()
        except:
            pass
        await callback.answer("Cancelled.")
        await state.clear()

    elif action == "back_to_types":
        await callback.message.edit_caption(
            caption=apply_branding("<b>Select Gate Type:</b>"),
            reply_markup=kb_file_uploaded(),
            parse_mode="HTML"
        )
        await state.set_state(MassCheckState.waiting_for_gate_type)

    # Answer callback only if not already answered in a branch above
    try:
        await callback.answer()
    except Exception:
        pass
