from aiogram import types, Bot, Dispatcher
import aiohttp
from config import auth_chats, API_TOKEN, can_use_b3

# ========= Config =========
DOT_ANCHOR = '<a href="http://t.me/IgnisXBot">•</a>'

async def proxycheck(message: types.Message):
    proxy_status = "Dead ❌"
    proxy_encrypted = "Error in Proxy"
    chat_id = message.chat.id
    user_id = message.from_user.id
    message_id_to_edit = None
    
    bot = message.bot

    try:
        if chat_id in auth_chats.get('private', []) or chat_id in auth_chats.get('group', []):
            if not await can_use_b3(chat_id, user_id):
                await message.reply(f"{DOT_ANCHOR} Please wait 30 seconds before using /chk again.", parse_mode="HTML")
                return
            await bot.send_chat_action(chat_id, "typing")
            response_message = await message.reply(f"{DOT_ANCHOR} wait a moment...", parse_mode="HTML")
            message_id_to_edit = response_message.message_id
    except:
        pass

    proxy_url = "http://p.webshare.io:80/"
    proxy_auth = aiohttp.BasicAuth('jelxyqtc-rotate', 'vxigi2vt6v8x')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://httpbin.org/ip", proxy=proxy_url, proxy_auth=proxy_auth) as response:
                if response.status == 200:
                    json_response = await response.json()
                    proxy = json_response["origin"]
                    proxy_status = "Live ✅"
                    proxy_encrypted = proxy[:-6] + "******"
                else:
                    proxy_encrypted = "Error in Proxy"
        except Exception as e:
            print(f"Error: {e}")
            proxy_encrypted = "Error in Proxy"
            
    if message_id_to_edit:
        await final(message_id_to_edit, chat_id, bot, proxy_status, proxy_encrypted)
    
async def final(message_id_to_edit, chat_id, bot, proxy_status, proxy_encrypted):
    reply_message = (
        f"{DOT_ANCHOR} <code>{proxy_encrypted}</code> {proxy_status}"
    )
    await bot.edit_message_text(text=reply_message, chat_id=chat_id, message_id=message_id_to_edit, parse_mode="HTML")  
