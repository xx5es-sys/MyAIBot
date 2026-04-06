from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_counters_for_gate(gate_type, session):
    """
    Returns the appropriate counters based on gate type.
    - AUTH: APPROVED, DECLINED, CCN
    - CHARGE: CHARGE, APPROVED, DECLINED
    - 3DS/LOOKUP: OTP REQUEST, PASSED, REJECTED
    """
    if gate_type == "auth":
        return [
            ("APPROVED ✅", session.get("approved", 0), "success"),
            ("DECLINED ❌", session.get("declined", 0), "danger"),
            ("CCN ♻️", session.get("ccn", 0), "danger") # CCN is danger (red) per new rules
        ]
    elif gate_type == "charge":
        return [
            ("CHARGE 💰", session.get("charge", 0), "success"),
            ("APPROVED ✅", session.get("approved", 0), "success"),
            ("DECLINED ❌", session.get("declined", 0), "danger")
        ]
    elif gate_type == "lookup" or gate_type == "3ds":
        return [
            ("OTP REQUEST ✅", session.get("otp", 0), "success"),
            ("PASSED ✅", session.get("passed", 0), "success"),
            ("REJECTED ❌", session.get("rejected", 0), "danger")
        ]
    else:
        # Default fallback
        return [
            ("PASSED ✅", session.get("passed", 0), "success"),
            ("REJECTED ❌", session.get("rejected", 0), "danger")
        ]

def create_mass_keyboard(user_id, session):
    total = len(session["cards"])
    processed = session["processed"]
    progress = (processed / total * 100) if total > 0 else 0
    gate_type = session.get("gate_type", "auth")
    status = session.get("status", "processing")
    
    buttons = []
    
    if status == "processing":
        # Full dashboard visible
        buttons.append([InlineKeyboardButton(text=f"𝙏𝙊𝙏𝘼𝙇 🌪️: [ {total} ]", callback_data="mass_info", style="primary")])
        buttons.append([InlineKeyboardButton(text=f"𝙋𝙍𝙊𝙂𝙍𝙀𝙎𝙎 🥷🏻: [ {progress:.2f}% ]", callback_data="mass_info", style="primary")])
        
        counters = get_counters_for_gate(gate_type, session)
        for label, value, style in counters:
            buttons.append([InlineKeyboardButton(text=f"{label}: [ {value} ]", callback_data="mass_info", style=style)])
        
        # UNKNOWN is danger (red) per new rules
        buttons.append([InlineKeyboardButton(text=f"𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓: [ {session.get('unknown', 0)} ]", callback_data="mass_info", style="danger")])
        
        # Current Item & Last Result
        current_item = session.get("current_item", "-")
        last_result = session.get("last_result", "-")
        buttons.append([InlineKeyboardButton(text=f"𝘾𝙐𝙍𝙍𝙀𝙉𝙏: [ {current_item[:30]} ]", callback_data="mass_info")])
        buttons.append([InlineKeyboardButton(text=f"𝙇𝘼𝙎𝙏 𝙍𝙀𝙎𝙐𝙇𝙏: [ {last_result[:30]} ]", callback_data="mass_info")])
        
        # BIND counter
        buttons.append([InlineKeyboardButton(text=f"𝘽𝙄𝙉𝘿 🚫: [ {session.get('bind', 0)} ]", callback_data="mass_info", style="danger")])
        
        # STOP button: no style (no color)
        buttons.append([InlineKeyboardButton(text="[ STOP ]", callback_data="mass:stop")])
        
    elif status == "paused":
        # Dashboard hidden, only control buttons
        buttons.append([InlineKeyboardButton(text="𝙍𝙀𝙎𝙐𝙈𝙀 🪢", callback_data="mass:resume", style="success")])
        buttons.append([InlineKeyboardButton(text="𝙉𝙀𝙒 𝙁𝙄𝙇𝙀 🪐", callback_data="mass:new_file", style="primary")])
        buttons.append([InlineKeyboardButton(text="CANCEL ❌", callback_data="mass:cancel", style="danger")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

import aiohttp
import ssl
import asyncio
import random

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
        "bank": "Unknown Bank", "country": "Unknown",
        "country_flag": "🌍", "blacklisted": False
    }
