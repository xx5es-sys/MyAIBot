# premium_util.py

"""
Centralized Credit-Based Premium System
Supports: Admin, Unlimited, Credit Premium, Free
All operations use premium.json (lowercase, case-sensitive)
"""

import json
import asyncio
from datetime import datetime, timezone
import aiofiles
from aiogram.types import Message
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
# import config

bot = Bot(
    token='7830034663:AAHcEFO9dHuQRPdRx93sKwYt2TzWGBvev70',
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Thread-safe lock for file operations
_file_lock = asyncio.Lock()

# File path (case-sensitive)
PREMIUM_FILE = "premium.json"

# ===========================
# Internal Helpers
# ===========================

async def _read_data():
    """Read premium.json with defaults."""
    try:
        async with aiofiles.open(PREMIUM_FILE, 'r', encoding='utf-8') as f:
            text = await f.read()
            data = json.loads(text)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"premium_users": []}

async def _write_data(data):
    """Write premium.json atomically."""
    async with aiofiles.open(PREMIUM_FILE, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

def _utc_now():
    """Return current UTC time as string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def _format_display_time(utc_str):
    """Convert UTC string to 12h AM/PM format + MM/DD/YYYY UTC."""
    if not utc_str or utc_str == "—":
        return "—"
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%I:%M %p » %m/%d/%Y UTC")
    except:
        return utc_str

def _format_date(utc_str):
    """Convert UTC string to MM/DD/YYYY UTC."""
    if not utc_str:
        return "—"
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m/%d/%Y UTC")
    except:
        return utc_str

# ===========================
# Core Functions
# ===========================

async def get_record(user_id: str):
    """
    Get user record from premium.json with defaults.
    Returns: dict with {user_id, username, credits, unlimited, since, expires, last_chk}
    """
    async with _file_lock:
        data = await _read_data()
        for user in data.get("premium_users", []):
            if str(user.get("user_id")) == str(user_id):
                # Ensure new fields exist
                user.setdefault("credits", 0)
                user.setdefault("unlimited", False)
                user.setdefault("last_chk", "—")
                return user
        # Return default record for non-premium users
        return {
            "user_id": str(user_id),
            "username": "—",
            "credits": 0,
            "unlimited": False,
            "since": "—",
            "expires": "—",
            "last_chk": "—"
        }

async def is_premium(user_id: str):
    """
    Check if user has active premium.
    Returns True if: unlimited OR credits>0 OR valid time-based subscription
    """
    record = await get_record(user_id)
    
    # Check unlimited
    if record.get("unlimited", False):
        return True
    
    # Check credits
    if record.get("credits", 0) > 0:
        return True
    
    # Check time-based subscription
    expires_str = record.get("expires")
    if expires_str and expires_str != "—":
        try:
            expires_time = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if now < expires_time:
                return True
        except:
            pass
    
    return False

async def is_unlimited(user_id: str):
    """Check if user has unlimited subscription."""
    record = await get_record(user_id)
    return record.get("unlimited", False)

async def consume_for_single(user_id: str):
    """
    Consume 1 credit before single check execution.
    Returns: (bool, str) - (success, message)
    """
    # Check if Admin
    if str(user_id) == str(608548316):
        return (True, "admin")
    
    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])
        
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                # Check unlimited
                if user.get("unlimited", False):
                    return (True, "unlimited")
                
                # Check credits
                credits = user.get("credits", 0)
                if credits > 0:
                    user["credits"] = credits - 1
                    await _write_data(data)
                    return (True, "consumed")
                else:
                    return (False, "no_credits")
        
        # User not found in premium list
        return (False, "no_credits")

async def refund_credit(user_id: str, amount: int = 1, reason: str = "transient_error"):
    """
    Refund credits for transient errors only.
    Valid reasons: Timeout, Network, TLS, 5xx errors
    """
    # Don't refund for Admin or Unlimited
    if str(user_id) == str(608548316):
        return
    
    if await is_unlimited(user_id):
        return
    
    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])
        
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                user["credits"] = user.get("credits", 0) + amount
                await _write_data(data)
                return

async def can_start_mass(user_id: str):
    """
    Check if user can start mass check session.
    Returns True if: Admin OR unlimited OR credits>0
    """
    if str(user_id) == str(608548316):
        return True
    
    if await is_unlimited(user_id):
        return True
    
    record = await get_record(user_id)
    return record.get("credits", 0) > 0

async def update_last_chk(user_id: str):
    """Update last_chk timestamp after successful check."""
    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])
        
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                user["last_chk"] = _utc_now()
                await _write_data(data)
                return

# ===========================
# Administrative Functions
# ===========================

async def add_credits(user_id: str, amount: int):
    """Add credits to user account."""
    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])
        
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                user["credits"] = max(0, user.get("credits", 0) + amount)
                await _write_data(data)
                return

async def add_credits(user_id: str, amount: int, username: str = None):
    """Add credits to user account.
    - If user exists in premium_users: increase their credits.
    - If user does NOT exist: create a new premium record with basic defaults.
    """
    if amount == 0:
        return

    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])

        target = None
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                target = user
                break

        if target is None:
            # Create a new record for this user
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            target = {
                "user_id": str(user_id),
                "username": username or "—",
                "credits": 0,
                "unlimited": False,
                "since": now,
                "expires": "—",
                "last_chk": "—",
            }
            users.append(target)
            data["premium_users"] = users

        # Safely update credits
        target["credits"] = max(0, int(target.get("credits", 0)) + int(amount))

        await _write_data(data)


async def set_unlimited(user_id: str, flag: bool):
    """Enable or disable unlimited subscription."""
    async with _file_lock:
        data = await _read_data()
        users = data.get("premium_users", [])
        
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                user["unlimited"] = flag
                if flag:
                    # When setting unlimited, set credits to 0
                    user["credits"] = 0
                await _write_data(data)
                return

# ===========================
# Display Function
# ===========================

async def send_premium_data(message: Message):
    """
    Send premium subscription details in unified format.
    Format:
    み Subscription Information
    ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
    • Status       {ADMIN|UNLIMITED|PREMIUM|FREE}
    • Credits      {∞|N|0}
    • Validity     {Unlimited|MM/DD/YYYY UTC|No Expiry|No Subscription UTC}
    • Last Chk     {HH:MM AM/PM » MM/DD/YYYY UTC}
    """
    user_id = str(message.from_user.id)
    
    # Check if Admin
    if str(user_id) == str(608548316):
        msg = (
            "み Subscription Information\n"
            "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
            "• Status       ADMIN\n"
            "• Credits      ∞\n"
            "• Validity     Unlimited\n"
            "• Last Chk     —\n"
        )
        await message.reply(msg, parse_mode='HTML')
        return
    
    record = await get_record(user_id)
    
    # Determine Status
    if record.get("unlimited", False):
        status = "UNLIMITED"
    elif record.get("credits", 0) > 0:
        status = "PREMIUM"
    else:
        # Check time-based subscription
        expires_str = record.get("expires")
        if expires_str and expires_str != "—":
            try:
                expires_time = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if now < expires_time:
                    status = "PREMIUM"
                else:
                    status = "FREE"
            except:
                status = "FREE"
        else:
            status = "FREE"
    
    # Determine Credits
    if record.get("unlimited", False):
        credits_display = "∞"
    else:
        credits_display = str(record.get("credits", 0))
    
    # Determine Validity
    if record.get("unlimited", False):
        validity = "Unlimited"
    elif record.get("credits", 0) > 0 and (not record.get("expires") or record.get("expires") == "—"):
        validity = "No Expiry"
    elif record.get("expires") and record.get("expires") != "—":
        validity = _format_date(record.get("expires"))
    else:
        validity = "No Subscription UTC"
    
    # Determine Last Chk
    last_chk = _format_display_time(record.get("last_chk", "—"))
    
    msg = (
        "み Subscription Information\n"
        "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"• Status       {status}\n"
        f"• Credits      {credits_display}\n"
        f"• Validity     {validity}\n"
        f"• Last Chk     {last_chk}\n"
    )
    
    await message.reply(msg, parse_mode='HTML')

# ===========================
# Subscription Checker (Legacy Support)
# ===========================

async def check_subscriptions():
    """
    Check and notify expired time-based subscriptions.
    This maintains backward compatibility with old system.
    """
    async with _file_lock:
        data = await _read_data()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        active_users = []
        expired_users = []
        
        for user in data.get("premium_users", []):
            expires_str = user.get("expires")
            
            # Skip if no expiry date (credit-only or unlimited users)
            if not expires_str or expires_str == "—":
                active_users.append(user)
                continue
            
            try:
                expires_time = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                if expires_time > now:
                    active_users.append(user)
                else:
                    # Only mark as expired if they have no credits and not unlimited
                    if user.get("credits", 0) == 0 and not user.get("unlimited", False):
                        expired_users.append(user)
                    else:
                        active_users.append(user)
            except:
                active_users.append(user)
        
        if expired_users:
            data["premium_users"] = active_users
            await _write_data(data)
            
            for user in expired_users:
                try:
                    message_text = (
                        f"Hi @{user.get('username', 'User')} 👋, your <b>time-based subscription</b> has <b>expired!</b> "
                        f"To <b>reactivate</b>, please <b>contact</b> @Mustafa2l."
                    )
                    await bot.send_message(user["user_id"], message_text, parse_mode='HTML')
                except:
                    pass

