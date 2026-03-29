"""
=================================================================
𝖨𝖦𝖭𝖨𝖲𝖷 — Broadcast System (aiogram 3.x)
=================================================================
"""

import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import Admin
from db import load_db

broadcast_router = Router()


# ===========================
# FSM States
# ===========================

class BroadcastState(StatesGroup):
    waiting_for_message = State()


# ===========================
# Broadcast Message Template
# ===========================

BROADCAST_TEMPLATE = (
    "𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 \n"
    "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
    "{message_body}\n"
    "\n"
    "┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
    "\n"
    "• DeveBy ↝ 𝖨𝖦𝖭𝖨𝖲𝖷"
)


def build_broadcast_text(message_body: str) -> str:
    """Build the final broadcast message from admin content."""
    return BROADCAST_TEMPLATE.format(message_body=message_body)


# ===========================
# /broadcast Command
# ===========================

@broadcast_router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != Admin:
        await message.reply("❌ You are not authorized to use this command.")
        return
    await message.reply("📢 Send the message you want to broadcast to all users:")
    await state.set_state(BroadcastState.waiting_for_message)


# ===========================
# Receive & Send Broadcast
# ===========================

@broadcast_router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    if message.from_user.id != Admin:
        await state.clear()
        return

    bot = message.bot

    # --- Build the broadcast text from admin's message ---
    message_body = message.text or message.caption or ""
    final_text = build_broadcast_text(message_body)

    # --- Gather all user IDs from database.json ---
    db = load_db()
    user_ids = [u["id"] for u in db.get("users", []) if "id" in u]

    if not user_ids:
        await message.reply("⚠️ No users found in the database.")
        await state.clear()
        return

    success_count = 0
    fail_count = 0

    # --- Handle photo broadcast ---
    photo = None
    if message.photo:
        photo = message.photo[-1].file_id

    for uid in user_ids:
        try:
            if photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=photo,
                    caption=final_text,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=uid,
                    text=final_text,
                    parse_mode="HTML",
                )
            success_count += 1
        except Exception:
            fail_count += 1
        await asyncio.sleep(0.05)  # small delay to respect rate limits

    # --- Summary for admin ---
    summary = (
        "📊 <b>Broadcast Summary</b>\n\n"
        f"• Total Users: <b>{len(user_ids)}</b>\n"
        f"• Success: <b>{success_count}</b>\n"
        f"• Failed: <b>{fail_count}</b>"
    )
    await message.reply(summary, parse_mode="HTML")
    await state.clear()
