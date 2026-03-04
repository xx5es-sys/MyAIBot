import config
import re
import random
import io
from datetime import datetime
from aiogram import types
from aiogram.types import BufferedInputFile
from message_handler import is_premium

# ========= Config =========
DOT_ANCHOR = '<a href="http://t.me/IgnisXBot">•</a>'

def calculate_luhn_checksum(digits):
    sum_digits = sum(int(d) if (i % 2 == 0) else int(d)*2 if int(d)*2 < 10 else int(d)*2 - 9
                     for i, d in enumerate(digits[::-1]))
    return (10 - (sum_digits % 10)) % 10

def generate_luhn_compliant_number(base):
    num_digits = 16
    num_to_generate = num_digits - len(base) - 1
    random_digits = [random.randint(0, 9) for _ in range(num_to_generate)]
    partial_number = [int(x) for x in base] + random_digits
    checksum = calculate_luhn_checksum(partial_number)
    return ''.join(str(x) for x in partial_number + [checksum])

async def generate_card(message: types.Message):
    user_id = message.from_user.id
    premium_status = await is_premium(str(user_id))

    if user_id == config.Admin:
        user_status = "Owner"
    elif premium_status:
        user_status = "Premium"
    else:
        user_status = "Free"

    # Note: can_use_b3 logic is kept as per original project
    if not await config.can_use_b3(message.chat.id, user_id):
        await message.reply(f"{DOT_ANCHOR} You do not have permission to use this command.", parse_mode='HTML')
        return

    # /gen bin [mes/ano] count
    text = message.text.strip()
    parts = text.split()
    
    if len(parts) < 2:
        await message.reply(f"{DOT_ANCHOR} Invalid format. Use <code>/gen bin</code> or <code>/gen bin count</code>", parse_mode='HTML')
        return

    bin_number = parts[1]
    requested_count = 10
    if len(parts) >= 3:
        try:
            requested_count = int(parts[2])
            if requested_count > 1000: requested_count = 1000
        except:
            pass

    cards = []
    for _ in range(requested_count):
        month = random.randint(1, 12)
        year = datetime.now().year + random.randint(0, 5)
        card_number = generate_luhn_compliant_number(bin_number)
        cvv = random.randint(100, 999)
        cards.append(f"{card_number}|{str(month).zfill(2)}|{year}|{cvv}")

    extrap = f"{bin_number}xxxx"

    file_content = '\n'.join(cards).encode()
    filename = f"ccgen_{random.randint(1000, 9999)}.txt"
    document = BufferedInputFile(file_content, filename=filename)

    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    response_message = (
        f"{DOT_ANCHOR} 𝗖𝗖 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗 ✅\n"
        f"{DOT_ANCHOR} ┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"{DOT_ANCHOR} ⊗ 𝐀𝐥𝐠𝐨𝐫𝐢𝐭𝐡𝐦 : <code>𝐋𝐮𝐡𝐧</code>\n"
        f"{DOT_ANCHOR} ⊗ 𝐄𝐱𝐭𝐫𝐚𝐩 : <code>{extrap}</code>\n"
        f"{DOT_ANCHOR} ⊗ 𝐀𝐦𝐨𝐮𝐧𝐭 : <code>{requested_count}</code>\n"
        "\n"
        f"{DOT_ANCHOR} ⊗ 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐁𝐲 ➺ {user_mention} [<code><b>{user_status}</b></code>]\n"
        f"{DOT_ANCHOR} ⊗ 𝐁𝐨ت ➺ 𝖨𝖦𝖭𝖨𝖲𝖷"
    )

    await message.reply_document(document=document, caption=response_message, parse_mode='HTML')
