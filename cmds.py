"""
=================================================================
O.T Bot - Commands & UI Module (Updated UI/UX Spec + UI Patch)
=================================================================
تطبيق مواصفات UI/UX الجديدة:
- شاشة /start مع MY PROFILE و ABOUT
- شاشة /cmds كمركز الأوامر الرئيسي
- قسم GATEWAYS مع AUTH/CHARGE/LOOKUP
- قسم TOOLS مع CC GENERATOR و CC SCRAPER
- HOME يعود إلى /start في مسار /start، وإلى /cmds في باقي المسارات
- EXIT يعرض "See you later 🙂" بدون أزرار

UI Patch:
1) زر HOME في مسار /start يعود إلى /start وليس /cmds
2) صورة MY PROFILE تعرض صورة المستخدم (مع fallback للبانر)
3) رابط Profile قابل للنقر
4) /sup يعرض MY PROFILE بدون أزرار
"""

from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, LabeledPrice
import contextlib
from config import Admin, PAYMENT_PROVIDER_TOKEN

# ========= Config =========
# Banner ثابت لجميع الشاشات
BANNER_URL = "https://t.me/i5ese/347"

# Import premium utilities
import premium_util
import asyncio
from datetime import datetime, timezone


# ========= Subscription Helper =========

async def _sub_info(user_id: int) -> dict:
    """
    Helper to get tier, credits, and validity for a user from premium.json
    Returns: {"tier": "FREE/PREMIUM/UNLIMITED/ADMIN", "credits": str, "valid_until": str, "last_chk": str}
    """
    # Check if Admin first
    if user_id == Admin:
        return {
            "tier": "ADMIN",
            "credits": "∞",
            "valid_until": "Unlimited",
            "last_chk": "—"
        }
    
    record = await premium_util.get_record(str(user_id))
    
    if not record:
        return {
            "tier": "FREE",
            "credits": "0",
            "valid_until": "No Subscription",
            "last_chk": "—"
        }
    
    # Determine tier
    if record.get("unlimited"):
        tier = "UNLIMITED"
        credits_display = "∞"
        expires_str = record.get("expires")
        if expires_str and expires_str != "—":
            try:
                dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                validity = dt.strftime("%m/%d/%Y UTC")
            except:
                validity = "Unlimited"
        else:
            validity = "Unlimited"
    else:
        # Check time-based subscription
        expires_str = record.get("expires")
        credits = record.get("credits", 0)
        
        if expires_str and expires_str != "—":
            try:
                expires_time = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if now < expires_time:
                    tier = "PREMIUM"
                    credits_display = str(credits)
                    validity = expires_time.strftime("%m/%d/%Y UTC")
                else:
                    if credits > 0:
                        tier = "PREMIUM"
                        credits_display = str(credits)
                        validity = "No Subscription"
                    else:
                        tier = "FREE"
                        credits_display = "0"
                        validity = "No Subscription"
            except:
                if credits > 0:
                    tier = "PREMIUM"
                    credits_display = str(credits)
                    validity = "No Subscription"
                else:
                    tier = "FREE"
                    credits_display = "0"
                    validity = "No Subscription"
        else:
            if credits > 0:
                tier = "PREMIUM"
                credits_display = str(credits)
                validity = "No Subscription"
            else:
                tier = "FREE"
                credits_display = "0"
                validity = "No Subscription"
    
    # Format last_chk
    last_chk_str = record.get("last_chk", "—")
    if last_chk_str and last_chk_str != "—":
        try:
            dt = datetime.strptime(last_chk_str, "%Y-%m-%d %H:%M:%S")
            last_chk = dt.strftime("%H:%M » %m/%d/%Y UTC")
        except:
            last_chk = last_chk_str
    else:
        last_chk = "—"
    
    return {
        "tier": tier,
        "credits": credits_display,
        "valid_until": validity,
        "last_chk": last_chk
    }


# ========= Captions =========

def cap_start(first_name: str) -> str:
    """شاشة /start"""
    return (
        f"🌅Hello  𓏺 {first_name}\n\n"
        "I'm 𝗢.𝗧↯. A Multi Functional Bot With Many Tools and Checker Gateways.\n"
        "Press /cmds To Know My Features"
    )


def cap_my_profile(u: types.User, sub: dict) -> str:
    """شاشة MY PROFILE مع رابط Profile قابل للنقر"""
    uname = f"@{u.username}" if u.username else "—"
    # رابط Profile قابل للنقر بصيغة HTML
    profile_link = f'<a href="tg://user?id={u.id}">Click Here</a>'
    return (
        "み O.T Bot — User Information\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"UID        : {u.id}\n"
        f"Name       : {u.first_name}\n"
        f"Username   : {uname}\n"
        f"Profile    : {profile_link}\n\n"
        "Subscription Information\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"Status     : {sub['tier']}\n"
        f"Credits    : {sub['credits']}\n"
        f"Validity   : {sub['valid_until']}\n"
        f"Last Check : {sub['last_chk']}\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "• /Buy VIP Subscription to Unlock All Features.\n"
        "• DeveBy ↝O.T"
    )


def cap_about() -> str:
    """شاشة ABOUT"""
    return (
        "み  O.T Bot↯ BreakDown !\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "Language ⌁ Python x Aiogram\n"
        "Version    ⌁ v1.1\n"
        "Hosting      ⌁ VPS\n"
        "Developer     ⌁ O.T Dev\n"
        "Updated       ⌁ 2026\n\n"
        "Community\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "• Official Channel\n"
        "• Support Chat"
    )


def cap_cmds() -> str:
    """شاشة /cmds - المركز الرئيسي"""
    return (
        "𝗢.𝗧 Bot — Commands Overview\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "Gateways\n"
        "•  Auth\n"
        "•  Charge\n"
        "•  LookUp\n\n"
        "Tools\n"
        "• CC Generator\n"
        "• CC Scraper\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "↯   Click Below to View Full Details  ↯"
    )


def cap_gateways_overview() -> str:
    """شاشة GATEWAYS الرئيسية"""
    return (
        "Overview Section of 𝗢.𝗧 Bot\n\n"
        "•  Auth     ⌁  3 Gates\n"
        "•  Charge   ⌁  4 Gates\n"
        "•  LookUp   ⌁  4 Gates\n\n"
        "↯  Check Below to View Available Gates."
    )


def cap_auth_gates() -> str:
    """شاشة AUTH Gates"""
    return (
        "み 𝗢.𝗧 Bot AUTH\n\n"
        "↯ Name » Stripe Auth  ( /au )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Stripe AUTH\n\n"
        "↯ Name » Braintree Auth  ( /ba )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Braintree Auth\n\n"
        "↯ Name » Square Auth  ( /sq )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Square Auth"
    )


def cap_charge_gates() -> str:
    """شاشة CHARGE Gates"""
    return (
        "み 𝗢.𝗧 Bot CHARGE\n\n"
        "↯ Name » PayPal Cvv  ( /Pv )\n"
        "• Status   ⌁  PREMIUM  »  ON\n"
        "• Gateway  ⌁  PayPal\n\n"
        "↯ Name » Square charge  ( /Sh )\n"
        "• Status   ⌁  PREMIUM  »  ON\n"
        "• Gateway  ⌁  Square charge\n\n"
        "↯ Name » Azathoth  ( /az )\n"
        "• Status   ⌁  PREMIUM  »  ON\n"
        "• Gateway  ⌁  Authorize.Net [AIM]\n\n"
        "↯ Name » Stripe Charge  ( /sc )\n"
        "• Status   ⌁  PREMIUM  »  ON\n"
        "• Gateway  ⌁  Stripe v1"
    )


def cap_lookup_gates() -> str:
    """شاشة LOOKUP Gates"""
    return (
        "み 𝗢.𝗧 Bot LookUp\n\n"
        "↯ Name » Verify Secure  ( /vbv )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Braintree 3DS\n\n"
        "↯ Name » Global 3DS  ( /G3 )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Global payment\n\n"
        "↯ Name » Global Passed  ( /GP )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Global payment\n\n"
        "↯ Name » Verify Passed  ( /BP )\n"
        "• Status   ⌁  PREMIUM  ⌁  ON\n"
        "• Gateway  ⌁  Braintree Passed"
    )


def cap_tools() -> str:
    """شاشة TOOLS الرئيسية"""
    return (
        "𝗢.𝗧 Bot — Tools Overview\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "• CC Generator\n"
        "• CC Scraper\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "↯   Click Below to View Full Details  ↯"
    )


def cap_cc_generator() -> str:
    """شاشة CC GENERATOR"""
    return (
        "あ 𝗢.𝗧 Bot Binning Tools あ\n\n"
        "↯ Name  Bin Checker\n"
        "• Format  » /bin bin_number\n"
        "• Status  »  ACTIVE  ✅\n\n"
        "↯ Name  Card Generator\n"
        "• Format  » /gen bin\n"
        "• Status  »  ACTIVE  ✅\n\n"
        "↯ Name  Card Generator\n"
        "• Format  » /mgen bin [Number card]\n"
        "• Status  »  ACTIVE  ✅"
    )


def cap_cc_scraper() -> str:
    """شاشة CC SCRAPER"""
    return "COMING SOON"


# ========= Keyboards =========

def kb_start():
    """أزرار شاشة /start"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("MY PROFILE", callback_data="st:profile"),
        InlineKeyboardButton("ABOUT", callback_data="st:about")
    )
    kb.add(InlineKeyboardButton("EXIT", callback_data="st:exit"))
    return kb


def kb_profile_from_start():
    """أزرار شاشة MY PROFILE (من مسار /start) - HOME يعود إلى /start"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("HOME", callback_data="st:home"))
    return kb


def kb_about_from_start():
    """أزرار شاشة ABOUT (من مسار /start) - HOME يعود إلى /start"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("HOME", callback_data="st:home"))
    return kb


def kb_cmds():
    """أزرار شاشة /cmds"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("GATEWAYS", callback_data="cmds:gateways"),
        InlineKeyboardButton("TOOLS", callback_data="cmds:tools")
    )
    kb.add(InlineKeyboardButton("EXIT", callback_data="st:exit"))
    return kb


def kb_gateways():
    """أزرار شاشة GATEWAYS الرئيسية"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("AUTH", callback_data="gw:auth"),
        InlineKeyboardButton("CHARGE", callback_data="gw:charge")
    )
    kb.add(InlineKeyboardButton("LOOKUP", callback_data="gw:lookup"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_auth_gates():
    """أزرار شاشة AUTH (بدون زر AUTH)"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("CHARGE", callback_data="gw:charge"))
    kb.add(InlineKeyboardButton("LOOKUP", callback_data="gw:lookup"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_charge_gates():
    """أزرار شاشة CHARGE (بدون زر CHARGE)"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("AUTH", callback_data="gw:auth"))
    kb.add(InlineKeyboardButton("LOOKUP", callback_data="gw:lookup"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_lookup_gates():
    """أزرار شاشة LOOKUP (بدون زر LOOKUP)"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("AUTH", callback_data="gw:auth"))
    kb.add(InlineKeyboardButton("CHARGE", callback_data="gw:charge"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_tools():
    """أزرار شاشة TOOLS"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("CC GENERATOR", callback_data="tools:gen"),
        InlineKeyboardButton("CC SCRAPER", callback_data="tools:scr")
    )
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_cc_generator():
    """أزرار شاشة CC GENERATOR"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("CC SCRAPER", callback_data="tools:scr"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


def kb_cc_scraper():
    """أزرار شاشة CC SCRAPER"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("CC GENERATOR", callback_data="tools:gen"))
    kb.add(InlineKeyboardButton("HOME", callback_data="cmds:home"))
    return kb


# ========= Helpers =========

MAX_CAPTION_LEN = 1024

def _truncate_caption(text: str) -> str:
    if not text:
        return ""
    if len(text) > MAX_CAPTION_LEN:
        return text[:MAX_CAPTION_LEN - 3] + "..."
    return text


async def _edit_media(call: types.CallbackQuery, caption: str, kb, photo_url: str = None):
    """تعديل الرسالة مع صورة (البانر افتراضياً أو صورة مخصصة)"""
    safe_caption = _truncate_caption(caption)
    use_photo = photo_url if photo_url else BANNER_URL
    
    with contextlib.suppress(Exception):
        await call.message.edit_media(
            InputMediaPhoto(media=use_photo, caption=safe_caption, parse_mode="HTML")
        )
        await call.message.edit_reply_markup(kb)
        return
    
    with contextlib.suppress(Exception):
        await call.message.edit_caption(
            caption=safe_caption,
            parse_mode="HTML",
            reply_markup=kb
        )
        return
    
    # Fallback: send new message
    await call.message.answer_photo(
        photo=use_photo,
        caption=safe_caption,
        parse_mode="HTML",
        reply_markup=kb
    )


async def _get_user_profile_photo(bot, user_id: int) -> str:
    """الحصول على صورة المستخدم الشخصية، أو البانر كـ fallback"""
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            # الحصول على أكبر حجم متاح
            photo = photos.photos[0][-1]
            return photo.file_id
    except Exception as e:
        print(f"Error getting user profile photo: {e}")
    
    # Fallback إلى البانر
    return BANNER_URL


# ========= /start Command =========

async def start_command(message: types.Message):
    """معالج أمر /start"""
    await message.answer_photo(
        photo=BANNER_URL,
        caption=cap_start(message.from_user.first_name or "User"),
        parse_mode="HTML",
        reply_markup=kb_start()
    )


# ========= /sup Command (MY PROFILE بدون أزرار) =========

async def sup_command(message: types.Message):
    """معالج أمر /sup - يعرض MY PROFILE بدون أزرار"""
    sub = await _sub_info(message.from_user.id)
    
    # الحصول على صورة المستخدم
    user_photo = await _get_user_profile_photo(message.bot, message.from_user.id)
    
    await message.answer_photo(
        photo=user_photo,
        caption=cap_my_profile(message.from_user, sub),
        parse_mode="HTML",
        reply_markup=None  # بدون أزرار
    )


# ========= /cmds Command =========

async def cmds_entry(message: types.Message):
    """معالج أمر /cmds - المركز الرئيسي"""
    await message.answer_photo(
        photo=BANNER_URL,
        caption=cap_cmds(),
        parse_mode="HTML",
        reply_markup=kb_cmds()
    )


# ========= Start Callbacks =========

async def start_callbacks(call: types.CallbackQuery):
    """معالج callbacks شاشة /start"""
    data = call.data or ""
    
    # HOME من مسار /start - العودة إلى شاشة /start
    if data == "st:home":
        await _edit_media(
            call,
            cap_start(call.from_user.first_name or "User"),
            kb_start(),
            BANNER_URL
        )
        await call.answer()
        return
    
    # MY PROFILE من مسار /start - مع صورة المستخدم
    if data == "st:profile":
        sub = await _sub_info(call.from_user.id)
        
        # الحصول على صورة المستخدم
        user_photo = await _get_user_profile_photo(call.message.bot, call.from_user.id)
        
        await _edit_media(
            call,
            cap_my_profile(call.from_user, sub),
            kb_profile_from_start(),  # HOME يعود إلى /start
            user_photo  # صورة المستخدم
        )
        await call.answer()
        return
    
    # ABOUT من مسار /start
    if data == "st:about":
        await _edit_media(
            call,
            cap_about(),
            kb_about_from_start(),  # HOME يعود إلى /start
            BANNER_URL
        )
        await call.answer()
        return
    
    # EXIT
    if data == "st:exit":
        with contextlib.suppress(Exception):
            await call.message.edit_caption("See you later 🙂", parse_mode="HTML", reply_markup=None)
        await call.answer()
        return
    
    await call.answer()


# ========= Cmds Callbacks =========

async def cmds_callbacks(call: types.CallbackQuery):
    """معالج callbacks شاشة /cmds والأقسام الفرعية"""
    data = call.data or ""
    
    # HOME - العودة إلى /cmds
    if data == "cmds:home":
        await _edit_media(call, cap_cmds(), kb_cmds(), BANNER_URL)
        await call.answer()
        return
    
    # GATEWAYS الرئيسية
    if data == "cmds:gateways":
        await _edit_media(call, cap_gateways_overview(), kb_gateways(), BANNER_URL)
        await call.answer()
        return
    
    # AUTH Gates
    if data == "gw:auth":
        await _edit_media(call, cap_auth_gates(), kb_auth_gates(), BANNER_URL)
        await call.answer()
        return
    
    # CHARGE Gates
    if data == "gw:charge":
        await _edit_media(call, cap_charge_gates(), kb_charge_gates(), BANNER_URL)
        await call.answer()
        return
    
    # LOOKUP Gates
    if data == "gw:lookup":
        await _edit_media(call, cap_lookup_gates(), kb_lookup_gates(), BANNER_URL)
        await call.answer()
        return
    
    # TOOLS الرئيسية
    if data == "cmds:tools":
        await _edit_media(call, cap_tools(), kb_tools(), BANNER_URL)
        await call.answer()
        return
    
    # CC GENERATOR
    if data == "tools:gen":
        await _edit_media(call, cap_cc_generator(), kb_cc_generator(), BANNER_URL)
        await call.answer()
        return
    
    # CC SCRAPER
    if data == "tools:scr":
        await _edit_media(call, cap_cc_scraper(), kb_cc_scraper(), BANNER_URL)
        await call.answer()
        return
    
    await call.answer("Action not found.")
