"""
=================================================================
نظام الفحص الجماعي المطور - Advanced Mass Check System
=================================================================
UI/UX Spec:
- لا يوجد أمر /mass
- الفحص الجماعي يبدأ فقط عند رفع ملف .txt
- بعد الرفع: المستخدم يختار نوع البوابة (AUTH/CHARGE/LOOKUP)
- ثم يختار بوابة محددة لبدء الفحص
- Premium gating: FREE users يُرفضون ويُوجهون إلى /buy
"""

import asyncio
import aiohttp
import ssl
import datetime
import random
import time
from aiogram import types, Bot, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config
from premium_util import can_start_mass, consume_for_single, refund_credit, update_last_chk, is_premium

# Banner ثابت
BANNER_URL = "https://t.me/i5ese/347"


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
# Keyboards
# =================================================================

def kb_file_uploaded():
    """أزرار بعد رفع الملف - اختيار نوع البوابة"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("AUTH", callback_data="mass:type:auth"),
        InlineKeyboardButton("CHARGE", callback_data="mass:type:charge")
    )
    kb.add(InlineKeyboardButton("LOOKUP", callback_data="mass:type:lookup"))
    kb.add(InlineKeyboardButton("CANCEL", callback_data="mass:cancel"))
    return kb


def kb_auth_gates():
    """أزرار بوابات AUTH"""
    kb = InlineKeyboardMarkup(row_width=2)
    for gate in AUTH_GATES:
        kb.add(InlineKeyboardButton(gate["name"], callback_data=f"mass:gate:{gate['id']}"))
    kb.add(InlineKeyboardButton("⬅️ BACK", callback_data="mass:back_to_types"))
    kb.add(InlineKeyboardButton("CANCEL", callback_data="mass:cancel"))
    return kb


def kb_charge_gates():
    """أزرار بوابات CHARGE"""
    kb = InlineKeyboardMarkup(row_width=2)
    for gate in CHARGE_GATES:
        kb.add(InlineKeyboardButton(gate["name"], callback_data=f"mass:gate:{gate['id']}"))
    kb.add(InlineKeyboardButton("⬅️ BACK", callback_data="mass:back_to_types"))
    kb.add(InlineKeyboardButton("CANCEL", callback_data="mass:cancel"))
    return kb


def kb_lookup_gates():
    """أزرار بوابات LOOKUP"""
    kb = InlineKeyboardMarkup(row_width=2)
    for gate in LOOKUP_GATES:
        kb.add(InlineKeyboardButton(gate["name"], callback_data=f"mass:gate:{gate['id']}"))
    kb.add(InlineKeyboardButton("⬅️ BACK", callback_data="mass:back_to_types"))
    kb.add(InlineKeyboardButton("CANCEL", callback_data="mass:cancel"))
    return kb


def create_stats_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """إنشاء لوحة الإحصائيات"""
    session = mass_sessions.get(user_id)
    if not session:
        return InlineKeyboardMarkup()

    keyboard = InlineKeyboardMarkup(row_width=1)
    
    total = len(session["cards"])
    processed = session["processed"]
    progress = (processed / total * 100) if total > 0 else 0
    
    keyboard.add(InlineKeyboardButton(text=f"𝙏𝙊𝙏𝘼𝙇 🌪️: [ {total} ]", callback_data="mass_info"))
    keyboard.add(InlineKeyboardButton(text=f"𝙋𝙍𝙊𝙂𝙍𝙀𝙎𝙎 🥷🏻: [ {progress:.2f}% ]", callback_data="mass_info"))
    keyboard.add(InlineKeyboardButton(text=f"𝙊𝙏𝙋 𝙍𝙀𝙌𝙐𝙄𝙍𝙀𝘿 ✅: [ {session['otp']} ]", callback_data="mass_info"))
    keyboard.add(InlineKeyboardButton(text=f"𝙋𝘼𝙎𝙎𝙀𝘿 ✅: [ {session['passed']} ]", callback_data="mass_info"))
    keyboard.add(InlineKeyboardButton(text=f"𝙍𝙀𝙅𝙀𝘾𝙏𝙀𝘿 ❌: [ {session['rejected']} ]", callback_data="mass_info"))
    keyboard.add(InlineKeyboardButton(text=f"𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓: [ {session['unknown']} ]", callback_data="mass_info"))
    
    if session["status"] == "processing":
        keyboard.add(InlineKeyboardButton(text="[ STOP ]", callback_data="mass:stop"))
    elif session["status"] == "paused":
        keyboard.add(InlineKeyboardButton(text="𝙍𝙀𝙎𝙐𝙈𝙀 🪢", callback_data="mass:resume"))
        keyboard.add(InlineKeyboardButton(text="𝙉𝙀𝙒 𝙁𝙄𝙇𝙀 🪐", callback_data="mass:new_file"))
    
    return keyboard


def kb_completed():
    """أزرار بعد اكتمال الفحص"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


# =================================================================
# Captions
# =================================================================

def cap_file_uploaded(file_name: str, total_lines: int, valid_items: int) -> str:
    """رسالة بعد رفع الملف"""
    return (
        "𝗢.𝗧 Bot — File Uploaded\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n\n"
        "Your file has been received successfully.\n\n"
        f"• File name   ⌁  {file_name}\n"
        f"• Total lines ⌁  {total_lines}\n"
        f"• Valid items ⌁  {valid_items}\n\n"
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
    
    # تحليل بيانات البطاقة
    card_info = card_data.strip().replace('/', '|')
    parts = card_info.split('|')
    if len(parts) < 3:
        session["processed"] += 1
        session["unknown"] += 1
        return True

    cc = parts[0]
    
    # خصم الكريدت
    success, msg = await consume_for_single(user_id_str)
    if not success:
        session["status"] = "paused"
        return False

    # الحصول على معلومات BIN
    bin_info = await get_bin_info(cc)

    # اختيار نتيجة عشوائية
    status_code, response_text, category, is_transient = random.choices(
        MOCK_RESPONSES_MASS, weights=RESPONSE_WEIGHTS, k=1
    )[0]
    
    # زمن وهمي للاستجابة
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # معالجة الأخطاء المؤقتة (Refund)
    if is_transient:
        await refund_credit(user_id_str, 1, status_code)
        
    # تحديث حالة الجلسة
    session["processed"] += 1
    if category == "otp": session["otp"] += 1
    elif category == "passed": session["passed"] += 1
    elif category == "rejected": session["rejected"] += 1
    else: session["unknown"] += 1
    
    # إرسال النتيجة للـ OTP و PASSED فقط
    if category in ["otp", "passed"]:
        gateway_name = session.get("gateway_name", "Unknown")
        text = (
            f"{response_text}\n\n"
            f"• 𝗖𝗮𝗿𝗱 ⌁ <code>{card_data}</code>\n"
            f"• 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ {gateway_name}\n"
            f"• 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ {status_code}\n\n"
            f"• 𝗜𝗻𝗳𝗼 ⌁ {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
            f"• 𝐈𝐬𝐬𝐮𝐞𝐫 ⌁ {bin_info['bank']}\n"
            f"• 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info['country']} {bin_info['country_flag']}"
        )
        try:
            await bot.send_message(session["chat_id"], text, parse_mode="HTML")
        except:
            pass
        
    return True


# =================================================================
# دوال المعالجة الرئيسية
# =================================================================

async def handle_document(message: types.Message, state: FSMContext):
    """معالج رفع الملفات .txt"""
    user_id = message.from_user.id
    
    # التحقق من نوع الملف
    if not message.document:
        return
    
    file_name = message.document.file_name or ""
    
    if not file_name.endswith('.txt'):
        await message.reply(
            "Invalid file type.\n\n"
            "Please upload a valid .txt file only."
        )
        return
    
    # Premium gating
    if user_id != config.Admin and not await is_premium(str(user_id)):
        await message.reply(
            "⛔ <b>Premium Access Required</b>\n\n"
            "Mass checking is available only for Premium users.\n"
            "Use /buy to purchase a subscription and unlock all features.",
            parse_mode="HTML"
        )
        return
    
    # التحقق من الكريدت
    if not await can_start_mass(str(user_id)):
        await message.reply("⛔ لا يوجد كريدت كافٍ. استخدم /buy لشراء كريدت.")
        return
    
    try:
        # تحميل الملف
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        content = downloaded_file.read().decode('utf-8', errors='ignore')
        
        lines = content.strip().split('\n')
        total_lines = len(lines)
        cards = [line.strip() for line in lines if "|" in line]
        valid_items = len(cards)
        
        if valid_items == 0:
            await message.reply("❌ لا توجد بطاقات صالحة في الملف.")
            return
        
        # حفظ البيانات في الجلسة
        mass_sessions[user_id] = {
            "status": "waiting",
            "cards": cards[:1000],  # حد أقصى 1000 بطاقة
            "file_name": file_name,
            "total_lines": total_lines,
            "valid_items": valid_items,
            "processed": 0,
            "otp": 0,
            "passed": 0,
            "rejected": 0,
            "unknown": 0,
            "chat_id": message.chat.id,
            "gate_type": None,
            "gateway_id": None,
            "gateway_name": None,
            "message_id": None,
            "start_time": None
        }
        
        # إرسال رسالة اختيار نوع البوابة
        msg = await message.answer_photo(
            photo=BANNER_URL,
            caption=cap_file_uploaded(file_name, total_lines, valid_items),
            parse_mode="HTML",
            reply_markup=kb_file_uploaded()
        )
        
        mass_sessions[user_id]["message_id"] = msg.message_id
        await MassCheckState.waiting_for_gate_type.set()
        
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")


async def mass_callback_handler(call: types.CallbackQuery, state: FSMContext):
    """معالج callbacks الفحص الجماعي"""
    user_id = call.from_user.id
    data = call.data
    
    if data == "mass_info":
        await call.answer()
        return
    
    # CANCEL - العودة إلى /cmds
    if data == "mass:cancel":
        if user_id in mass_sessions:
            del mass_sessions[user_id]
        await state.finish()
        
        # استيراد cmds للعودة
        from cmds import cap_cmds, kb_cmds, BANNER_URL
        try:
            await call.message.edit_media(
                types.InputMediaPhoto(media=BANNER_URL, caption=cap_cmds(), parse_mode="HTML")
            )
            await call.message.edit_reply_markup(kb_cmds())
        except:
            pass
        await call.answer("Cancelled")
        return
    
    # اختيار نوع البوابة
    if data.startswith("mass:type:"):
        gate_type = data.split(":")[2]
        
        if user_id not in mass_sessions:
            await call.answer("Session expired. Please upload file again.", show_alert=True)
            return
        
        mass_sessions[user_id]["gate_type"] = gate_type
        
        # عرض البوابات المتاحة
        if gate_type == "auth":
            kb = kb_auth_gates()
            caption = "Select AUTH Gateway:"
        elif gate_type == "charge":
            kb = kb_charge_gates()
            caption = "Select CHARGE Gateway:"
        else:
            kb = kb_lookup_gates()
            caption = "Select LOOKUP Gateway:"
        
        try:
            await call.message.edit_caption(caption=caption, reply_markup=kb)
        except:
            pass
        
        await MassCheckState.waiting_for_gateway.set()
        await call.answer()
        return
    
    # العودة لاختيار نوع البوابة
    if data == "mass:back_to_types":
        if user_id not in mass_sessions:
            await call.answer("Session expired.", show_alert=True)
            return
        
        session = mass_sessions[user_id]
        caption = cap_file_uploaded(
            session["file_name"],
            session["total_lines"],
            session["valid_items"]
        )
        
        try:
            await call.message.edit_caption(caption=caption, reply_markup=kb_file_uploaded())
        except:
            pass
        
        await MassCheckState.waiting_for_gate_type.set()
        await call.answer()
        return
    
    # اختيار بوابة محددة وبدء الفحص
    if data.startswith("mass:gate:"):
        gate_id = data.split(":")[2]
        
        if user_id not in mass_sessions:
            await call.answer("Session expired. Please upload file again.", show_alert=True)
            return
        
        session = mass_sessions[user_id]
        gate_type = session.get("gate_type")
        
        # البحث عن البوابة
        all_gates = AUTH_GATES + CHARGE_GATES + LOOKUP_GATES
        gate = next((g for g in all_gates if g["id"] == gate_id), None)
        
        if not gate:
            await call.answer("Gateway not found.", show_alert=True)
            return
        
        # تحديث الجلسة
        session["gateway_id"] = gate_id
        session["gateway_name"] = gate["name"]
        session["status"] = "processing"
        session["start_time"] = time.time()
        
        # تحديث الرسالة لعرض الإحصائيات
        try:
            await call.message.edit_caption(
                caption=f"𝘽𝙊𝙏 𝘾𝙃𝙀𝘾𝙆 𝘽𝙔 @OT_DEV\nGateway: {gate['name']}",
                reply_markup=create_stats_keyboard(user_id)
            )
        except:
            pass
        
        # بدء الفحص
        await MassCheckState.processing.set()
        asyncio.create_task(run_mass_process(user_id, call.message.bot))
        await call.answer(f"Starting mass check with {gate['name']}...")
        return
    
    # STOP
    if data == "mass:stop":
        if user_id in mass_sessions:
            mass_sessions[user_id]["status"] = "paused"
            await call.message.edit_reply_markup(reply_markup=create_stats_keyboard(user_id))
            await call.answer("Processing stopped. You can resume or send a new file.", show_alert=True)
        return

    # RESUME
    if data == "mass:resume":
        if user_id in mass_sessions:
            mass_sessions[user_id]["status"] = "processing"
            await call.answer("Processing resumed.")
            asyncio.create_task(run_mass_process(user_id, call.message.bot))
        return

    # NEW FILE
    if data == "mass:new_file":
        if user_id in mass_sessions:
            del mass_sessions[user_id]
        await state.finish()
        await call.message.answer("Send the new .txt file now.")
        await call.answer()
        return
    
    await call.answer()


async def run_mass_process(user_id: int, bot: Bot):
    """تشغيل عملية الفحص الجماعي"""
    session = mass_sessions.get(user_id)
    if not session:
        return
    
    while session["processed"] < len(session["cards"]) and session["status"] == "processing":
        card = session["cards"][session["processed"]]
        success = await check_single_card_mock(card, user_id, bot)
        if not success:
            break
        
        # تحديث اللوحة كل 5 بطاقات
        if session["processed"] % 5 == 0:
            try:
                await bot.edit_message_reply_markup(
                    chat_id=session["chat_id"],
                    message_id=session["message_id"],
                    reply_markup=create_stats_keyboard(user_id)
                )
            except:
                pass
    
    # اكتمال الفحص
    if session["processed"] >= len(session["cards"]):
        session["status"] = "completed"
        
        # رسالة الملخص
        summary = (
            "✅ <b>Mass Check Completed</b>\n\n"
            f"• Total: {len(session['cards'])}\n"
            f"• OTP Required: {session['otp']}\n"
            f"• Passed: {session['passed']}\n"
            f"• Rejected: {session['rejected']}\n"
            f"• Unknown: {session['unknown']}\n\n"
            f"Gateway: {session['gateway_name']}"
        )
        
        try:
            await bot.edit_message_caption(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                caption=summary,
                parse_mode="HTML",
                reply_markup=kb_completed()
            )
        except:
            await bot.send_message(session["chat_id"], summary, parse_mode="HTML", reply_markup=kb_completed())
        
        if user_id in mass_sessions:
            del mass_sessions[user_id]


def register_handlers(dp: Dispatcher):
    """تسجيل معالجات الفحص الجماعي"""
    # معالج رفع الملفات - يعمل في أي حالة
    dp.register_message_handler(handle_document, content_types=['document'], state="*")
    
    # معالج callbacks
    dp.register_callback_query_handler(
        mass_callback_handler,
        lambda c: c.data and (c.data.startswith("mass:") or c.data == "mass_info"),
        state="*"
    )
