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

def cap_start(first_name: str) -> str:
    return apply_branding(
        f"🌅Hello  𓏺 {first_name}\n\n"
        "I'm 𝖨𝖦𝖭𝖨𝖲𝖷. A Multi Functional Bot With Many Tools and Checker Gateways.\n"
        "Press /cmds To Know My Features"
    )


def cap_my_profile(u: types.User, sub: dict) -> str:
    uname = f"@{u.username}" if u.username else "—"
    profile_link = f'<a href="tg://user?id={u.id}">Click Here</a>'
    return apply_branding(
        "み 𝖨𝖦𝖭𝖨𝖲𝖷 — User Information\n"
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
        "<a href=\"http://t.me/IgnisXBot\">•</a> /Buy VIP Subscription to Unlock All Features.\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> DeveBy ↝𝖨𝖦𝖭𝖨𝖲𝖷"
    )


def cap_about() -> str:
    return apply_branding(
        "み  𝖨𝖦𝖭𝖨𝖲𝖷↯ BreakDown !\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "Language ⌁ Python x Aiogram\n"
        "Version    ⌁ v1.1\n"
        "Hosting      ⌁ VPS\n"
        "Developer     ⌁ 𝖨𝖦𝖭𝖨𝖲𝖷 Dev\n"
        "Updated       ⌁ 2026\n\n"
        "Community\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Official Channel\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a> Support Chat"
    )


def cap_cmds() -> str:
    return apply_branding(
        "𝖨𝖦𝖭𝖨𝖲𝖷 Bot — Commands Overview\n"
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
        "Overview Section of 𝖨𝖦𝖭𝖨𝖲𝖷 Bot\n\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Auth     ⌁  3 Gates\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  Charge   ⌁  4 Gates\n"
        "<a href=\"http://t.me/IgnisXBot\">•</a>  LookUp   ⌁  4 Gates\n\n"
        "↯  Check Below to View Available Gates."
    )


def cap_auth_gates() -> str:
    return apply_branding(
        "み 𝖨𝖦𝖭𝖨𝖲𝖷 Bot AUTH\n\n"
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
        "み 𝖨𝖦𝖭𝖨𝖲𝖷 Bot CHARGE\n\n"
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
        "み 𝖨𝖦𝖭𝖨𝖲𝖷 Bot LookUp\n\n"
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
        "𝖨𝖦𝖭𝖨𝖲𝖷 Bot — Tools Overview\n"
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
        caption=cap_start(message.from_user.first_name),
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


async def handle_profile(message: types.Message):
    sub = await _sub_info(message.from_user.id)
    await message.reply_photo(
        photo=BANNER_URL,
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
        await call.message.edit_caption(
            caption=cap_my_profile(user, sub),
            reply_markup=kb_profile_from_start(),
            parse_mode="HTML"
        )

    elif data == "st:about":
        await call.message.edit_caption(
            caption=cap_about(),
            reply_markup=kb_about_from_start(),
            parse_mode="HTML"
        )

    elif data == "st:home":
        await call.message.edit_caption(
            caption=cap_start(user.first_name),
            reply_markup=kb_start(),
            parse_mode="HTML"
        )

    elif data == "st:exit":
        await call.message.delete()

    elif data == "cmds:home":
        await call.message.edit_caption(
            caption=cap_cmds(),
            reply_markup=kb_cmds(),
            parse_mode="HTML"
        )

    elif data == "cmds:gateways":
        await call.message.edit_caption(
            caption=cap_gateways_overview(),
            reply_markup=kb_gateways(),
            parse_mode="HTML"
        )

    elif data == "gw:auth":
        await call.message.edit_caption(
            caption=cap_auth_gates(),
            reply_markup=kb_auth_gates(),
            parse_mode="HTML"
        )

    elif data == "gw:charge":
        await call.message.edit_caption(
            caption=cap_charge_gates(),
            reply_markup=kb_charge_gates(),
            parse_mode="HTML"
        )

    elif data == "gw:lookup":
        await call.message.edit_caption(
            caption=cap_lookup_gates(),
            reply_markup=kb_lookup_gates(),
            parse_mode="HTML"
        )

    elif data == "cmds:tools":
        await call.message.edit_caption(
            caption=cap_tools(),
            reply_markup=kb_tools(),
            parse_mode="HTML"
        )

    elif data == "tools:bin":
        await call.message.edit_caption(
            caption=cap_cc_generator(),
            reply_markup=kb_bin_tools(),
            parse_mode="HTML"
        )

    elif data == "tools:scraper":
        await call.message.edit_caption(
            caption=cap_cc_scraper(),
            reply_markup=kb_scraper(),
            parse_mode="HTML"
        )

    await call.answer()


# ========= Logic Helper =========

async def _edit_media(message: types.Message, photo_url: str, caption: str, reply_markup=None):
    with contextlib.suppress(Exception):
        await message.edit_media(
            media=InputMediaPhoto(media=photo_url, caption=caption, parse_mode="HTML"),
            reply_markup=reply_markup
        )
