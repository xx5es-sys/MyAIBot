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

admin_router = Router()

# ========= Config =========
DOT_ANCHOR = '<a href="http://t.me/IgnisXBot">•</a>'

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


# ===========================
# Admin Menu
# ===========================

@admin_router.message(F.text == "/adm")
async def admin_commands(message: types.Message, state: FSMContext):
    if message.from_user.id == Admin:
        await state.set_state(AdminActions.authorized)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Add Time-Based Premium", callback_data="add_premium")],
            [InlineKeyboardButton(text="Add Credits", callback_data="add_credits")],
            [InlineKeyboardButton(text="Set Unlimited", callback_data="set_unlimited")],
            [InlineKeyboardButton(text="View Premium Users", callback_data="view_premium")],
            [InlineKeyboardButton(text="Remove Premium User", callback_data="remove_premium")],
        ])
        await message.reply(f"{DOT_ANCHOR} <b>Admin Menu:</b>", reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ You are not authorized to access this command.", parse_mode="HTML")
        await state.clear()


# ===========================
# Time-Based Premium
# ===========================

@admin_router.callback_query(F.data == "add_premium")
async def process_add_premium(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f"{DOT_ANCHOR} Please send the subscription duration in number of minutes or days or hours.", parse_mode="HTML")
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
        await message.reply(f"{DOT_ANCHOR} Enter the user ID to add to premium.", parse_mode="HTML")
        await state.set_state(AdminActions.waiting_for_user_id)
    else:
        await message.reply(
            f"{DOT_ANCHOR} ❌ Invalid format. Please enter the duration as '(number) minutes', '(number) hours', or '(number) days'.",
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
            await message.reply(f"{DOT_ANCHOR} ❌ No chat found with this user.", parse_mode="HTML")
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
            f"{DOT_ANCHOR} User <b>@{username}</b> added successfully to <b>premium</b>.\n"
            f"{DOT_ANCHOR} Added on: <b>{formatted_now}</b>\n"
            f"{DOT_ANCHOR} Subscription will expire on: <b>{formatted_expires_at}</b>",
            parse_mode="HTML",
        )

        try:
            await bot.send_message(
                user_id,
                f"{DOT_ANCHOR} <b>Congratulations</b> 🥳 <b>@{username}</b>, you are now a <b>premium</b> user!\n"
                f"{DOT_ANCHOR} Valid until: <b>{formatted_expires_at}</b>\n"
                f"{DOT_ANCHOR} 💡 <b>Remember,</b> you can always check your <b>status</b> using /sup",
                parse_mode="HTML",
                reply_to_message_id=None # We don't have a message to reply to here
            )
        except Exception:
            pass

        await state.clear()
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ Hmm... That doesn't look right. Please send a numeric user ID.", parse_mode="HTML")


# ===========================
# Credits Management
# ===========================

@admin_router.callback_query(F.data == "add_credits")
async def process_add_credits(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f"{DOT_ANCHOR} Enter the amount of credits to add:", parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_credits_amount)


@admin_router.message(AdminActions.waiting_for_credits_amount)
async def process_credits_amount(message: types.Message, state: FSMContext):
    amount_text = message.text.strip()
    if amount_text.isdigit():
        amount = int(amount_text)
        await state.update_data(credits_amount=amount)
        await message.reply(f"{DOT_ANCHOR} Enter the user ID to add credits to:", parse_mode="HTML")
        await state.set_state(AdminActions.waiting_for_credits_user_id)
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ Invalid amount. Please enter a numeric value.", parse_mode="HTML")


@admin_router.message(AdminActions.waiting_for_credits_user_id)
async def process_credits_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    bot = message.bot
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except Exception:
            await message.reply(f"{DOT_ANCHOR} ❌ No chat found with this user.", parse_mode="HTML")
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
            f"{DOT_ANCHOR} ✅ Added <b>{amount}</b> credits to user <b>@{username}</b> (ID: {user_id})",
            parse_mode="HTML",
        )

        try:
            await bot.send_message(
                user_id,
                f"{DOT_ANCHOR} 🎉 You have received <b>{amount}</b> credits!\n"
                f"{DOT_ANCHOR} Check your balance with /sup",
                parse_mode="HTML",
            )
        except Exception:
            pass

        await state.clear()
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ Please send a numeric user ID.", parse_mode="HTML")


@admin_router.callback_query(F.data == "set_unlimited")
async def process_set_unlimited(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f"{DOT_ANCHOR} Enter the user ID to set as unlimited:", parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_unlimited_user_id)


@admin_router.message(AdminActions.waiting_for_unlimited_user_id)
async def process_unlimited_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    bot = message.bot
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except Exception:
            await message.reply(f"{DOT_ANCHOR} ❌ No chat found with this user.", parse_mode="HTML")
            return

        data = await load_premium_data()

        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["unlimited"] = True
                break

        if not user_found:
            new_user = {
                "user_id": user_id,
                "username": username,
                "credits": 0,
                "unlimited": True,
                "since": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "expires": "—",
                "last_chk": "—",
            }
            data.setdefault("premium_users", []).append(new_user)

        await save_premium_data(data)

        await message.reply(
            f"{DOT_ANCHOR} ✅ User <b>@{username}</b> is now <b>unlimited</b>.",
            parse_mode="HTML",
        )

        try:
            await bot.send_message(
                user_id,
                f"{DOT_ANCHOR} ♾️ You now have <b>unlimited</b> access!\n"
                f"{DOT_ANCHOR} Check your status with /sup",
                parse_mode="HTML",
            )
        except Exception:
            pass

        await state.clear()
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ Please send a numeric user ID.", parse_mode="HTML")


@admin_router.callback_query(F.data == "view_premium")
async def view_premium_users(call: CallbackQuery, state: FSMContext):
    data = await load_premium_data()
    users = data.get("premium_users", [])
    if not users:
        await call.message.edit_text(f"{DOT_ANCHOR} No premium users found.", parse_mode="HTML")
        return

    text = f"{DOT_ANCHOR} <b>Premium Users:</b>\n\n"
    for u in users:
        text += f"{DOT_ANCHOR} @{u.get('username', 'N/A')} (ID: {u.get('user_id')})\n"
    
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


@admin_router.callback_query(F.data == "remove_premium")
async def remove_premium_user(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f"{DOT_ANCHOR} Enter the user ID to remove from premium:", parse_mode="HTML")
    await call.answer()
    await state.set_state(AdminActions.waiting_for_user_id_remove)


@admin_router.message(AdminActions.waiting_for_user_id_remove)
async def process_remove_premium(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        data = await load_premium_data()
        users = data.get("premium_users", [])
        new_users = [u for u in users if str(u.get("user_id")) != user_id]
        
        if len(users) == len(new_users):
            await message.reply(f"{DOT_ANCHOR} ❌ User not found in premium list.", parse_mode="HTML")
        else:
            data["premium_users"] = new_users
            await save_premium_data(data)
            await message.reply(f"{DOT_ANCHOR} ✅ User removed from premium successfully.", parse_mode="HTML")
        
        await state.clear()
    else:
        await message.reply(f"{DOT_ANCHOR} ❌ Please send a numeric user ID.", parse_mode="HTML")
