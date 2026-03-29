"""
=================================================================
𝖨𝖦𝖭𝖨𝖲𝖷 - Commands & UI Module (aiogram 3.25.0 + Bot API 9.4)
=================================================================
"""

from aiogram import types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto,
)
import contextlib
from config import Admin, PAYMENT_PROVIDER_TOKEN
from branding import apply_branding

# ========= Config =========
BANNER_URL = "https://t.me/i5ese/347"

import premium_util
import asyncio
from datetime import datetime, timezone


# ========= Subscription Helper =========

async def _sub_info(user_id: int) -> dict:
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

def cap_start(u: types.User) -> str:
    first_name = u.first_name
    user_id = u.id
    return apply_branding(
        f"Hello 𓏺 <a href=\"tg://user?id={user_id}\">{first_name}</a>\n\n"
        f"I'm <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. A Multi Functional Bot With Many Tools and Checker Gateways.\n"
        "Press /cmds To Know My Features"
    )


def cap_my_profile(u: types.User, sub: dict) -> str:
    uname = f"@{u.username}" if u.username else "—"
    user_id = u.id
    first_name = u.first_name
    profile_link = f'<a href="tg://user?id={user_id}">Click Here</a>'
    return apply_branding(
        f"み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a> — User Information\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> UID        : {user_id}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Name       : <a href=\"tg://user?id={user_id}\">{first_name}</a>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Username   : {uname}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Profile    : {profile_link}\n\n"
        "Subscription Information\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Status     : {sub['tier']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Credits    : {sub['credits']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Validity   : {sub['valid_until']}\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> Last Check : {sub['last_chk']}\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> /Buy VIP Subscription to Unlock All Features.\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> DeveBy ↝ <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>"
    )


def cap_about() -> str:
    return apply_branding(
        "み  <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯ BreakDown !\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Language ⌁ Python x Aiogram\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Version    ⌁ v1.1\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Hosting      ⌁ VPS\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Developer     ⌁ <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a> Dev\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Updated       ⌁ 2026\n\n"
        "Community\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Official Channel\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Support Chat"
    )


def cap_cmds() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯.  — Commands Overview\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "Gateways\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Auth\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Charge\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  LookUp\n\n"
        "Tools\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> CC Generator\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> CC Scraper\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "↯   Click Below to View Full Details  ↯"
    )


def cap_gateways_overview() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — Overview Section\n\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Auth     ⌁  3 Gates\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Charge   ⌁  4 Gates\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  LookUp   ⌁  4 Gates\n\n"
        "↯  Check Below to View Available Gates."
    )


def cap_auth_gates() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — AUTH\n\n"
        "↯ Name » Stripe Auth  ( /au )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Stripe AUTH\n\n"
        "↯ Name » Braintree Auth  ( /ba )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Braintree Auth\n\n"
        "↯ Name » Square Auth  ( /sq )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Square Auth"
    )


def cap_charge_gates() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — CHARGE\n\n"
        "↯ Name » PayPal Cvv  ( /Pv )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  »  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  PayPal\n\n"
        "↯ Name » Square charge  ( /Sh )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  »  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Square charge\n\n"
        "↯ Name » Azathoth  ( /az )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  »  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Authorize.Net [AIM]\n\n"
        "↯ Name » Stripe Charge  ( /sc )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  »  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Stripe v1"
    )


def cap_lookup_gates() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — LookUp\n\n"
        "↯ Name » Verify Secure  ( /vbv )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Braintree 3DS\n\n"
        "↯ Name » Global 3DS  ( /G3 )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Global payment\n\n"
        "↯ Name » Global Passed  ( /GP )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Global payment\n\n"
        "↯ Name » Verify Passed  ( /BP )\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status   ⌁  PREMIUM  ⌁  ON\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Gateway  ⌁  Braintree Passed"
    )


def cap_tools() -> str:
    return apply_branding(
        "み <a href=\"http://t.me/IgnisXBot\">𝖨𝖦𝖭𝖨𝖲𝖷</a>↯. — Tools Overview\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> CC Generator\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> CC Scraper\n\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "↯   Click Below to View Full Details  ↯"
    )


def cap_cc_generator() -> str:
    return apply_branding(
        "あ 𝖨𝖦𝖭𝖨𝖲𝖷 Bot Binning Tools あ\n\n"
        "↯ Name  Bin Checker\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Format  » /bin bin_number\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status  »  ACTIVE  ✅\n\n"
        "↯ Name  Card Generator\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Format  » /gen bin\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status  »  ACTIVE  ✅\n\n"
        "↯ Name  Card Generator\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Format  » /mgen bin [Number card]\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Status  »  ACTIVE  ✅"
    )


def cap_cc_scraper() -> str:
    return "COMING SOON"


# ========= Keyboards (aiogram 3.x style) =========

def kb_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MY PROFILE", callback_data="st:profile", style="primary"),
            InlineKeyboardButton(text="ABOUT", callback_data="st:about", style="primary")
        ],
        [InlineKeyboardButton(text="EXIT", callback_data="st:exit", style="danger")]
    ])


def kb_profile_from_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="HOME", callback_data="st:home", style="primary")]
    ])


def kb_about_from_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="HOME", callback_data="st:home", style="primary")]
    ])


def kb_cmds():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="GATEWAYS", callback_data="cmds:gateways", style="primary"),
            InlineKeyboardButton(text="TOOLS", callback_data="cmds:tools", style="primary")
        ],
        [InlineKeyboardButton(text="EXIT", callback_data="st:exit", style="danger")]
    ])


def kb_gateways():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="AUTH", callback_data="gw:auth", style="success"),
            InlineKeyboardButton(text="CHARGE", callback_data="gw:charge", style="success")
        ],
        [InlineKeyboardButton(text="LOOKUP", callback_data="gw:lookup", style="success")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_auth_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHARGE", callback_data="gw:charge", style="success")],
        [InlineKeyboardButton(text="LOOKUP", callback_data="gw:lookup", style="success")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_charge_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="AUTH", callback_data="gw:auth", style="success")],
        [InlineKeyboardButton(text="LOOKUP", callback_data="gw:lookup", style="success")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_lookup_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="AUTH", callback_data="gw:auth", style="success")],
        [InlineKeyboardButton(text="CHARGE", callback_data="gw:charge", style="success")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_tools():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="BIN TOOLS", callback_data="tools:bin", style="primary"),
            InlineKeyboardButton(text="SCRAPER", callback_data="tools:scraper", style="primary")
        ],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_bin_tools():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="SCRAPER", callback_data="tools:scraper", style="primary")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


def kb_scraper():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BIN TOOLS", callback_data="tools:bin", style="primary")],
        [InlineKeyboardButton(text="HOME", callback_data="cmds:home", style="primary")]
    ])


# ========= Handlers =========

async def handle_start(message: types.Message):
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_start(message.from_user),
        reply_markup=kb_start(),
        parse_mode="HTML"
    )


async def handle_cmds(message: types.Message):
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_cmds(),
        reply_markup=kb_cmds(),
        parse_mode="HTML"
    )


async def _get_user_photo(bot, user_id: int):
    """جلب صورة المستخدم بأعلى دقة أو البانر كـ fallback"""
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            # photos.photos[0] هي قائمة بأحجام مختلفة لنفس الصورة، نأخذ آخر عنصر (الأعلى دقة)
            return photos.photos[0][-1].file_id
    except Exception:
        pass
    return BANNER_URL


async def handle_profile(message: types.Message):
    sub = await _sub_info(message.from_user.id)
    photo = await _get_user_photo(message.bot, message.from_user.id)
    await message.reply_photo(
        photo=photo,
        caption=cap_my_profile(message.from_user, sub),
        reply_markup=kb_profile_from_start(),
        parse_mode="HTML"
    )


# ========= Callbacks =========

async def on_callback_query(call: types.CallbackQuery):
    data = call.data
    user = call.from_user

    if data == "st:profile":
        sub = await _sub_info(user.id)
        photo = await _get_user_photo(call.bot, user.id)
        await _edit_media(
            call.message,
            photo_url=photo,
            caption=cap_my_profile(user, sub),
            reply_markup=kb_profile_from_start()
        )

    elif data == "st:about":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_about(),
            reply_markup=kb_about_from_start()
        )

    elif data == "st:home":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_start(user),
            reply_markup=kb_start()
        )

    elif data == "st:exit":
        await call.message.delete()

    elif data == "cmds:home":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_cmds(),
            reply_markup=kb_cmds()
        )

    elif data == "cmds:gateways":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_gateways_overview(),
            reply_markup=kb_gateways()
        )

    elif data == "gw:auth":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_auth_gates(),
            reply_markup=kb_auth_gates()
        )

    elif data == "gw:charge":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_charge_gates(),
            reply_markup=kb_charge_gates()
        )

    elif data == "gw:lookup":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_lookup_gates(),
            reply_markup=kb_lookup_gates()
        )

    elif data == "cmds:tools":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_tools(),
            reply_markup=kb_tools()
        )

    elif data == "tools:bin":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_cc_generator(),
            reply_markup=kb_bin_tools()
        )

    elif data == "tools:scraper":
        await _edit_media(
            call.message,
            photo_url=BANNER_URL,
            caption=cap_cc_scraper(),
            reply_markup=kb_scraper()
        )

    await call.answer()


# ========= Logic Helper =========

async def _edit_media(message: types.Message, photo_url: str, caption: str, reply_markup=None):
    with contextlib.suppress(Exception):
        await message.edit_media(
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode="HTML"),
            reply_markup=reply_markup
        )
