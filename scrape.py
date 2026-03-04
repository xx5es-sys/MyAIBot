from telethon import TelegramClient, sync
import asyncio
import re
import io
from aiogram import Bot, types
from aiogram.types import BufferedInputFile
from config import API_TOKEN

bot = Bot(token="8317431246:AAFfUUDoocr273qTY0v4r8i-giy7fNmAoug")
api_id   = '1234567'
api_hash = '2dc4807c0abe5b2a1bd0b77c35b68c38'
session_name = 'scrape_session'
# client = TelegramClient(session_name, api_id, api_hash)

async def handle_scrape_command(message: types.Message):
    client = TelegramClient(session_name, api_id, api_hash)
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not client.is_connected():
        await client.start()

    command_parts = message.text.split()
    if len(command_parts) < 3:
        await message.reply("Please use the command in the format: /scr <channel_name> <number_of_messages>")
        return

    channel_name = command_parts[1]
    try:
        num_messages = int(command_parts[2])
    except ValueError:
        await message.reply("Please enter a valid number for cards.")
        return

    process_message = await message.reply("𝐉𝐮𝐬𝐭 𝐚 𝐦𝐨𝐦𝐞𝐧𝐭...")

    try:
        channel = await client.get_entity(channel_name)
        messages = await client.get_messages(channel, limit=num_messages)
    except Exception as e:
        await process_message.edit_text(f"𝐢𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐜𝐡𝐚𝐧𝐧𝐞𝐥 𝐮𝐬𝐞𝐫𝐧𝐚𝐦𝐞")
        return

    all_cards = []
    cards_set = set()
    card_pattern = re.compile(r'(\d{16})\|(\d{2})\|(\d{4})\|(\d{3})')
    for msg in messages:
        if msg.text:
            found_cards = card_pattern.findall(msg.text)
            for card in found_cards:
                if len(card[0]) == 16 and 1 <= int(card[1]) <= 12 and len(card[2]) == 4 and len(card[3]) == 3:
                    all_cards.append('|'.join(card))
                    cards_set.add('|'.join(card))

    duplicates_removed = len(all_cards) - len(cards_set)

    if cards_set:
        with io.BytesIO() as file:
            file.write("\n".join(cards_set).encode('utf-8'))
            file.seek(0)
            
            await process_message.delete()
            
            filename = f"{len(cards_set)}x{channel_name}.txt"
            channel_link = f"https://t.me/{channel.username}" if channel.username else f"https://t.me/{channel_name}"
            final_message = f"<b>CC Scrapped Successful ✅</b>\n━━━━━━━━━━━━━━━━\n<b>Source:</b> <a href='{channel_link}'>{channel_name}</a>\n<b>Amount:</b> <code>{len(cards_set)}</code>\n<b>Duplicates Removed:</b> <code>{duplicates_removed}</code>\n━━━━━━━━━━━━━━━━\n<b>CC Scrapper By:</b> <a href='https://t.me/thba7cccbot'>𝐓𝐡𝐁𝐚𝟕 𝐜𝐡𝐞𝐜𝐤𝐞𝐫</a>"
            await bot.send_document(chat_id, BufferedInputFile(file.getvalue().encode(), filename=filename), reply_to_message_id=message.message_id, caption=final_message, parse_mode='HTML')
    else:
        await process_message.edit_text("No valid cards found.")






