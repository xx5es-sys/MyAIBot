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
            ("CCN ♻️", session.get("ccn", 0), "success")
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
    
    buttons = [
        [InlineKeyboardButton(text=f"𝙏𝙊𝙏𝘼𝙇 🌪️: [ {total} ]", callback_data="mass_info", style="primary")],
        [InlineKeyboardButton(text=f"𝙋𝙍𝙊𝙂𝙍𝙀𝙎𝙎 🥷🏻: [ {progress:.2f}% ]", callback_data="mass_info", style="primary")]
    ]
    
    counters = get_counters_for_gate(gate_type, session)
    for label, value, style in counters:
        buttons.append([InlineKeyboardButton(text=f"{label}: [ {value} ]", callback_data="mass_info", style=style)])
    
    # Add UNKNOWN as primary (blue) per rules
    buttons.append([InlineKeyboardButton(text=f"𝙐𝙉𝙆𝙉𝙊𝙒𝙉 ❓: [ {session.get('unknown', 0)} ]", callback_data="mass_info", style="primary")])
    
    if session["status"] == "processing":
        # STOP button should be without style (no color)
        buttons.append([InlineKeyboardButton(text="[ STOP ]", callback_data="mass:stop")])
    elif session["status"] == "paused":
        buttons.append([InlineKeyboardButton(text="𝙍𝙀𝙎𝙐𝙈𝙀 🪢", callback_data="mass:resume", style="success")])
        buttons.append([InlineKeyboardButton(text="𝙉𝙀𝙒 𝙁𝙄𝙇𝙀 🪐", callback_data="mass:new_file", style="primary")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)
