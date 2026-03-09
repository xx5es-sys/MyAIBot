from aiogram import Bot, types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
import json
import re
from config import API_TOKEN, Admin
import os
import aiofiles
import premium_util
from branding import apply_branding

admin_router = Router()

# ===========================
# Premium JSON File Handling
# ===========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREMIUM_FILE_PATH = os.path.join(BASE_DIR, "premium.json")


async def ensure_premium_file():
    if not os.path.exists(PREMIUM_FILE_PATH):
        default_data = {"premium_users": []}
        try:
            async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
                await file.write(json.dumps(default_data, indent=2, ensure_ascii=False))
        except PermissionError as e:
            print(f"PermissionError: Could not create 'premium.json'. Error: {e}")
            raise
        return

    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "r", encoding="utf-8") as file:
            text = await file.read()
        if not text.strip():
            raise json.JSONDecodeError("Empty file", "", 0)
        json.loads(text)
    except (json.JSONDecodeError, FileNotFoundError):
        default_data = {"premium_users": []}
        try:
            async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
                await file.write(json.dumps(default_data, indent=2, ensure_ascii=False))
        except PermissionError as e:
            print(f"PermissionError: Could not re-init 'premium.json'. Error: {e}")
            raise


async def load_premium_data():
    await ensure_premium_file()
    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "r", encoding="utf-8") as file:
            text = await file.read()
            return json.loads(text)
    except Exception as e:
        print(f"Error loading premium.json: {e}")
        return {"premium_users": []}


async def save_premium_data(data):
    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
            await file.write(json.dumps(data, indent=2, ensure_ascii=False))
    except PermissionError as e:
        print(f"PermissionError: Could not save 'premium.json'. Error: {e}")
        raise


# ===========================
# FSM States
# ===========================

class AdminActions(StatesGroup):
    authorized = State()
    waiting_for_duration = State()
    waiting_for_unit = State()
    waiting_for_user_id = State()
    waiting_for_user_id_remove = State()
    waiting_for_credits_amount = State()
    waiting_for_credits_user_id = State()
    waiting_for_unlimited_user_id = State()
    waiting_for_bin_add = State()
    waiting_for_bin_remove = State()


# ===========================
# Admin Menu
# ===========================

@admin_router.message(F.text == "/adm")
async def admin_commands(message: types.Message, state: FSMContext):
    if message.from_user.id == Admin:
        await state.set_state(AdminActions.authorized)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Add Time-Based Premium", callback_data="add_premium", style="success")],
            [InlineKeyboardButton(text="💰 Add Credits", callback_data="add_credits", style="success")],
            [InlineKeyboardButton(text="♾️ Set Unlimited", callback_data="set_unlimited", style="success")],
            [InlineKeyboardButton(text="👥 View Premium Users", callback_data="view_premium", style="primary")],
            [InlineKeyboardButton(text="❌ Remove Premium User", callback_data="remove_premium", style="danger")],
            [
                InlineKeyboardButton(text="🚫 Block BIN", callback_data="block_bin", style="danger"),
                InlineKeyboardButton(text="✅ Unblock BIN", callback_data="unblock_bin", style="success")
            ],
            [InlineKeyboardButton(text="📋 List Blocked BINs", callback_data="list_bins", style="primary")],
        ])
        await message.reply(apply_branding("Admin Menu:"), reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.reply(apply_branding("You are not authorized to access this command."), parse_mode="HTML")
        await state.clear()


# ===========================
# Time-Based Premium
# ===========================

@admin_router.callback_query(F.data == "add_premium")
async def process_add_premium(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Please send the subscription duration in number of minutes or days or hours."), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_duration)


@admin_router.message(AdminActions.waiting_for_duration)
async def process_duration(message: types.Message, state: FSMContext):
    match = re.match(r"(\d+)\s*(m|minute|minutes|h|hour|hours|d|day|days)", message.text.strip().lower())
    if match:
        duration = int(match.group(1))
        unit = match.group(2)
        if "minute" in unit or "m" in unit:
            total_seconds = duration * 60
        elif "hour" in unit or "h" in unit:
            total_seconds = duration * 3600
        elif "d" in unit or "day" in unit:
            total_seconds = duration * 86400
        await state.update_data(duration=total_seconds, unit=unit)
        await message.reply(apply_branding("Enter the user ID to add to premium."), parse_mode="HTML")
        await state.set_state(AdminActions.waiting_for_user_id)
    else:
        await message.reply(
            apply_branding("Invalid format. Please enter the duration as '(number) minutes', '(number) hours', or '(number) days'."),
            parse_mode="HTML"
        )


@admin_router.message(AdminActions.waiting_for_user_id)
async def add_premium_user(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    bot = message.bot
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except Exception:
            await message.reply(apply_branding("No chat found with this user."), parse_mode="HTML")
            return

        data_state = await state.get_data()
        total_seconds = data_state.get("duration")
        subscription_duration = timedelta(seconds=total_seconds)
        now = datetime.utcnow()
        expires_at = now + subscription_duration
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        formatted_expires_at = expires_at.strftime("%Y-%m-%d %H:%M:%S")

        data = await load_premium_data()

        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["expires"] = formatted_expires_at
                if not user_rec.get("since"):
                    user_rec["since"] = formatted_now
                break

        if not user_found:
            new_user = {
                "user_id": user_id,
                "username": username,
                "credits": 0,
                "unlimited": False,
                "since": formatted_now,
                "expires": formatted_expires_at,
                "last_chk": "—",
            }
            data.setdefault("premium_users", []).append(new_user)

        await save_premium_data(data)

        await message.reply(
            apply_branding(f"User <b>@{username}</b> added successfully to <b>premium</b>.\n"
            f"Added on: <b>{formatted_now}</b>\n"
            f"Subscription will expire on: <b>{formatted_expires_at}</b>"),
            parse_mode="HTML",
        )

        try:
            await bot.send_message(
                user_id,
                apply_branding(f"<b>Congratulations</b> 🥳 <b>@{username}</b>, you are now a <b>premium</b> user!\n"
                f"Valid until: <b>{formatted_expires_at}</b>\n"
                f"💡 <b>Remember,</b> you can always check your <b>status</b> using /sup"),
                parse_mode="HTML"
            )
        except Exception:
            pass

        await state.clear()
    else:
        await message.reply(apply_branding("Hmm... That doesn't look right. Please send a numeric user ID."), parse_mode="HTML")


# ===========================
# Credits Management
# ===========================

@admin_router.callback_query(F.data == "add_credits")
async def process_add_credits(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Enter the amount of credits to add:"), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_credits_amount)


@admin_router.message(AdminActions.waiting_for_credits_amount)
async def process_credits_amount(message: types.Message, state: FSMContext):
    amount_text = message.text.strip()
    if amount_text.isdigit():
        amount = int(amount_text)
        await state.update_data(credits_amount=amount)
        await message.reply(apply_branding("Enter the user ID to add credits to:"), parse_mode="HTML")
        await state.set_state(AdminActions.waiting_for_credits_user_id)
    else:
        await message.reply(apply_branding("Invalid amount. Please enter a numeric value."), parse_mode="HTML")


@admin_router.message(AdminActions.waiting_for_credits_user_id)
async def process_credits_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    bot = message.bot
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except Exception:
            await message.reply(apply_branding("No chat found with this user."), parse_mode="HTML")
            return

        data_state = await state.get_data()
        amount = data_state.get("credits_amount", 0)

        data = await load_premium_data()

        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["credits"] = user_rec.get("credits", 0) + amount
                break

        if not user_found:
            new_user = {
                "user_id": user_id,
                "username": username,
                "credits": amount,
                "unlimited": False,
                "since": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "expires": "—",
                "last_chk": "—",
            }
            data.setdefault("premium_users", []).append(new_user)

        await save_premium_data(data)

        await message.reply(
            apply_branding(f"✅ Added <b>{amount}</b> credits to user <b>@{username}</b> (ID: {user_id})"),
            parse_mode="HTML",
        )

        try:
            await bot.send_message(
                user_id,
                apply_branding(f"🎉 You have received <b>{amount}</b> credits!\nCheck your balance with /sup"),
                parse_mode="HTML",
            )
        except Exception:
            pass

        await state.clear()
    else:
        await message.reply(apply_branding("Hmm... That doesn't look right. Please send a numeric user ID."), parse_mode="HTML")


# ===========================
# BIN Blacklist Management
# ===========================

@admin_router.callback_query(F.data == "block_bin")
async def process_block_bin(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Enter the 6-digit BIN to block:"), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_bin_add)

@admin_router.message(AdminActions.waiting_for_bin_add)
async def add_bin_handler(message: types.Message, state: FSMContext):
    bin_num = message.text.strip()
    if bin_num.isdigit() and len(bin_num) >= 6:
        from db import add_bin_to_blacklist
        if add_bin_to_blacklist(bin_num[:6]):
            await message.reply(apply_branding(f"✅ BIN <code>{bin_num[:6]}</code> has been blocked."), parse_mode="HTML")
        else:
            await message.reply(apply_branding(f"ℹ️ BIN <code>{bin_num[:6]}</code> is already blocked."), parse_mode="HTML")
        await state.clear()
    else:
        await message.reply(apply_branding("❌ Invalid BIN. Please enter at least 6 digits."), parse_mode="HTML")

@admin_router.callback_query(F.data == "unblock_bin")
async def process_unblock_bin(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Enter the 6-digit BIN to unblock:"), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_bin_remove)

@admin_router.message(AdminActions.waiting_for_bin_remove)
async def remove_bin_handler(message: types.Message, state: FSMContext):
    bin_num = message.text.strip()
    if bin_num.isdigit() and len(bin_num) >= 6:
        from db import remove_bin_from_blacklist
        if remove_bin_from_blacklist(bin_num[:6]):
            await message.reply(apply_branding(f"✅ BIN <code>{bin_num[:6]}</code> has been unblocked."), parse_mode="HTML")
        else:
            await message.reply(apply_branding(f"ℹ️ BIN <code>{bin_num[:6]}</code> was not blocked."), parse_mode="HTML")
        await state.clear()
    else:
        await message.reply(apply_branding("❌ Invalid BIN. Please enter at least 6 digits."), parse_mode="HTML")

@admin_router.callback_query(F.data == "list_bins")
async def list_bins_handler(call: CallbackQuery):
    from db import load_bin_blacklist
    bins = load_bin_blacklist()
    if bins:
        bin_list = "\n".join([f"<code>{b}</code>" for b in bins])
        await call.message.edit_text(apply_branding(f"📋 <b>Blocked BINs:</b>\n\n{bin_list}"), parse_mode="HTML")
    else:
        await call.message.edit_text(apply_branding("📋 No BINs are currently blocked."), parse_mode="HTML")
    await call.answer()

# ===========================
# Unlimited Access
# ===========================

@admin_router.callback_query(F.data == "set_unlimited")
async def process_set_unlimited(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Enter the user ID to toggle unlimited access:"), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_unlimited_user_id)


@admin_router.message(AdminActions.waiting_for_unlimited_user_id)
async def process_unlimited_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        data = await load_premium_data()
        user_found = False
        new_status = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["unlimited"] = not user_rec.get("unlimited", False)
                new_status = user_rec["unlimited"]
                break

        if not user_found:
            await message.reply(apply_branding("User not found in premium list. Please add them as premium first."), parse_mode="HTML")
            return

        await save_premium_data(data)
        status_text = "ENABLED" if new_status else "DISABLED"
        await message.reply(apply_branding(f"✅ Unlimited access <b>{status_text}</b> for user ID: {user_id}"), parse_mode="HTML")
        await state.clear()
    else:
        await message.reply(apply_branding("Please send a numeric user ID."), parse_mode="HTML")


# ===========================
# View / Remove Users
# ===========================

@admin_router.callback_query(F.data == "view_premium")
async def view_premium_users(call: CallbackQuery):
    data = await load_premium_data()
    users = data.get("premium_users", [])
    if not users:
        await call.message.edit_text(apply_branding("No premium users found."), parse_mode="HTML")
    else:
        text = "<b>Premium Users:</b>\n\n"
        for u in users:
            text += f"👤 <b>@{u['username']}</b> (<code>{u['user_id']}</code>)\n"
            text += f"   💰 Credits: {u.get('credits', 0)} | ♾️ Unlimited: {u.get('unlimited', False)}\n"
            text += f"   📅 Expires: {u.get('expires', '—')}\n\n"
        
        # Split text if too long
        if len(text) > 4000:
            await call.message.edit_text(apply_branding("Too many users to display here."), parse_mode="HTML")
        else:
            await call.message.edit_text(apply_branding(text), parse_mode="HTML")
    await call.answer()


@admin_router.callback_query(F.data == "remove_premium")
async def process_remove_premium(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(apply_branding("Enter the user ID to remove from premium:"), parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_user_id_remove)


@admin_router.message(AdminActions.waiting_for_user_id_remove)
async def remove_premium_user(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        data = await load_premium_data()
        original_count = len(data.get("premium_users", []))
        data["premium_users"] = [u for u in data.get("premium_users", []) if str(u.get("user_id")) != user_id]
        
        if len(data["premium_users"]) < original_count:
            await save_premium_data(data)
            await message.reply(apply_branding(f"✅ User ID {user_id} removed from premium."), parse_mode="HTML")
        else:
            await message.reply(apply_branding("User ID not found."), parse_mode="HTML")
        await state.clear()
    else:
        await message.reply(apply_branding("Please send a numeric user ID."), parse_mode="HTML")
