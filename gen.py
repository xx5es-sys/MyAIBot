import config
import re
import random
import io
from datetime import datetime
from aiogram import types
from premium_util import is_premium
from branding import apply_branding

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

    if not await config.can_use_b3(message.chat.id, user_id):
        await message.reply(apply_branding("You do not have permission to use this command."), parse_mode="HTML")
        return

    pattern = r'^/gen (\d{4,12})(?: \|(\d{2})\|(\d{4})\|)? (\d+)$'
    match = re.match(pattern, message.text.strip())
    if not match:
        await message.reply(apply_branding("Invalid format. Use /gen bin [mes/ano] count."), parse_mode='HTML')
        return

    bin_number = match.group(1)
    requested_count = int(match.group(4))

    cards = []
    for _ in range(requested_count):
        month = int(match.group(2)) if match.group(2) else random.randint(1, 12)
        year = int(match.group(3)) if match.group(3) else datetime.now().year + random.randint(0, 5)
        card_number = generate_luhn_compliant_number(bin_number)
        cvv = random.randint(100, 999)
        cards.append(f"{card_number}|{str(month).zfill(2)}|{year}|{cvv}")

    random_card = random.choice(cards)
    card_number, month, year, cvv = random_card.split('|')
    extrap = f"{card_number[:-4]}xxxx"

    file_content = '\n'.join(cards).encode()
    filename = f"ccgen_{random.randint(1000, 9999)}.txt"
    
    # Use BufferedInputFile for aiogram 3.x
    from aiogram.types import BufferedInputFile
    input_file = BufferedInputFile(file_content, filename=filename)

    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    response_message = apply_branding(
        "𝗖𝗖 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗 ✅\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐀𝐥𝐠𝐨𝐫𝐢𝐭𝐡𝐦 : <code>𝐋𝐮𝐡𝐧</code>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐄𝐱𝐭𝐫𝐚𝐩 : <code>{extrap}</code>\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐀𝐦𝐨𝐮𝐧𝐭 : <code>{requested_count}</code>\n\n"
        f"<a href=\"http://t.me/IgnisXBot\">•</a> 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐁𝐲 ➺ {user_mention if message.from_user else '𝐔𝐧𝐤𝐧𝐨𝐰𝐧 𝐔𝐬𝐞𝐫'} {{<code><b>{user_status}</b></code>}}"
    )

    await message.reply_document(document=input_file, caption=response_message, parse_mode='HTML')
