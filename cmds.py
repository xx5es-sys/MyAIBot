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

# ========= Config =========
BANNER_URL = "https://t.me/i5ese/347"
BRAND_ANCHOR = '<a href="https://t.me/lgnisXBot">𝖨𝖦𝖭𝖨𝖲𝖷</a>'
DOT_ANCHOR = '<a href="https://t.me/lgnisXBot">•</a>'
BOT_LINK = f"{DOT_ANCHOR} https://t.me/lgnisXBot"

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
    return (
        f"{DOT_ANCHOR} Hello  𓏺 {first_name}\n"
        "\n"
        f"{DOT_ANCHOR} I'm {BRAND_ANCHOR}↯. A Multi Functional Bot With Many Tools and Checker Gateways.\n"
        f"{DOT_ANCHOR} Press /cmds To Know My Features\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_my_profile(u: types.User, sub: dict) -> str:
    uname = f"@{u.username}" if u.username else "—"
    profile_link = f'<a href="tg://user?id={u.id}">Click Here</a>'
    return (
        f"{DOT_ANCHOR} み {BRAND_ANCHOR} — User Information\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} UID        : {u.id}\n"
        f"{DOT_ANCHOR} Name       : {u.first_name}\n"
        f"{DOT_ANCHOR} Username   : {uname}\n"
        f"{DOT_ANCHOR} Profile    : {profile_link}\n"
        "\n"
        f"{DOT_ANCHOR} Subscription Information\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} Status     : {sub['tier']}\n"
        f"{DOT_ANCHOR} Credits    : {sub['credits']}\n"
        f"{DOT_ANCHOR} Validity   : {sub['valid_until']}\n"
        f"{DOT_ANCHOR} Last Check : {sub['last_chk']}\n"
        "\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} /Buy VIP Subscription to Unlock All Features.\n"
        f"{DOT_ANCHOR} DeveBy ↝O.T\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_about() -> str:
    return (
        f"{DOT_ANCHOR} み  {BRAND_ANCHOR}↯ BreakDown !\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} Language ⌁ Python x Aiogram\n"
        f"{DOT_ANCHOR} Version    ⌁ v1.1\n"
        f"{DOT_ANCHOR} Hosting      ⌁ VPS\n"
        f"{DOT_ANCHOR} Developer     ⌁ O.T Dev\n"
        f"{DOT_ANCHOR} Updated       ⌁ 2026\n"
        "\n"
        f"{DOT_ANCHOR} Community\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} Official Channel\n"
        f"{DOT_ANCHOR} Support Chat\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_cmds() -> str:
    return (
        f"{DOT_ANCHOR} {BRAND_ANCHOR} — Commands Overview\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} Gateways\n"
        f"{DOT_ANCHOR} • Auth\n"
        f"{DOT_ANCHOR} • Charge\n"
        f"{DOT_ANCHOR} • LookUp\n"
        "\n"
        f"{DOT_ANCHOR} Tools\n"
        f"{DOT_ANCHOR} • CC Generator\n"
        f"{DOT_ANCHOR} • CC Scraper\n"
        "\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} ↯   Click Below to View Full Details  ↯\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_gateways_overview() -> str:
    return (
        f"{DOT_ANCHOR} Overview Section of {BRAND_ANCHOR}\n"
        "\n"
        f"{DOT_ANCHOR} • Auth     ⌁  3 Gates\n"
        f"{DOT_ANCHOR} • Charge   ⌁  4 Gates\n"
        f"{DOT_ANCHOR} • LookUp   ⌁  4 Gates\n"
        "\n"
        f"{DOT_ANCHOR} ↯  Check Below to View Available Gates.\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_auth_gates() -> str:
    return (
        f"{DOT_ANCHOR} み {BRAND_ANCHOR} AUTH\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Stripe Auth  ( /au )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Stripe AUTH\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Braintree Auth  ( /ba )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Braintree Auth\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Square Auth  ( /sq )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Square Auth\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_charge_gates() -> str:
    return (
        f"{DOT_ANCHOR} み {BRAND_ANCHOR} CHARGE\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » PayPal Cvv  ( /Pv )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  »  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  PayPal\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Square charge  ( /Sh )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  »  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Square charge\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Azathoth  ( /az )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  »  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Authorize.Net [AIM]\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Stripe Charge  ( /sc )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  »  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Stripe v1\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_lookup_gates() -> str:
    return (
        f"{DOT_ANCHOR} み {BRAND_ANCHOR} LookUp\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Verify Secure  ( /vbv )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Braintree 3DS\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Global 3DS  ( /G3 )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Global payment\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Global Passed  ( /GP )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Global payment\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name » Verify Passed  ( /BP )\n"
        f"{DOT_ANCHOR} • Status   ⌁  PREMIUM  ⌁  ON\n"
        f"{DOT_ANCHOR} • Gateway  ⌁  Braintree Passed\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_tools() -> str:
    return (
        f"{DOT_ANCHOR} {BRAND_ANCHOR} — Tools Overview\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} • CC Generator\n"
        f"{DOT_ANCHOR} • CC Scraper\n"
        "\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} ↯   Click Below to View Full Details  ↯\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_cc_generator() -> str:
    return (
        f"{DOT_ANCHOR} あ {BRAND_ANCHOR} Binning Tools あ\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name  Bin Checker\n"
        f"{DOT_ANCHOR} • Format  » /bin bin_number\n"
        f"{DOT_ANCHOR} • Status  »  ACTIVE  ✅\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name  Card Generator\n"
        f"{DOT_ANCHOR} • Format  » /gen bin\n"
        f"{DOT_ANCHOR} • Status  »  ACTIVE  ✅\n"
        "\n"
        f"{DOT_ANCHOR} ↯ Name  Card Generator\n"
        f"{DOT_ANCHOR} • Format  » /mgen bin [Number card]\n"
        f"{DOT_ANCHOR} • Status  »  ACTIVE  ✅\n"
        "\n"
        f"{BOT_LINK}"
    )


def cap_cc_scraper() -> str:
    return (
        f"{DOT_ANCHOR} COMING SOON\n"
        "\n"
        f"{BOT_LINK}"
    )


# ========= Keyboards (aiogram 3.x style) =========

def kb_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="MY PROFILE", callback_data="st:profile"),
            InlineKeyboardButton(text="ABOUT", callback_data="st:about")
        ],
        [InlineKeyboardButton(text="EXIT", callback_data="st:exit")]
    ])


def kb_profile_from_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="st:home")]
    ])


def kb_about_from_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="st:home")]
    ])


def kb_cmds():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="GATEWAYS", callback_data="cmds:gateways"),
            InlineKeyboardButton(text="TOOLS", callback_data="cmds:tools")
        ],
        [InlineKeyboardButton(text="MY PROFILE", callback_data="cmds:profile")],
        [InlineKeyboardButton(text="EXIT", callback_data="cmds:exit")]
    ])


def kb_gateways():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="AUTH", callback_data="gw:auth"),
            InlineKeyboardButton(text="CHARGE", callback_data="gw:charge")
        ],
        [InlineKeyboardButton(text="LOOKUP", callback_data="gw:lookup")],
        [InlineKeyboardButton(text="BACK", callback_data="cmds:home")]
    ])


def kb_auth_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:gateways")]
    ])


def kb_charge_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:gateways")]
    ])


def kb_lookup_gates():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:gateways")]
    ])


def kb_tools():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CC GENERATOR", callback_data="tools:gen"),
            InlineKeyboardButton(text="CC SCRAPER", callback_data="tools:scrape")
        ],
        [InlineKeyboardButton(text="BACK", callback_data="cmds:home")]
    ])


def kb_tool_gen():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:tools")]
    ])


def kb_tool_scrape():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:tools")]
    ])


def kb_profile_from_cmds():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BACK", callback_data="cmds:home")]
    ])


# ========= Handlers =========

async def start_command(message: types.Message):
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_start(message.from_user.first_name),
        reply_markup=kb_start(),
        parse_mode="HTML"
    )


async def cmds_entry(message: types.Message):
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_cmds(),
        reply_markup=kb_cmds(),
        parse_mode="HTML"
    )


async def sup_command(message: types.Message):
    sub = await _sub_info(message.from_user.id)
    await message.reply_photo(
        photo=BANNER_URL,
        caption=cap_my_profile(message.from_user, sub),
        parse_mode="HTML"
    )


# ========= Callback Handlers =========

async def start_callbacks(call: types.CallbackQuery):
    data = call.data.split(":")[-1]

    if data == "home":
        await call.message.edit_caption(
            caption=cap_start(call.from_user.first_name),
            reply_markup=kb_start(),
            parse_mode="HTML"
        )
    elif data == "profile":
        sub = await _sub_info(call.from_user.id)
        await call.message.edit_caption(
            caption=cap_my_profile(call.from_user, sub),
            reply_markup=kb_profile_from_start(),
            parse_mode="HTML"
        )
    elif data == "about":
        await call.message.edit_caption(
            caption=cap_about(),
            reply_markup=kb_about_from_start(),
            parse_mode="HTML"
        )
    elif data == "exit":
        with contextlib.suppress(Exception):
            await call.message.delete()
    await call.answer()


async def cmds_callbacks(call: types.CallbackQuery):
    data = call.data.split(":")[-1]

    if data == "home":
        await call.message.edit_caption(caption=cap_cmds(), reply_markup=kb_cmds(), parse_mode="HTML")
    elif data == "gateways":
        await call.message.edit_caption(caption=cap_gateways_overview(), reply_markup=kb_gateways(), parse_mode="HTML")
    elif data == "tools":
        await call.message.edit_caption(caption=cap_tools(), reply_markup=kb_tools(), parse_mode="HTML")
    elif data == "profile":
        sub = await _sub_info(call.from_user.id)
        await call.message.edit_caption(
            caption=cap_my_profile(call.from_user, sub),
            reply_markup=kb_profile_from_cmds(),
            parse_mode="HTML"
        )
    elif data == "exit":
        with contextlib.suppress(Exception):
            await call.message.delete()

    # Gateways Sub-Menus
    elif data == "auth":
        await call.message.edit_caption(caption=cap_auth_gates(), reply_markup=kb_auth_gates(), parse_mode="HTML")
    elif data == "charge":
        await call.message.edit_caption(caption=cap_charge_gates(), reply_markup=kb_charge_gates(), parse_mode="HTML")
    elif data == "lookup":
        await call.message.edit_caption(caption=cap_lookup_gates(), reply_markup=kb_lookup_gates(), parse_mode="HTML")

    # Tools Sub-Menus
    elif data == "gen":
        await call.message.edit_caption(caption=cap_cc_generator(), reply_markup=kb_tool_gen(), parse_mode="HTML")
    elif data == "scrape":
        await call.message.edit_caption(caption=cap_cc_scraper(), reply_markup=kb_tool_scrape(), parse_mode="HTML")

    await call.answer()
