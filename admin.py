from aiogram import Bot, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
import json
import re
from config import API_TOKEN, Admin
import os
from aiogram.utils.exceptions import ChatNotFound
import aiofiles
import premium_util

bot = Bot(token=API_TOKEN)

# ===========================
# Premium JSON File Handling
# ===========================

# نخلي مسار premium.json ثابت بجانب admin.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREMIUM_FILE_PATH = os.path.join(BASE_DIR, "premium.json")


async def ensure_premium_file():
    """
    Create premium.json if it doesn't exist or is empty/corrupted.
    """
    # إذا الملف ما موجود أصلاً
    if not os.path.exists(PREMIUM_FILE_PATH):
        default_data = {"premium_users": []}
        try:
            async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
                await file.write(json.dumps(default_data, indent=2, ensure_ascii=False))
        except PermissionError as e:
            print(f"PermissionError: Could not create 'premium.json'. Check file permissions. Error: {e}")
            raise PermissionError(
                "Permission denied for 'premium.json'. "
                "Please run as administrator or check folder permissions."
            ) from e
        return

    # إذا الملف موجود لكن فارغ أو خربان
    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "r", encoding="utf-8") as file:
            text = await file.read()
        if not text.strip():
            raise json.JSONDecodeError("Empty file", "", 0)
        json.loads(text)
    except (json.JSONDecodeError, FileNotFoundError):
        # نعيد تهيئة الملف بشكل صحيح
        default_data = {"premium_users": []}
        try:
            async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
                await file.write(json.dumps(default_data, indent=2, ensure_ascii=False))
        except PermissionError as e:
            print(f"PermissionError: Could not re-init 'premium.json'. Error: {e}")
            raise PermissionError(
                "Permission denied for 'premium.json'. "
                "Please run as administrator or check folder permissions."
            ) from e


async def load_premium_data():
    """Load premium data from file, ensuring file exists first."""
    await ensure_premium_file()
    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "r", encoding="utf-8") as file:
            text = await file.read()
            return json.loads(text)
    except Exception as e:
        print(f"Error loading premium.json: {e}")
        # If loading fails, return default structure to prevent crash
        return {"premium_users": []}


async def save_premium_data(data):
    """Save premium data to file."""
    try:
        async with aiofiles.open(PREMIUM_FILE_PATH, "w", encoding="utf-8") as file:
            await file.write(json.dumps(data, indent=2, ensure_ascii=False))
    except PermissionError as e:
        print(f"PermissionError: Could not save 'premium.json'. Check file permissions. Error: {e}")
        raise PermissionError(
            "Permission denied for 'premium.json'. "
            "Please run as administrator or check folder permissions."
        ) from e


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


async def admin_commands(message: types.Message, state: FSMContext):
    """Main admin menu."""
    if message.from_user.id == Admin:
        await AdminActions.authorized.set()
        keyboard = InlineKeyboardMarkup(row_width=1)
        add_button = InlineKeyboardButton("⏰ Add Time-Based Premium", callback_data="add_premium")
        add_credits_button = InlineKeyboardButton("💰 Add Credits", callback_data="add_credits")
        set_unlimited_button = InlineKeyboardButton("♾️ Set Unlimited", callback_data="set_unlimited")
        view_button = InlineKeyboardButton("👥 View Premium Users", callback_data="view_premium")
        remove_button = InlineKeyboardButton("❌ Remove Premium User", callback_data="remove_premium")
        keyboard.add(add_button, add_credits_button, set_unlimited_button, view_button, remove_button)
        await message.reply("Admin Menu:", reply_markup=keyboard)
    else:
        await message.reply("You are not authorized to access this command.")
        await state.reset_state()

# ===========================
# Time-Based Premium (Legacy)
# ===========================

async def process_add_premium(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Please send the subscription duration in number of minutes or days or hours.")
    await call.answer()
    await AdminActions.waiting_for_duration.set()


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
        await message.reply("Enter the user ID to add to premium.")
        await AdminActions.waiting_for_user_id.set()
    else:
        await message.reply(
            "Invalid format. Please enter the duration as "
            "'(number) minutes', '(number) hours', or '(number) days'."
        )


async def add_premium_user(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except ChatNotFound:
            await message.reply("No chat found with this user. Please ensure the user has started a chat with this bot.")
            return

        data_state = await state.get_data()
        total_seconds = data_state.get("duration")
        subscription_duration = timedelta(seconds=total_seconds)
        now = datetime.utcnow()
        expires_at = now + subscription_duration
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        formatted_expires_at = expires_at.strftime("%Y-%m-%d %H:%M:%S")

        data = await load_premium_data()

        # Check if user exists
        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                # Update expiry date
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
            f"User <b>@{username}</b> added successfully to <b>premium</b>.\n"
            f"Added on: <b>{formatted_now}</b>\n"
            f"Subscription will expire on: <b>{formatted_expires_at}</b>",
            parse_mode="HTML",
        )

        # Send confirmation to the user
        try:
            await bot.send_message(
                user_id,
                f"<b>Congratulations</b> 🥳 <b>@{username}</b>, you are now a <b>premium</b> user!\n"
                f"Valid until: <b>{formatted_expires_at}</b>\n"
                f"💡 <b>Remember,</b> you can always check your <b>status</b> using /sup",
                parse_mode="HTML",
            )
        except Exception:
            pass

        await state.reset_state()
    else:
        await message.reply("Hmm... That doesn't look right. 🧐 Please send a numeric user ID.")

# ===========================
# Credits Management
# ===========================

async def process_add_credits(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Enter the amount of credits to add:")
    await call.answer()
    await AdminActions.waiting_for_credits_amount.set()


async def process_credits_amount(message: types.Message, state: FSMContext):
    amount_text = message.text.strip()
    if amount_text.isdigit():
        amount = int(amount_text)
        await state.update_data(credits_amount=amount)
        await message.reply("Enter the user ID to add credits to:")
        await AdminActions.waiting_for_credits_user_id.set()
    else:
        await message.reply("Invalid amount. Please enter a numeric value.")


async def process_credits_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except ChatNotFound:
            await message.reply("No chat found with this user. Please ensure the user has started a chat with this bot.")
            return

        data_state = await state.get_data()
        amount = data_state.get("credits_amount", 0)

        data = await load_premium_data()

        # Check if user exists
        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["credits"] = user_rec.get("credits", 0) + amount
                break

        if not user_found:
            # Create new user with credits
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
            f"✅ Added <b>{amount}</b> credits to user <b>@{username}</b> (ID: {user_id})",
            parse_mode="HTML",
        )

        # Notify user
        try:
            await bot.send_message(
                user_id,
                f"🎉 You have received <b>{amount}</b> credits!\n"
                f"Check your balance with /sup",
                parse_mode="HTML",
            )
        except Exception:
            pass

        await state.reset_state()
    else:
        await message.reply("Invalid user ID. Please send a numeric user ID.")

# ===========================
# Unlimited Management
# ===========================

async def process_set_unlimited(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Enter the user ID to set as Unlimited (or send 'remove USER_ID' to remove unlimited):"
    )
    await call.answer()
    await AdminActions.waiting_for_unlimited_user_id.set()


async def process_unlimited_user_id(message: types.Message, state: FSMContext):
    text = message.text.strip()

    # Check if removing unlimited
    if text.lower().startswith("remove "):
        user_id = text[7:].strip()
        flag = False
        action = "removed from"
    else:
        user_id = text
        flag = True
        action = "set as"

    if user_id.isdigit():
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "No username"
        except ChatNotFound:
            await message.reply("No chat found with this user. Please ensure the user has started a chat with this bot.")
            return

        data = await load_premium_data()

        # Check if user exists
        user_found = False
        for user_rec in data.get("premium_users", []):
            if str(user_rec.get("user_id")) == user_id:
                user_found = True
                user_rec["unlimited"] = flag
                if flag:
                    # When setting unlimited, set credits to 0
                    user_rec["credits"] = 0
                break

        if not user_found and flag:
            # Create new user with unlimited
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

        status_text = "Unlimited ♾️" if flag else "Limited"
        await message.reply(
            f"✅ User <b>@{username}</b> (ID: {user_id}) has been {action} <b>{status_text}</b>",
            parse_mode="HTML",
        )

        # Notify user
        try:
            if flag:
                await bot.send_message(
                    user_id,
                    "🎉 Congratulations! You now have <b>Unlimited</b> access!\n"
                    "Check your status with /sup",
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    user_id,
                    "Your unlimited access has been removed.\n"
                    "Check your status with /sup",
                    parse_mode="HTML",
                )
        except Exception:
            pass

        await state.reset_state()
    else:
        await message.reply("Invalid user ID. Please send a numeric user ID.")

# ===========================
# Remove Premium
# ===========================

async def remove_premium_user(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Please send the user ID to remove from premium.")
    await call.answer()
    await AdminActions.waiting_for_user_id_remove.set()


async def process_remove_premium(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    user_details = None

    data = await load_premium_data()
    premium_users = data.get("premium_users", [])
    filtered_users = []
    for user in premium_users:
        if str(user.get("user_id")) != user_id:
            filtered_users.append(user)
        else:
            user_details = user
    data["premium_users"] = filtered_users
    await save_premium_data(data)

    if user_details:
        username_display = f"@{user_details.get('username', 'No username')}"
        await message.reply(f"User {username_display} (ID: {user_id}) has been removed from premium.")
    else:
        try:
            user = await bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user_id
        except Exception:
            username = user_id
        await message.reply(f"User {username} does not have a premium.")

    await state.reset_state()

# ===========================
# View Premium Users
# ===========================

async def view_premium_users(call: CallbackQuery, state: FSMContext):
    await call.answer()
    now = datetime.utcnow()

    data = await load_premium_data()

    if data.get("premium_users"):
        message_text = "<b>Premium Users:</b>\n\n"
        for user in data["premium_users"]:
            user_id = user.get("user_id", "—")
            username = user.get("username", "No Username")
            credits = user.get("credits", 0)
            unlimited = user.get("unlimited", False)
            since = user.get("since", "—")
            expires = user.get("expires", "—")
            last_chk = user.get("last_chk", "—")

            # Determine status
            if unlimited:
                status = "♾️ UNLIMITED"
                credits_display = "∞"
            elif credits > 0:
                status = "💰 CREDIT PREMIUM"
                credits_display = str(credits)
            else:
                status = "⏰ TIME-BASED"
                credits_display = "0"

            # Calculate remaining time for time-based
            time_info = ""
            if expires and expires != "—":
                try:
                    expires_time = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
                    remaining_time = expires_time - now
                    if remaining_time.total_seconds() > 0:
                        days, remainder = divmod(remaining_time.total_seconds(), 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes = remainder // 60
                        if days > 0:
                            time_info = f"⏳ {int(days)}d {int(hours)}h left"
                        elif hours > 0:
                            time_info = f"⏳ {int(hours)}h {int(minutes)}m left"
                        else:
                            time_info = f"⏳ {int(minutes)}m left"
                    else:
                        time_info = "⏰ Expired"
                except Exception:
                    pass

            message_text += (
                "━━━━━━━━━━━━━━━━\n"
                f"<b>Status:</b> {status}\n"
                f"<b>ID:</b> <code>{user_id}</code>\n"
                f"<b>User:</b> @{username}\n"
                f"<b>Credits:</b> {credits_display}\n"
                f"<b>Since:</b> {since}\n"
                f"<b>Expires:</b> {expires}\n"
                f"<b>Last Check:</b> {last_chk}\n"
            )
            if time_info:
                message_text += f"{time_info}\n"
            message_text += "\n"
    else:
        message_text = "<b>No premium users found.</b>"

    await call.message.edit_text(message_text, parse_mode="HTML")
